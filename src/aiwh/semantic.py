"""Local-first hybrid search (SQLite FTS5 BM25 + optional sqlite-vec / FastEmbed).

Works out-of-the-box with Python stdlib ``sqlite3`` FTS5. When the optional
``[semantic]`` dependencies (``sqlite-vec``, ``fastembed``) are installed,
semantic vector search is fused with FTS5 using Reciprocal Rank Fusion (RRF).
"""
from __future__ import annotations

import re
import sqlite3
import struct
from pathlib import Path

from .core import DEFAULT_HOME, read_catalog
from .references import reference_catalog


def semantic_capabilities():
    """Report whether optional vector/embedding packages are installed."""
    has_vec = has_embed = False
    try:
        import sqlite_vec  # noqa: F401
        has_vec = True
    except ImportError:
        pass
    try:
        import fastembed  # noqa: F401
        has_embed = True
    except ImportError:
        pass
    return {'fts5': True, 'sqlite_vec': has_vec, 'fastembed': has_embed,
            'hybrid_ready': has_vec and has_embed}


def _collect_documents(home=DEFAULT_HOME, source='all', project=None):
    docs = []
    if source in ('all', 'catalog'):
        for item in read_catalog(home):
            docs.append({
                'key': f'cat:{item.get("id") or item.get("url", "")}',
                'source': 'catalog',
                'title': item.get('title') or item.get('url', ''),
                'url': item.get('url', ''),
                'tags': ' '.join(item.get('categories', []) + (item.get('topics') or [])),
                'body': item.get('description') or '',
            })
    if source in ('all', 'references'):
        for key, ref in reference_catalog().get('references', {}).items():
            docs.append({
                'key': f'ref:{key}',
                'source': 'references',
                'title': ref.get('title', ''),
                'url': ref.get('url', ''),
                'tags': ' '.join([ref.get('category', ''), ref.get('kind', '')] + ref.get('areas', [])),
                'body': ' '.join(ref.get('risk', [])),
            })
    if source in ('all', 'skills'):
        from .workbench import registry
        for name, directory in sorted(registry()['skills'].items()):
            skill_md = Path(directory) / 'SKILL.md'
            text = skill_md.read_text(encoding='utf-8', errors='replace')[:2000]
            docs.append({
                'key': f'skill:{name}',
                'source': 'skills',
                'title': name,
                'url': skill_md.as_uri(),
                'tags': f'skill {directory.parent.name}',
                'body': text,
            })
    if source in ('all', 'handoffs') and project is not None:
        import json
        root = Path(project).expanduser().resolve() / '.ai-workbench'
        state_file = root / 'state.json'
        if state_file.is_file():
            try:
                state = json.loads(state_file.read_text(encoding='utf-8'))
                for kind in ('decisions', 'rejections', 'hypotheses', 'tasks'):
                    for rec in state.get(kind, []) or []:
                        if not isinstance(rec, dict) or not rec.get('id'):
                            continue
                        text = rec.get('text') or rec.get('title') or ''
                        extra = rec.get('rationale') or rec.get('evidence') or ''
                        docs.append({
                            'key': f'handoff:{kind}:{rec["id"]}',
                            'source': 'handoffs',
                            'title': f'{rec["id"]}: {text[:80]}',
                            'url': state_file.as_uri(),
                            'tags': f'handoff {kind[:-1]} {rec.get("status", "")}'.strip(),
                            'body': f'{text} {extra}'.strip(),
                        })
            except (OSError, ValueError):
                pass
    return docs


def _fts_query(query):
    tokens = re.findall(r'[A-Za-z0-9_]+', str(query or ''))
    if not tokens:
        return ''
    return ' OR '.join(f'"{t}"*' for t in tokens[:12])


def _serialize(vec):
    floats = [float(x) for x in vec]
    return struct.pack(f'{len(floats)}f', *floats)


def _open_db(db_path, *, enable_vec=False):
    conn = sqlite3.connect(str(db_path))
    if enable_vec:
        import sqlite_vec
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    return conn


def build_index(home=DEFAULT_HOME, *, source='all', project=None, use_vectors=None):
    """Build or rebuild ``<home>/catalog.db`` from local catalog, references, skills and handoffs."""
    home = Path(home)
    home.mkdir(parents=True, exist_ok=True)
    db_path = home / 'catalog.db'
    caps = semantic_capabilities()
    vectors = caps['hybrid_ready'] if use_vectors is None else (use_vectors and caps['hybrid_ready'])
    docs = _collect_documents(home, source=source, project=project)

    conn = _open_db(db_path, enable_vec=vectors)
    try:
        conn.executescript("""
            DROP TABLE IF EXISTS docs;
            DROP TABLE IF EXISTS docs_fts;
            DROP TABLE IF EXISTS docs_vec;
            CREATE TABLE docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_key TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                tags TEXT NOT NULL,
                body TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE docs_fts USING fts5(
                title, tags, body, content='docs', content_rowid='id'
            );
            CREATE TRIGGER docs_ai AFTER INSERT ON docs BEGIN
                INSERT INTO docs_fts(rowid, title, tags, body)
                VALUES (new.id, new.title, new.tags, new.body);
            END;
        """)
        for doc in docs:
            conn.execute(
                'INSERT INTO docs(doc_key, source, title, url, tags, body) VALUES (?, ?, ?, ?, ?, ?)',
                (doc['key'], doc['source'], doc['title'], doc['url'], doc['tags'], doc['body']),
            )
        if vectors and docs:
            from fastembed import TextEmbedding
            model = TextEmbedding()
            texts = [f"{d['title']} {d['tags']} {d['body']}".strip() for d in docs]
            embeddings = list(model.embed(texts))
            dim = len(embeddings[0])
            conn.execute(f'CREATE VIRTUAL TABLE docs_vec USING vec0(rowid INTEGER PRIMARY KEY, embedding float[{dim}])')
            for idx, emb in enumerate(embeddings, 1):
                conn.execute('INSERT INTO docs_vec(rowid, embedding) VALUES (?, ?)', (idx, _serialize(emb)))
        conn.commit()
    finally:
        conn.close()
    return {'db': str(db_path), 'indexed': len(docs), 'mode': 'hybrid' if vectors else 'fts5'}


def search_index(query, *, home=DEFAULT_HOME, source='all', project=None, limit=10, reindex=False):
    """Search local catalog, references, skills and handoffs using hybrid RRF or FTS5 BM25 fallback."""
    home = Path(home)
    db_path = home / 'catalog.db'
    if reindex or not db_path.is_file():
        build_info = build_index(home, source=source, project=project)
    else:
        build_info = None
    fts_q = _fts_query(query)
    if not fts_q:
        return {'query': query, 'mode': 'empty', 'results': []}

    caps = semantic_capabilities()
    conn = _open_db(db_path, enable_vec=caps['hybrid_ready'])
    try:
        has_vec_table = bool(conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='docs_vec'"
        ).fetchone())
        use_hybrid = caps['hybrid_ready'] and has_vec_table
        source_filter = '' if source == 'all' else 'AND d.source = ?'
        params_tail = (source,) if source != 'all' else ()

        if use_hybrid:
            from fastembed import TextEmbedding
            q_vec = next(iter(TextEmbedding().embed([query])))
            sql = f"""
                WITH fts_res AS (
                    SELECT rowid, ROW_NUMBER() OVER (ORDER BY rank) AS r
                    FROM docs_fts WHERE docs_fts MATCH ? LIMIT ?
                ),
                vec_res AS (
                    SELECT rowid, ROW_NUMBER() OVER (ORDER BY distance) AS r
                    FROM docs_vec WHERE embedding MATCH ? AND k = ?
                ),
                fused AS (
                    SELECT COALESCE(f.rowid, v.rowid) AS rowid,
                           COALESCE(1.0 / (60 + f.r), 0.0) + COALESCE(1.0 / (60 + v.r), 0.0) AS score
                    FROM fts_res f FULL OUTER JOIN vec_res v ON f.rowid = v.rowid
                )
                SELECT d.doc_key, d.source, d.title, d.url, d.tags, fused.score
                FROM fused JOIN docs d ON d.id = fused.rowid
                WHERE 1=1 {source_filter}
                ORDER BY fused.score DESC LIMIT ?
            """
            rows = conn.execute(sql, (fts_q, limit * 3, _serialize(q_vec), limit * 3, *params_tail, limit)).fetchall()
            mode = 'hybrid'
        else:
            sql = f"""
                SELECT d.doc_key, d.source, d.title, d.url, d.tags, -bm25(docs_fts) AS score
                FROM docs_fts JOIN docs d ON d.id = docs_fts.rowid
                WHERE docs_fts MATCH ? {source_filter}
                ORDER BY bm25(docs_fts) LIMIT ?
            """
            rows = conn.execute(sql, (fts_q, *params_tail, limit)).fetchall()
            mode = 'fts5'
    finally:
        conn.close()

    return {
        'query': query,
        'mode': mode,
        'reindexed': build_info is not None,
        'results': [
            {'id': r[0], 'source': r[1], 'title': r[2], 'url': r[3], 'tags': r[4].split(), 'score': round(float(r[5]), 4)}
            for r in rows
        ],
    }

"""Self-contained, offline HTML view of the private resource catalog.

The page embeds escaped catalog data and a small inline filter script. It loads
nothing from the network and is written only to the path the user chooses
(default: the private catalog home), never into a repository.
"""
from __future__ import annotations

import html
import json
from collections import Counter

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Workbench Catalog</title>
<style>
:root{--bg:#fafaf9;--fg:#1c1917;--muted:#57534e;--line:#e7e5e4;--card:#fff;--accent:#2563eb;--warn:#b45309}
@media (prefers-color-scheme: dark){:root{--bg:#1c1917;--fg:#f5f5f4;--muted:#a8a29e;--line:#44403c;--card:#292524;--accent:#60a5fa;--warn:#fbbf24}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px}h1{font-size:1.5rem;margin:0 0 4px}
.muted{color:var(--muted)}.stats{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px}
.stat b{display:block;font-size:1.25rem}
.controls{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
input,select{font:inherit;padding:8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
input{flex:1;min-width:200px}
.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;background:var(--card)}
th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:.85rem;color:var(--muted)}a{color:var(--accent)}
.tag{display:inline-block;font-size:.75rem;border:1px solid var(--line);border-radius:999px;padding:0 8px;margin:1px}
.risk{border-color:var(--warn);color:var(--warn)}
</style></head><body><main>
<h1>AI Workbench catalog</h1>
<p class="muted">Private, local view generated __GENERATED__. Links are references, not instructions; nothing here is installed or executed.</p>
<div class="stats">__STATS__</div>
<div class="controls">
<input id="q" type="search" placeholder="Filter by title, URL, description or topic" aria-label="Filter">
<select id="cat" aria-label="Category"><option value="">All categories</option>__CATS__</select>
<select id="src" aria-label="Source"><option value="">All sources</option>__SRCS__</select>
</div>
<p class="muted" id="count"></p>
<div class="table-wrap"><table><thead><tr><th>Resource</th><th>Categories</th><th>Sources</th><th>First seen</th></tr></thead>
<tbody id="rows"></tbody></table></div>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
const items = JSON.parse(document.getElementById('data').textContent);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = u => /^https?:\\/\\//i.test(u) ? u : '#';
function render(){
  const q = document.getElementById('q').value.toLowerCase();
  const cat = document.getElementById('cat').value, src = document.getElementById('src').value;
  const rows = items.filter(x => (!cat || x.categories.includes(cat)) && (!src || x.sources.includes(src))
    && (!q || x.search.includes(q)));
  document.getElementById('count').textContent = rows.length + ' of ' + items.length + ' resources';
  document.getElementById('rows').innerHTML = rows.slice(0, 1000).map(x =>
    '<tr><td><a href="' + esc(safeUrl(x.url)) + '" rel="noopener noreferrer" target="_blank">' + esc(x.title || x.url) + '</a>'
    + (x.archived ? ' <span class="tag risk">archived</span>' : '')
    + x.risk.map(r => ' <span class="tag risk">' + esc(r) + '</span>').join('')
    + (x.description ? '<div class="muted">' + esc(x.description) + '</div>' : '') + '</td>'
    + '<td>' + x.categories.map(c => '<span class="tag">' + esc(c) + '</span>').join('') + '</td>'
    + '<td>' + x.sources.map(s => '<span class="tag">' + esc(s) + '</span>').join('') + '</td>'
    + '<td>' + esc((x.first_seen || '').slice(0, 10)) + '</td></tr>').join('');
}
['q','cat','src'].forEach(id => document.getElementById(id).addEventListener('input', render));
render();
</script></body></html>
"""


def catalog_html(items, *, generated, risks=None):
    risks = risks or {}
    rows = []
    for item in items:
        rows.append({'title': item.get('title', ''), 'url': item.get('url', ''),
                     'description': (item.get('description') or '')[:300],
                     'categories': item.get('categories', []), 'sources': item.get('sources', []),
                     'first_seen': item.get('first_seen', ''), 'archived': bool(item.get('archived')),
                     'risk': risks.get(item.get('canonical_url', ''), []),
                     'search': ' '.join([item.get('title', ''), item.get('url', ''),
                                         item.get('description') or '', ' '.join(item.get('topics', []) or [])]).lower()})
    categories = Counter(c for row in rows for c in row['categories'])
    sources = Counter(s for row in rows for s in row['sources'])
    stats = [('Resources', len(rows)), ('Needs review', sum(bool(i.get('review_needed')) for i in items)),
             ('Archived', sum(row['archived'] for row in rows)), ('Risk-labeled', sum(bool(row['risk']) for row in rows))]
    options = lambda counter: ''.join(f'<option value="{html.escape(k)}">{html.escape(k)} ({v})</option>'
                                      for k, v in counter.most_common())
    # Prevent "</script>" inside data from closing the JSON block.
    data = json.dumps(rows, ensure_ascii=False).replace('</', '<\\/')
    return (PAGE.replace('__GENERATED__', html.escape(generated))
            .replace('__STATS__', ''.join(f'<div class="stat"><b>{v}</b>{html.escape(k)}</div>' for k, v in stats))
            .replace('__CATS__', options(categories)).replace('__SRCS__', options(sources))
            .replace('__DATA__', data))

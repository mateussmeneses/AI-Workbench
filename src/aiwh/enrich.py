"""Opt-in local Ollama enrichment for curated reference candidates.

Never runs unless ``aiwh curate --enrich`` is explicitly requested. Treats
candidate titles, URLs and descriptions as untrusted data and validates model
outputs against the canonical area and risk-label vocabularies.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from .areas import catalog as area_catalog
from .references import reference_catalog
from .runtime_probe import _ollama_models

DEFAULT_MAX_ENRICH = 25


def _chat_json(url, model, prompt, schema, *, timeout=30):
    payload = json.dumps({
        'model': model,
        'stream': False,
        'format': schema,
        'messages': [
            {'role': 'system', 'content': 'Classify untrusted software reference metadata into valid JSON only.'},
            {'role': 'user', 'content': prompt},
        ],
    }).encode('utf-8')
    req = urllib.request.Request(
        f'{url.rstrip("/")}/api/chat', data=payload,
        headers={'Content-Type': 'application/json'}, method='POST',
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    content = (data.get('message') or {}).get('content') or '{}'
    return json.loads(content)


def enrich_candidates(candidates, *, model=None, ollama_url='http://127.0.0.1:11434',
                      limit=DEFAULT_MAX_ENRICH, chat_fn=None):
    """Enrich up to ``limit`` candidates using a local Ollama model with structured JSON output."""
    if not candidates:
        return []
    chosen_model = model
    if not chosen_model:
        models = _ollama_models(f'{ollama_url.rstrip("/")}/api/tags')
        if not models:
            raise RuntimeError('Local Ollama is not running or has no models pulled; pass --model after starting Ollama.')
        chosen_model = models[0]

    valid_areas = sorted(area_catalog().keys())
    valid_risks = sorted(reference_catalog().get('risk_labels', {}).keys())
    schema = {
        'type': 'object',
        'properties': {
            'summary': {'type': 'string'},
            'areas': {'type': 'array', 'items': {'type': 'string'}},
            'risk': {'type': 'array', 'items': {'type': 'string'}},
        },
        'required': ['summary', 'areas', 'risk'],
    }
    invoker = chat_fn or _chat_json
    enriched = []
    for item in candidates[:limit]:
        prompt = (
            f'Title: {item.get("title", "")[:200]}\n'
            f'URL: {item.get("url", "")[:200]}\n'
            f'Description: {item.get("description", "")[:400]}\n'
            f'Allowed areas: {", ".join(valid_areas)}\n'
            f'Allowed risk labels: {", ".join(valid_risks)}\n'
            'Return a concise 1-sentence technical summary, up to 3 allowed areas, and any applicable risk labels.'
        )
        try:
            raw = invoker(ollama_url, chosen_model, prompt, schema)
            areas = [a for a in (raw.get('areas') or []) if a in valid_areas][:3]
            risk = [r for r in (raw.get('risk') or []) if r in valid_risks]
            summary = ' '.join(str(raw.get('summary') or '').split())[:240]
            enrichment = {'model': chosen_model, 'summary': summary, 'areas': areas, 'risk': risk}
        except (OSError, ValueError, urllib.error.URLError) as exc:
            enrichment = {'model': chosen_model, 'error': str(exc)[:160]}
        enriched.append({**item, 'enrichment': enrichment})
    return enriched + list(candidates[limit:])

"""CLI for importing knowledge, preparing new repos, and continuing existing work."""
import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

from .core import (DEFAULT_HOME, attach, browser_html_export, catalog_metadata,
                   chromelike_bookmarks, detect_browser_files, github_from_gh, github_stars,
                   json_read, merged_index, new_since, now, project_profile, read_catalog,
                   save_catalog)
from .workbench import (AGENTS, bootstrap, inspect_project, registry, resume,
                        global_integration, remove_managed)
from .areas import catalog as area_catalog, recommend, markdown_plan, validate_catalog
from .game_porting import assess_game_port, game_port_markdown, save_game_plan, validate_game_catalog, game_catalog


def get_parser():
    p = argparse.ArgumentParser(prog='aiwh', description='AI Workbench: project bootstrap and continuity')
    p.add_argument('--home', type=Path, default=DEFAULT_HOME,
                   help='private local catalog directory; default ~/.ai-workbench-hub')
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('sync', help='optional read-only bookmark/GitHub stars catalog import')
    s.add_argument('--browser-auto', action='store_true')
    s.add_argument('--browser-json', type=Path, action='append', default=[])
    s.add_argument('--html', type=Path, action='append', default=[])
    s.add_argument('--stars-json', type=Path, action='append', default=[])
    s.add_argument('--github', action='store_true')
    s.add_argument('--dry-run', action='store_true')
    s.add_argument('--show-new', action='store_true', help='list resources not seen in earlier syncs')
    cu = sub.add_parser('curate', help='read-only: list new reference candidates not yet in the repository')
    cu.add_argument('--github', action='store_true', help='read starred repositories through gh')
    cu.add_argument('--stars-json', type=Path, action='append', default=[])
    cu.add_argument('--html', type=Path, action='append', default=[], help='bookmark export to scan')
    cu.add_argument('--browser-json', type=Path, action='append', default=[])
    cu.add_argument('--baseline-html', type=Path, action='append', default=[],
                    help='older bookmark export; links already in it are skipped')
    cu.add_argument('--json', action='store_true')
    cu.add_argument('--output', type=Path, help='write the Markdown/JSON report to this file')
    rf = sub.add_parser('references', help='list curated public references with risk labels')
    rf.add_argument('--area', action='append', default=[])
    rf.add_argument('--risk', help='only references carrying this risk label')
    rf.add_argument('--json', action='store_true')
    rf.add_argument('--markdown', action='store_true', help='print the generated docs/REFERENCES.md')
    ca = sub.add_parser('catalog', help='curated reference catalog maintenance')
    ca_sub = ca.add_subparsers(dest='catalog_action', required=True)
    cc = ca_sub.add_parser('check', help='opt-in network: check GitHub references for archived/stale/missing repos via gh')
    cc.add_argument('--stale-days', type=int, default=365)
    cc.add_argument('--json', action='store_true')
    sk = sub.add_parser('skills', help='skill quality lint and provenance-tracked local imports')
    sk_sub = sk.add_subparsers(dest='skills_action', required=True)
    sl = sk_sub.add_parser('lint', help='report vague, oversized and boilerplate skills (warnings)')
    sl.add_argument('--json', action='store_true')
    sl.add_argument('--strict', action='store_true', help='exit 1 when findings exist')
    si = sk_sub.add_parser('import', help='copy validated local skills into a project (untrusted text, never executed)')
    si.add_argument('source', type=Path)
    si.add_argument('--project', type=Path, default=Path.cwd())
    si.add_argument('--agent', choices=[*AGENTS, 'all'], default='claude')
    si.add_argument('--allow-scripts', action='store_true', help='also copy script files after manual review')
    si.add_argument('--dry-run', action='store_true')
    mc = sub.add_parser('mcp', help='MCP configuration previews')
    mc_sub = mc.add_subparsers(dest='mcp_action', required=True)
    mp = mc_sub.add_parser('plan', help='preview agent MCP config; --apply writes only a project .mcp.json for Claude')
    mp.add_argument('path', nargs='?', type=Path, default=Path.cwd())
    mp.add_argument('--agent', choices=['claude', 'codex', 'hermes', 'generic'], default='claude')
    mp.add_argument('--mcp', action='append', default=[])
    mp.add_argument('--area', action='append', default=[])
    mp.add_argument('--windows', dest='windows', action='store_true', default=None, help='wrap npx with cmd /c')
    mp.add_argument('--no-windows', dest='windows', action='store_false')
    mp.add_argument('--apply', action='store_true')
    mp.add_argument('--json', action='store_true')
    ho = sub.add_parser('handoff', help='export the continuity handoff')
    ho_sub = ho.add_subparsers(dest='handoff_action', required=True)
    he = ho_sub.add_parser('export', help='export to json, markdown, claude-memory or wiki (read-only for the project)')
    he.add_argument('path', nargs='?', type=Path, default=Path.cwd())
    he.add_argument('--format', choices=['json', 'markdown', 'claude-memory', 'wiki'], default='markdown')
    he.add_argument('--output', type=Path, help='directory to write files; omitted prints to stdout')
    ins = sub.add_parser('inspect', help='identify an analysis target and route it to a method, tools and skills')
    ins.add_argument('target', type=Path)
    ins.add_argument('--json', action='store_true')
    sp = sub.add_parser('spec', help='behavior-only specification checks')
    sp_sub = sp.add_subparsers(dest='spec_action', required=True)
    spc = sp_sub.add_parser('check', help='fail when a spec leaks addresses, decompiler names or assembly')
    spc.add_argument('path', type=Path)
    spc.add_argument('--json', action='store_true')
    cr = sub.add_parser('cleanroom', help='clean-room rebuild workspace')
    cr_sub = cr.add_subparsers(dest='cleanroom_action', required=True)
    cri = cr_sub.add_parser('init', help='create lab/ and clean/ rooms, native subagents, templates and devcontainer')
    cri.add_argument('path', type=Path)
    cri.add_argument('--rea-tools', type=Path, help='file with REA tool names (e.g. rea doctor --json output)')
    cri.add_argument('--dry-run', action='store_true')
    a = sub.add_parser('attach', help='attach private recommendations to an existing project')
    a.add_argument('--project', type=Path, default=Path.cwd())
    a.add_argument('--profile', action='append', default=[])
    a.add_argument('--limit', type=int, default=25)
    a.add_argument('--dry-run', action='store_true')
    b = sub.add_parser('init', help='bootstrap capabilities into a new or existing project')
    b.add_argument('path', nargs='?', type=Path, default=Path.cwd())
    b.add_argument('--create', action='store_true', help='create project folder if absent')
    b.add_argument('--agent', choices=[*AGENTS, 'all'], default='codex')
    b.add_argument('--profile', action='append', default=[], help='explicit profile override; repeatable')
    b.add_argument('--area', action='append', default=[], help='composable area, e.g. frontend + sales')
    b.add_argument('--goal', default='', help='plain-language project mission for area suggestions')
    b.add_argument('--auto-areas', action='store_true', help='opt in to top matching project areas')
    b.add_argument('--dry-run', action='store_true')
    managed = sub.add_parser('managed', help='manage files recorded by aiwh init')
    managed_sub = managed.add_subparsers(dest='managed_action', required=True)
    managed_remove = managed_sub.add_parser('remove', help='remove only manifest-verified managed files')
    managed_remove.add_argument('path', nargs='?', type=Path, default=Path.cwd())
    managed_remove.add_argument('--dry-run', action='store_true')
    re = sub.add_parser('resume', help='generate an evidence-based next-session report')
    re.add_argument('path', nargs='?', type=Path, default=Path.cwd())
    re.add_argument('--agent', choices=[*AGENTS, 'all'], default='codex')
    re.add_argument('--dry-run', action='store_true')
    au = sub.add_parser('audit', help='read-only project status in JSON')
    au.add_argument('path', nargs='?', type=Path, default=Path.cwd())
    gi = sub.add_parser('global-integration', help='optional global agent instruction hook (opt-in)')
    gi.add_argument('--agent', choices=['codex','claude','antigravity'], required=True)
    gi.add_argument('--apply', action='store_true', help='write to your user profile (default previews)')
    gi.add_argument('--disable', action='store_true', help='remove only AI Workbench managed block')
    sub.add_parser('profiles', help='list supported profiles')
    sub.add_parser('areas', help='list cross-domain, composable capability areas')
    rec = sub.add_parser('recommend', help='read-only, explainable skill/MCP/plugin plan for project')
    rec.add_argument('path', nargs='?', type=Path, default=Path.cwd())
    rec.add_argument('--goal', default='', help='describe the intended project')
    rec.add_argument('--area', action='append', default=[], help='explicitly select one or more areas')
    rec.add_argument('--json', action='store_true', help='machine-readable plan')
    gp = sub.add_parser('game-port', help='read-only console/binary and porting workflow triage')
    gp.add_argument('path', nargs='?', type=Path, default=Path.cwd())
    gp.add_argument('--binary', type=Path, help='inspect first 4 KiB of a game executable/ROM/disc')
    gp.add_argument('--platform', choices=sorted(game_catalog()['platforms']), help='explicit platform declaration')
    gp.add_argument('--track', choices=['auto','matching-decomp','static-recomp','compatibility-runtime','triage'], default='auto')
    gp.add_argument('--goal', default='', help='desired result: matching source, native port or runtime fixes')
    gp.add_argument('--json', action='store_true', help='machine-readable recommendation')
    gp.add_argument('--save', action='store_true', help='write a private Workbench-owned agent handoff')
    sub.add_parser('capabilities', help='list available agents, skills and MCP catalog')
    rp = sub.add_parser('report', help='summarize private resource catalog')
    rp.add_argument('--since', help='list resources first seen at/after YYYY-MM-DD, or "last" for the last sync')
    rp.add_argument('--html', nargs='?', type=Path, const=True, default=None,
                    help='write an offline HTML view (default: <home>/catalog.html)')
    d = sub.add_parser('doctor', help='check runtime and registry')
    d.add_argument('--project', type=Path, default=Path.cwd())
    return p


def main(argv=None):
    args = get_parser().parse_args(argv)
    home = args.home.expanduser()
    if args.command == 'init':
        report = bootstrap(args.path, agent=args.agent, profiles=args.profile or None,
                           areas=args.area or None, goal=args.goal, auto_areas=args.auto_areas,
                           create=args.create, dry_run=args.dry_run, home=home)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    if args.command == 'managed' and args.managed_action == 'remove':
        result = remove_managed(args.path, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if args.command == 'resume':
        result = resume(args.path, agent=args.agent, dry_run=args.dry_run)
        print(result['markdown'])
        print('Preview only.' if args.dry_run else 'Saved local .ai-workbench/CONTEXT.md')
        return 0
    if args.command == 'audit':
        print(json.dumps(inspect_project(args.path), indent=2, ensure_ascii=False))
        return 0
    if args.command == 'global-integration':
        print(json.dumps(global_integration(args.agent, dry_run=not args.apply, disable=args.disable), indent=2))
        return 0
    if args.command == 'profiles':
        for name, entry in registry()['profiles'].items():
            print(f'{name:<20} {entry.get("description", "")}')
        return 0
    if args.command == 'areas':
        validate_catalog()
        for name, entry in area_catalog().items():
            print(f'{name:<24} {entry["label"]}')
        return 0
    if args.command == 'recommend':
        validate_catalog()
        result = recommend(args.path,goal=args.goal,selected=args.area)
        print(json.dumps(result,indent=2,ensure_ascii=False) if args.json else markdown_plan(result))
        return 0
    if args.command == 'game-port':
        validate_game_catalog()
        result = assess_game_port(args.path, binary=args.binary, platform=args.platform,
                                  track=args.track, goal=args.goal)
        if args.save:
            result['saved_to'] = str(save_game_plan(args.path, result))
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else game_port_markdown(result))
        return 0
    if args.command == 'capabilities':
        reg = registry()
        print(f"Skills: {len(reg['skills'])} | Agent roles: {len(reg['agents'])} | Profiles: {len(reg['profiles'])}")
        print('Skills:', ', '.join(sorted(reg['skills'])))
        print('Agents:', ', '.join(sorted(reg['agents'])))
        return 0
    if args.command == 'sync':
        incoming = []
        if args.browser_auto:
            sources = detect_browser_files()
            print(f'Browser profiles found: {len(sources)}')
            for browser, profile, path in sources:
                incoming += chromelike_bookmarks(path, browser, profile)
        for path in args.browser_json:
            incoming += chromelike_bookmarks(path, 'manual', path.parent.name)
        for path in args.html:
            incoming += browser_html_export(path)
        for path in args.stars_json:
            incoming += github_stars(json_read(path))
        if args.github:
            incoming += github_from_gh()
        if not (args.browser_auto or args.browser_json or args.html or args.stars_json or args.github):
            print('Specify a source: aiwh sync --browser-auto --github')
            return 2
        old = read_catalog(home)
        stamp = now()
        merged = merged_index(old, incoming, seen_at=stamp)
        old_ids = {str(x['id']) for x in old}
        fresh = [x for x in merged if str(x['id']) not in old_ids]
        print(f'Imported {len(incoming)} resources, {len(merged)} unique ({len(fresh)} new)')
        if args.show_new:
            for item in fresh:
                print(f'+ {item.get("title") or item["url"]} <{item["url"]}>')
        print('Preview only.' if args.dry_run else f'Private catalog saved: {save_catalog(merged, home, last_sync=stamp)}')
        return 0
    if args.command == 'inspect':
        from .artifact import inspect_artifact, inspect_markdown
        result = inspect_artifact(args.target)
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else inspect_markdown(result), end='' if not args.json else '\n')
        return 0
    if args.command == 'spec' and args.spec_action == 'check':
        from .cleanroom import spec_check
        result = spec_check(args.path)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            for leak in result['leaks']:
                print(f'{args.path}:{leak["line"]}: {leak["rule"]}: {leak["match"]}')
            for warning in result['warnings']:
                print('warning:', warning)
            print('OK: no analysis details found.' if result['ok'] else f'{len(result["leaks"])} leaks found.')
        return 0 if result['ok'] else 1
    if args.command == 'cleanroom' and args.cleanroom_action == 'init':
        from .cleanroom import cleanroom_init
        result = cleanroom_init(args.path, dry_run=args.dry_run, rea_tools=args.rea_tools)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if args.command == 'curate':
        from .references import curate, curate_markdown
        incoming = []
        for path in args.html:
            incoming += browser_html_export(path)
        for path in args.browser_json:
            incoming += chromelike_bookmarks(path, 'manual', path.parent.name)
        for path in args.stars_json:
            incoming += github_stars(json_read(path))
        if args.github:
            incoming += github_from_gh()
        if not incoming:
            print('Specify a source: aiwh curate --github --html bookmarks.html')
            return 2
        baseline = [x for path in args.baseline_html for x in browser_html_export(path)]
        candidates = curate(incoming, baseline=baseline)
        text = (json.dumps(candidates, indent=2, ensure_ascii=False) + '\n') if args.json else curate_markdown(candidates)
        if args.output:
            args.output.write_text(text, encoding='utf-8')
            print(f'{len(candidates)} candidates written to {args.output}')
        else:
            print(text, end='')
        return 0
    if args.command == 'references':
        from .references import references_for, references_markdown, risk_suffix, validate_references
        validate_references()
        if args.markdown:
            print(references_markdown(), end='')
            return 0
        rows = references_for(args.area or None, risk=args.risk)
        if args.json:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            for row in rows:
                print(f'{row["title"]:<40} {row["url"]}{risk_suffix(row.get("risk", []))}')
            print(f'{len(rows)} references')
        return 0
    if args.command == 'catalog' and args.catalog_action == 'check':
        from .references import check_references
        report = check_references(stale_days=args.stale_days)
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            for row in report:
                if row['status'] != 'ok':
                    extra = row.get('reason') or ('last push ' + str(row.get('pushed_at') or '')[:10])
                    print(f'{row["status"]:<12} {row["url"]} ({extra})')
            print('Summary:', dict(Counter(row['status'] for row in report)))
        return 0
    if args.command == 'skills' and args.skills_action == 'lint':
        from .skilltools import lint_skills
        result = lint_skills()
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            for finding in result['findings']:
                print(f'{finding["rule"]:<18} {finding["skill"]}: {finding["detail"]}')
            print(f'{len(result["findings"])} findings across {result["skills"]} skills')
        return 1 if args.strict and result['findings'] else 0
    if args.command == 'skills' and args.skills_action == 'import':
        from .skilltools import import_skills
        result = import_skills(args.source, args.project, agent=args.agent,
                               allow_scripts=args.allow_scripts, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if args.command == 'mcp' and args.mcp_action == 'plan':
        from .mcp_plan import mcp_plan
        result = mcp_plan(args.path, agent=args.agent, mcps=args.mcp or None, areas=args.area or None,
                          windows=args.windows, apply=args.apply)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f'Target: {result["target"]}')
            print(result['snippet'], end='')
            for item in result['manual_setup']:
                print(f'Manual setup: {item["mcp"]} ({item["url"]})')
            for note in result['notes']:
                print('Note:', note)
            print('Applied.' if result['applied'] else ('Not written: see notes.' if args.apply else 'Preview only; nothing was written.'))
        return 0
    if args.command == 'handoff' and args.handoff_action == 'export':
        from .handoff_export import export_handoff
        result = export_handoff(args.path, args.format, output=args.output)
        if args.output:
            print('\n'.join(result['written']) or 'Nothing new to write.')
        else:
            for name, content in result['files'].items():
                if len(result['files']) > 1:
                    print(f'===== {name}')
                print(content, end='')
        return 0
    if args.command == 'report':
        items = read_catalog(home)
        if args.html is not None:
            from .html_report import catalog_html
            from .references import risk_index
            target = home / 'catalog.html' if args.html is True else Path(args.html)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(catalog_html(items, generated=now(), risks=risk_index()), encoding='utf-8')
            print(f'HTML report written: {target}')
            return 0
        if args.since:
            since = catalog_metadata(home).get('last_sync', '') if args.since == 'last' else args.since
            if not since:
                print('No recorded sync yet; run aiwh sync first.')
                return 2
            fresh = new_since(items, since)
            for item in fresh:
                print(f'+ {item.get("title") or item["url"]} <{item["url"]}> ({", ".join(item.get("categories", []))})')
            print(f'{len(fresh)} resources first seen since {since}')
            return 0
        source_counts = Counter(k for x in items for k in x.get('sources', []))
        categories = Counter(k for x in items for k in x.get('categories', []))
        print(f'Catalog: {len(items)} unique resources | review: {sum(bool(x.get("review_needed")) for x in items)}')
        print('Sources:', dict(source_counts.most_common()))
        print('Categories:', dict(categories.most_common()))
        return 0
    if args.command == 'attach':
        if args.limit < 1:
            print('Limit must be >= 1')
            return 2
        result = attach(args.project, read_catalog(home), profiles=args.profile or None,
                        limit=args.limit, dry_run=args.dry_run)
        print(f'Profiles: {", ".join(result["plan"]["profiles"])}')
        print(f'Catalog references: {len(result["plan"]["resources"])}')
        print('Preview only' if args.dry_run else 'Attached to private .ai-workbench/ directory')
        if args.dry_run:
            print(result['markdown'])
        return 0
    if args.command == 'doctor':
        reg = registry()
        print('Area catalog:', validate_catalog())
        from .references import validate_references
        from .skilltools import lint_skills
        print('Reference catalog:', validate_references())
        print('Game-porting catalog:', validate_game_catalog())
        print('Skill lint findings:', len(lint_skills()['findings']), '(run aiwh skills lint)')
        print('Capabilities root:', reg['skills'][next(iter(reg['skills']))].parents[2])
        print('Skills:', len(reg['skills']), 'profiles:', len(reg['profiles']), 'agent roles:', len(reg['agents']))
        print('Catalog path:', home)
        for command in ('git','gh','codex','claude','hermes','rea','node','java'):
            print(f'{command}: {shutil.which(command) or "not detected"}')
        import os
        for variable in ('GHIDRA_INSTALL_DIR', 'JAVA_HOME'):
            print(f'{variable}: {os.environ.get(variable) or "not set"}')
        print('Detected profiles:', ', '.join(project_profile(args.project)))
        return 0
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

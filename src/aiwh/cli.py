"""CLI for importing knowledge, preparing new repos, and continuing existing work."""
import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

from .core import (DEFAULT_HOME, attach, browser_html_export, chromelike_bookmarks,
                   detect_browser_files, github_from_gh, github_stars, json_read,
                   merged_index, project_profile, read_catalog, save_catalog)
from .workbench import AGENTS, bootstrap, inspect_project, registry, resume, global_integration
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
    sub.add_parser('report', help='summarize private resource catalog')
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
        merged = merged_index(old, incoming)
        print(f'Imported {len(incoming)} resources, {len(merged)} unique ({len(merged)-len(old)} new)')
        print('Preview only.' if args.dry_run else f'Private catalog saved: {save_catalog(merged, home)}')
        return 0
    if args.command == 'report':
        items = read_catalog(home)
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
        print('Capabilities root:', reg['skills'][next(iter(reg['skills']))].parents[2])
        print('Skills:', len(reg['skills']), 'profiles:', len(reg['profiles']), 'agent roles:', len(reg['agents']))
        print('Catalog path:', home)
        for command in ('git','gh','codex','claude','hermes'):
            print(f'{command}: {shutil.which(command) or "not detected"}')
        print('Detected profiles:', ', '.join(project_profile(args.project)))
        return 0
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

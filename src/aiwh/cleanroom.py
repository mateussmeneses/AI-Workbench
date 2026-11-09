"""Clean-room rebuild support: spec leak detection and workspace scaffolding.

``spec_check`` finds analysis details (addresses, decompiler names, assembly)
that must not cross from the analysis room into the clean room.
``cleanroom_init`` writes the two-room layout, native Claude Code subagents,
templates and the clean-room devcontainer through the managed-file manifest,
so ``aiwh managed remove`` reverses it.
"""
from __future__ import annotations

import re
from pathlib import Path

from .workbench import ManagedFilePlan, registry

LEAK_RULES = {
    'address': re.compile(r'\b0x[0-9a-fA-F]{5,}\b'),
    'decompiler-name': re.compile(
        r'\b(?:sub|FUN|LAB|DAT|loc|unk|off|var|arg|byte|word|dword|qword|field|PTR|thunk)_[0-9a-fA-F]{2,}\b'),
    'decompiler-type': re.compile(r'\b(?:undefined[1248]?|in_stack_[0-9a-fA-F]+|extraout_\w+|unaff_\w+)\b'),
    'assembly': re.compile(
        r'^\s*(?:0x[0-9a-fA-F]+:?\s*)?(?:mov|movzx|movsx|lea|push|pop|call|jmp|je|jne|jz|jnz|ja|jb|jg|jl|'
        r'cmp|test|xor|and|or|shl|shr|sar|imul|idiv|ret|add|sub|inc|dec|ldr|str|bl|blr|stp|ldp|adrp)\s+'
        r'.*\b(?:r?[abcd]x|e[abcd]x|[re]?[sd]i|[re]?[sb]p|r(?:8|9|1[0-5])[dwb]?|xmm\d+|[abcd][lh]|[xw]\d{1,2}|sp|lr)\b',
        re.IGNORECASE),
    'file-offset': re.compile(r'\b(?:file\s+offset|RVA|VA)\s*[:=]?\s*0x[0-9a-fA-F]+', re.IGNORECASE),
}
REQUIRED_SECTIONS = ('test cases', 'open questions')

# Read-oriented REA tools granted to the analyst subagent (Claude Code adds the mcp__rea__ prefix).
DEFAULT_REA_TOOLS = (
    'binary_overview', 'open_binary', 'close_binary', 'binary_session', 'inspect_artifact', 'extract_artifact',
    'analyze_function', 'batch_decompile', 'procedure_pseudo_code', 'procedure_assembly', 'procedure_info',
    'procedure_callers', 'procedure_callees', 'procedure_references', 'read_function_instructions',
    'list_procedures', 'search_procedures', 'list_strings', 'search_strings', 'list_names', 'list_segments',
    'xrefs', 'find_xrefs_to_name', 'get_call_graph', 'trace_call_path', 'build_call_path', 'trace_feature',
    'trace_application_feature', 'inspect_address_context', 'inspect_binary_layout', 'read_bytes', 'search_bytes',
    'analyze_javascript_application', 'analyze_web_bundle', 'recover_javascript_sources',
    'trace_javascript_semantics', 'trace_web_module_imports', 'inspect_web_network_capture',
    'inspect_managed_artifact', 'inspect_managed_members', 'inspect_android_package', 'inspect_android_class',
    'inspect_android_method', 'search_android_classes', 'decode_android_resources', 'inspect_wasm_artifact',
    'inspect_go_binary', 'inspect_rust_binary', 'inspect_macho', 'inspect_plist', 'inspect_sqlite_database',
    'inspect_pcap_capture', 'extract_firmware', 'inspect_firmware_regions',
    'record_unknown', 'update_unknown', 'list_unknowns', 'export_evidence_bundle', 'get_evidence_bundle',
)


def spec_check(path):
    """Return leaks (blocking) and structural warnings for a behavior-only spec."""
    path = Path(path)
    text = path.read_text(encoding='utf-8', errors='replace')
    leaks = []
    for number, line in enumerate(text.splitlines(), 1):
        for rule, pattern in LEAK_RULES.items():
            match = pattern.search(line)
            if match:
                leaks.append({'line': number, 'rule': rule, 'match': match.group(0)[:60],
                              'text': line.strip()[:160]})
    headings = {h.strip().lower() for h in re.findall(r'^#+\s*(?:\d+\.\s*)?(.+)$', text, re.MULTILINE)}
    warnings = [f'missing section: {section}' for section in REQUIRED_SECTIONS
                if not any(section in heading for heading in headings)]
    return {'path': str(path), 'ok': not leaks, 'leaks': leaks, 'warnings': warnings}


def rea_tool_names(source=None):
    """Tool names for the analyst: from a file (doctor JSON or a list) or the bundled default."""
    if source is None:
        names = DEFAULT_REA_TOOLS
    else:
        text = Path(source).read_text(encoding='utf-8', errors='replace')
        names = re.findall(r'mcp__rea__([a-z0-9_]+)', text)
        if not names:
            names = re.findall(r'"name"\s*:\s*"([a-z][a-z0-9_]+)"', text)
        if not names:
            names = [line.strip() for line in text.splitlines() if re.fullmatch(r'[a-z][a-z0-9_]+', line.strip())]
        if not names:
            raise ValueError(f'No REA tool names found in {source}')
    return ['mcp__rea__' + name for name in dict.fromkeys(names)]


def cleanroom_init(target, *, dry_run=False, rea_tools=None):
    root = Path(target).expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise ValueError(f'Not a directory: {root}')
    skills = registry()['skills']
    source = skills['wb-clean-room-rebuild']
    oracle = skills['wb-oracle-testing']
    tools = ', '.join(rea_tool_names(rea_tools))
    plan = ManagedFilePlan(root, dry_run) if root.exists() else None
    if plan is None:
        if dry_run:
            return {'target': str(root), 'dry_run': True, 'would_create': True,
                    'files': sorted(_layout(source, oracle, tools))}
        root.mkdir(parents=True)
        plan = ManagedFilePlan(root, dry_run)
    for relative, content in _layout(source, oracle, tools).items():
        plan.write(root / relative, content)
    gitignore = root / '.gitignore'
    current = gitignore.read_text(encoding='utf-8') if gitignore.exists() else ''
    wanted = ['.ai-workbench/', 'lab/target/', 'lab/rebuild/', 'clean/src/build/']
    missing = [line for line in wanted if line not in current.splitlines()]
    if missing:
        plan.write(gitignore, current.rstrip() + ('\n\n' if current.strip() else '')
                   + '# AI Workbench clean room\n' + '\n'.join(missing) + '\n', allow_unowned_merge=True)
    managed = plan.finish()
    return {'target': str(root), 'dry_run': dry_run, 'managed_files': managed,
            'operations': [vars(op) for op in plan.operations],
            'next': ['Put the target in lab/target/', 'Build the clean container from clean/.devcontainer',
                     'Run ./run-team.ps1 -Target lab/target/<file> -Feature "<one feature>"']}


def _layout(source, oracle, tools):
    def read(path):
        return path.read_text(encoding='utf-8')
    files = {
        'lab/.claude/agents/analyst.md': read(source / 'agents/analyst.md').replace('{{REA_TOOLS}}', tools),
        'lab/.claude/agents/spec-writer.md': read(source / 'agents/spec-writer.md'),
        'lab/.claude/agents/verifier.md': read(source / 'agents/verifier.md'),
        'clean/.claude/agents/rebuilder.md': read(source / 'agents/rebuilder.md'),
        'lab/templates/planted-failures.md': read(oracle / 'templates/planted-failures.md'),
        'lab/NOTES.md': read(source / 'templates/NOTES.md'),
        'lab/target/.gitkeep': '', 'lab/analysis/.gitkeep': '', 'lab/handoff/.gitkeep': '',
        'clean/QUESTIONS.md': '# Open questions from the rebuild\n',
        'clean/ATTRIBUTION.md': '# Attribution\n\n| Asset | Source | License |\n|---|---|---|\n',
        'clean/src/.gitkeep': '',
        'run-team.ps1': read(source / 'templates/run-team.ps1'),
        'run-team.sh': read(source / 'templates/run-team.sh'),
        'CLEANROOM.md': ('# Clean room\n\nCreated by `aiwh cleanroom init`. Procedure: the `wb-clean-room-rebuild` skill.\n\n'
                         '- `lab/` analysis room: analyst, spec-writer, verifier (REA tools).\n'
                         '- `clean/` clean room: rebuilder only, opened in `clean/.devcontainer`.\n'
                         '- Only `handoff/SPEC.md` crosses to the clean room, after `aiwh spec check`.\n'
                         '- Remove everything Workbench wrote with `aiwh managed remove .`.\n'),
    }
    for name in ('TEARDOWN.md', 'SPEC.md', 'evidence.md'):
        files[f'lab/templates/{name}'] = read(source / 'templates' / name)
    for name in ('devcontainer.json', 'Dockerfile', 'init-firewall.sh'):
        files[f'clean/.devcontainer/{name}'] = read(source / 'devcontainer' / name)
    return files

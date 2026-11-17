---
name: wb-security-review
description: Use when auditing code, dependencies, auth flows, file I/O, or agent integrations for vulnerabilities, injection, and secret exposure.
---

# Security Review

## When to apply
- Reviewing PRs touching authentication, authorization, file paths, subprocesses, deserialization, or external inputs.
- Auditing third-party skills, MCP configs, or dependency trees for supply-chain risks.

## Procedure
1. Map trust boundaries, entry points, and attacker-controlled inputs (files, URLs, CLI args, headers, LLM/tool outputs).
2. Check for path traversal/symlink escapes, command injection (`shell=True`), unsafe deserialization (`yaml.load`, `pickle`), and SSRF/XSS.
3. Verify authn/authz enforcement on every sensitive action (fail-closed defaults, constant-time token comparison, least privilege).
4. Scan for hardcoded secrets, overly broad permissions, and sensitive data written to logs, errors, or git-tracked files.
5. Provide minimal proof-of-concept reproductions, severity rationale, and targeted regression tests for each confirmed finding.

## Verification
- Regression tests confirm rejected malicious inputs fail closed without side effects.
- Confirmed findings include exact file/line references and remediation verification.

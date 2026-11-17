---
name: wb-operations-process
description: Use when designing SOPs, incident runbooks, SLA/support workflows, or internal operational automations with human-in-the-loop checks.
---

# Operations Process

## When to apply
- Documenting recurring operational runbooks, support triage, or back-office automation scripts.
- Reducing manual toil while keeping approval gates on irreversible actions.

## Procedure
1. Map the current end-to-end process: triggers, inputs, manual handoffs, failure points, and time spent per step.
2. Identify high-frequency, deterministic steps safe to automate versus judgment calls requiring human approval.
3. Build idempotent scripts/runbooks with dry-run previews, audit logs, and clear escalation paths on failure.
4. Define measurable SLAs/SLOs and alert thresholds so silent failures are caught early.
5. Rehearse the runbook against a realistic failure scenario and update steps based on observed friction.

## Verification
- Runbook can be executed by a second operator without tribal knowledge.
- Automation supports `--dry-run` or preview mode before mutating live operational state.

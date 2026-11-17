---
name: wb-deployment-operations
description: Use when configuring CI/CD pipelines, Docker builds, release automation, health probes, or zero-downtime deployment rollbacks.
---

# Deployment Operations

## When to apply
- Editing GitHub Actions/CI workflows, Dockerfiles, systemd/service units, or release scripts.
- Investigating flaky pipelines, slow builds, or failed production rollouts.

## Procedure
1. Audit current build triggers, secrets scope, runner OS/versions, and artifact retention rules.
2. Pin base images, action SHAs/versions, and lockfiles so builds remain reproducible over time.
3. Structure pipelines into fast fail-early stages (lint/unit tests) before expensive packaging or deployment steps.
4. Include readiness/liveness checks, graceful shutdown handling, and a tested rollback procedure for every deployable unit.
5. Run local smoke verification on built artifacts before pushing workflow or release-script changes.

## Verification
- CI/release dry-runs or local packaging checks pass with zero leaked secrets.
- Rollback steps are documented and do not depend on manual memory during an outage.

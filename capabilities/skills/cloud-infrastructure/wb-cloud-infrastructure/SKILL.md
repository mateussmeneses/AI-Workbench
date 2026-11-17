---
name: wb-cloud-infrastructure
description: Use when authoring or reviewing Infrastructure-as-Code, IAM policies, networking, container orchestration, or cloud cost/security controls.
---

# Cloud Infrastructure

## When to apply
- Writing or modifying Terraform, Bicep, CloudFormation, Kubernetes manifests, or IAM roles.
- Diagnosing VPC/DNS routing, secret management, or unexpected cloud spend.

## Procedure
1. Inspect existing IaC state, environment boundaries (dev/staging/prod), and blast radius before proposing changes.
2. Enforce least-privilege IAM permissions, encrypted storage at rest/in transit, and private networking by default.
3. Parameterize environment-specific values (sizing, CIDR, retention) without duplicating entire module trees.
4. Run static validation (`terraform validate`/`plan`, `kubeval`, policy checks) and preview exact resource diffs before applying.
5. Tag every billable resource and document manual teardown or state-import steps when refactoring live infra.

## Verification
- Dry-run plan output reviewed with zero unintended destructive replacements.
- No plaintext credentials or wildcard `*` admin policies introduced.

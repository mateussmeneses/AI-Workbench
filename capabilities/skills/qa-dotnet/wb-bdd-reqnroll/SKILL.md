---
name: wb-bdd-reqnroll
description: Specify BDD scenarios with NUnit and Reqnroll in .NET projects
version: 1.1.0
---
# wb-bdd-reqnroll

**Suggested role:** `qa-strategist`. This file is portable and does not depend on that agent existing.

## When to use
BDD cases, .NET automation, step definitions and feature parameterization.

## Procedure
1. Locate `.feature` files, step definitions, pages, fixtures and existing conventions.
2. Write rule-oriented Given/When/Then, not click scripts; reuse existing steps.
3. Keep scenarios independent, data explicit and assertions on behavior (including toasts and permissions).
4. Run `dotnet test` with an appropriate filter; record environmental failures separately from functional ones.

## Output
New/changed scenarios, coverage gaps and commands/results.

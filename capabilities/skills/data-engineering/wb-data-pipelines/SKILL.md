---
name: wb-data-pipelines
description: Use when building or debugging ETL/ELT jobs, streaming/batch ingestion, schema evolution, partitioning, and data-quality assertions.
---

# Data Pipelines

## When to apply
- Creating new ingestion connectors, dbt/SQL transformations, or scheduled batch workflows.
- Fixing late-arriving data, duplicate rows, OOM transformations, or broken downstream tables.

## Procedure
1. Map source schemas, update cadence, volume growth, and downstream SLA consumers before writing transforms.
2. Make every stage idempotent and replayable by partition/watermark so backfills never duplicate records.
3. Separate raw landing, cleaned/typed staging, and business-mart layers with explicit schema contracts.
4. Add automated data-quality checks (row counts, non-null keys, freshness, referential integrity) that fail loudly before publishing.
5. Benchmark memory/disk footprint on a bounded sample before running full historical backfills.

## Verification
- Re-running the pipeline twice on the same input partition yields identical output counts and checksums.
- Lineage and PII/retention rules are documented for new datasets.

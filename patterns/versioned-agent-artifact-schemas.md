# Versioned Agent Artifact Schemas

Use this pattern when agent plans, tool results, approvals, traces, or eval fixtures survive longer than one process. Persisted JSON becomes an API: model prompts, workers, dashboards, and replay tools will otherwise interpret the same field differently as the product evolves.

## Problem

Agent artifacts often begin as convenient dictionaries. A worker adds `confidence`, another changes `actions` from strings to objects, and a replay job later reads old records with current assumptions. The JSON still parses, so the failure appears as incorrect behavior rather than an obvious compatibility error.

Version the artifact's meaning, not just its storage shape. Readers should either migrate a known old version into one canonical in-memory model or reject it with an actionable error. They should never guess which schema produced a record.

## Required fields

| Field | Purpose | Example |
| --- | --- | --- |
| `artifact_type` | Routes the record to the correct parser. | `agent.execution_plan` |
| `schema_version` | Identifies the documented field semantics. | `2` |
| `artifact_id` | Stable identity for logs, approvals, and retries. | `plan_01J...` |
| `created_at` | Supports retention and incident reconstruction. | ISO 8601 UTC timestamp |
| `producer` | Names the service and release that wrote the record. | `planner@4f8c2a1` |
| `payload` | Contains type-specific data, separate from the envelope. | `{"operations": [...]}` |

The envelope stays small. Prompt versions, model names, policy revisions, and input hashes belong in `payload` when they affect interpretation or reproducibility.

## Reader and writer contract

1. Define one canonical in-memory representation for the latest supported schema.
2. Validate the envelope before reading any payload fields.
3. Route by the exact `(artifact_type, schema_version)` pair.
4. Apply explicit, deterministic migrations one version at a time.
5. Validate again after migration; a migration is not permission to accept malformed data.
6. Run business logic only against the canonical representation.
7. Write only the current schema version; do not create new legacy records.
8. Preserve the original artifact or its content hash when migrated output is used for audit or replay.
9. Reject future and unknown versions without side effects.

```python
MIGRATIONS = {
    1: migrate_plan_v1_to_v2,
    2: migrate_plan_v2_to_v3,
}
CURRENT_VERSION = 3


def load_plan(raw):
    validate_envelope(raw)
    if raw["artifact_type"] != "agent.execution_plan":
        raise UnsupportedArtifactType(raw["artifact_type"])

    version = raw["schema_version"]
    if version > CURRENT_VERSION:
        raise UnsupportedSchemaVersion(version)

    migrated = raw
    while version < CURRENT_VERSION:
        migrate = MIGRATIONS.get(version)
        if migrate is None:
            raise MissingMigration(version, version + 1)
        migrated = migrate(migrated)
        version = migrated["schema_version"]

    validate_plan_v3(migrated)
    return PlanV3.from_dict(migrated)
```

## Evolution rules

| Change | Compatibility decision |
| --- | --- |
| Add optional metadata with a safe default | May remain in the same version if old readers ignore unknown fields. |
| Rename a field | New version plus an explicit migration. |
| Change units, enum meaning, default behavior, or null semantics | New version, even if the JSON type is unchanged. |
| Remove a field used by policy, replay, billing, or audit | New version and a documented retention decision. |
| Add a required field that cannot be derived | New version; old artifacts must be rejected or handled through a named degraded path. |
| Change only whitespace or serialization order | No schema bump; canonical hashing rules may still need an update. |

Avoid accepting both old and new field names throughout business logic. That distributes migration policy across the codebase and makes removal nearly impossible.

## Compatibility tests

Maintain sanitized fixtures for every supported version and run these checks without network access:

- each historical fixture migrates to the expected canonical object,
- migration is deterministic and does not mutate the source fixture,
- applying a migration twice fails clearly rather than corrupting the artifact,
- missing intermediate migrations fail with the exact unsupported version,
- future versions fail closed before tools or external APIs are called,
- semantically invalid values fail after migration even when their types are valid,
- current writer output round-trips through the current reader,
- artifact hashes use documented canonical fields and serialization.

A useful removal gate is production evidence that no retained artifact or active producer still requires the old reader. A calendar date alone is not evidence.

## Rollout sequence

1. Ship readers that understand both the current and next schema.
2. Verify old fixtures and shadow-read sampled stored artifacts.
3. Switch writers to the new version.
4. Monitor rejected versions and migration failures by `artifact_type` and producer.
5. Backfill only when it reduces operational risk; immutable audit records may be better left untouched.
6. Remove an old reader only after its retention window closes and active producers are confirmed upgraded.

For queued work, deploy compatible readers before writers. A new producer can otherwise enqueue artifacts that an older worker cannot safely consume during a rolling deployment.

## Acceptance criteria

Schema evolution is controlled when:

- every durable agent artifact has an explicit type and integer schema version,
- only the current schema enters business logic,
- semantic changes trigger version reviews rather than relying on JSON parse success,
- unknown future versions fail before side effects,
- supported historical versions have migration fixtures,
- rollout order prevents new writers from outrunning old readers,
- logs identify the artifact type, source version, target version, and producer without exposing sensitive payloads.

## Anti-patterns

- Treating a database migration number as the artifact schema version.
- Using model or prompt version as a substitute for a data contract.
- Defaulting a missing version to “latest.”
- Silently dropping unknown fields from signed or approval-bound artifacts.
- Parsing old and new shapes in every downstream function.
- Updating fixtures in place so historical compatibility is never exercised.
- Backfilling immutable audit artifacts without retaining source hashes or provenance.

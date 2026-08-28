# Ozone 12 tools

This directory contains **Ozone-specific** tooling migrated from `OZONE12_MASTERING_LAB`.

Current #100 scope is intentionally small: confirmed XML/schema/ElementChain validation and patching helpers. The old all-in-one mastering meter is not copied here as a permanent duplicate.

Follow-up #101 splits executable ownership:

```text
Ozone XML / ParamID / ElementChain / presets / REAPER bridge
    -> tools or src under mastering/ozone12

attack retention / mono loss / correlation / decoded codec peaks
    -> Genre_test backend-neutral technical/QC layer
```

The normal Genre_test analyzer must not require Ozone, REAPER or these tools.

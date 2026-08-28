# Ozone 12 runtime namespace

Reserved integration boundary for the optional Ozone 12 Advanced mastering backend.

Issue #100 establishes the repository and knowledge/config boundary without importing Ozone or REAPER into the ordinary Genre_test runtime. Issue #101 owns executable migration and will add Python modules here only after separating Ozone-specific code from backend-neutral TechnicalProfile/QC metrics.

Ordinary v0.4/v0.5 analysis and retrieval must continue to work when Ozone and REAPER are absent.

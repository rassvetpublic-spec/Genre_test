# Local AI Review v0.1.1

This tool runs a local, read-only cross-model consultation with configurable providers.

Default free topology:

```text
ContextPack
  ├─ Ollama / gpt-oss:20b -> Proposal A
  └─ Gemini / gemini-3.7-flash -> Proposal B
           -> independent cross-review
           -> primary-provider synthesis
           -> FINAL
```

It does not write repository files, publish GitHub reviews, create commits, or merge pull requests.

## Install optional remote-provider SDKs

```powershell
python -m pip install -e ".[ai-review]"
```

Ollama uses its local HTTP API and does not require a Python Ollama package.

## Default free configuration

The checked-in `config.yaml` selects:

```text
primary_provider  = ollama
primary_model     = gpt-oss:20b
secondary_provider = gemini
secondary_model    = gemini-3.7-flash
ollama_host         = http://127.0.0.1:11434
```

The local Ollama model must already be available in Ollama. This PR does not install Ollama or pull model weights.

Gemini still requires `GEMINI_API_KEY`. Keep secrets outside the repository; for Windows, a local PowerShell SecretStore can inject the key into the process environment before execution.

## Provider overrides

Provider roles are configuration values, not architectural constants:

```powershell
$env:AI_REVIEW_PRIMARY_PROVIDER = "ollama"
$env:AI_REVIEW_PRIMARY_MODEL = "gpt-oss:20b"
$env:AI_REVIEW_SECONDARY_PROVIDER = "gemini"
$env:AI_REVIEW_SECONDARY_MODEL = "gemini-3.7-flash"
$env:AI_REVIEW_OLLAMA_HOST = "http://127.0.0.1:11434"
```

Supported provider names are `ollama`, `openai`, and `gemini`.

To use the original paid OpenAI + Gemini topology:

```powershell
$env:AI_REVIEW_PRIMARY_PROVIDER = "openai"
$env:AI_REVIEW_PRIMARY_MODEL = "<OpenAI model id>"
$env:AI_REVIEW_SECONDARY_PROVIDER = "gemini"
$env:AI_REVIEW_SECONDARY_MODEL = "<Gemini model id>"
$env:OPENAI_API_KEY = "..."
$env:GEMINI_API_KEY = "..."
```

Only a selected provider is instantiated, so an Ollama + Gemini run does not require `OPENAI_API_KEY`.

## Run

```powershell
python -m tools.ai_review consult --task "Compare two implementation approaches."
```

A complete local transcript is written under `tools/ai_review/runs/` unless `--no-save` is used. The directory ignores generated run artifacts by default.

The result identifies the configured providers under:

```text
providers.primary
providers.secondary
```

and role-neutral results under:

```text
proposals.primary
proposals.secondary
reviews.primary_on_secondary
reviews.secondary_on_primary
```

## v0.1.1 boundary

- local `consult` only;
- configurable primary/secondary providers;
- local Ollama structured-output adapter;
- structured JSON contracts remain authoritative;
- same canonical ContextPack for both independent proposals and all later stages;
- no GitHub Actions;
- no repository write authority for either model;
- no autonomous merge;
- no iterative `review`/repair loop yet;
- no Ollama installation/model-download automation.

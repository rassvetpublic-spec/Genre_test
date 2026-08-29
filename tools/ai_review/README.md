# Local AI Review v0.1

This tool runs a local, read-only cross-model consultation:

```text
ContextPack
  ├─ OpenAI -> Proposal A
  └─ Gemini -> Proposal B
           -> cross-review
           -> OpenAI synthesis
           -> FINAL
```

It does not write repository files, publish GitHub reviews, create commits, or merge pull requests.

## Install optional SDKs

```powershell
python -m pip install -e ".[ai-review]"
```

## Configure

Set secrets only in the process environment:

```powershell
$env:OPENAI_API_KEY = "..."
$env:GEMINI_API_KEY = "..."
$env:OPENAI_MODEL = "<OpenAI model id>"
$env:GEMINI_MODEL = "<Gemini model id>"
```

`config.yaml` is JSON-compatible YAML so the loader needs no YAML dependency. Model identifiers
remain configuration values and are not architectural constants.

## Run

```powershell
python -m tools.ai_review consult --task "Compare two implementation approaches."
```

A complete local transcript is written under `tools/ai_review/runs/` unless `--no-save` is used.
The directory ignores generated run artifacts by default.

## v0.1 boundary

- local `consult` only;
- structured JSON contracts;
- same canonical ContextPack for both independent proposals;
- independent cross-review;
- no GitHub Actions;
- no repository write authority for either model;
- no autonomous merge;
- no iterative `review`/repair loop yet.

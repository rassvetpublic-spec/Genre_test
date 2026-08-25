# Runtime data — v0.4.0

Genre_test keeps generated runtime data outside Git while using the checkout as the default working-copy state root.

Default Windows checkout:

```text
C:\GIT\Genre_test
```

## Working-copy locations

```text
C:\GIT\Genre_test\results\
C:\GIT\Genre_test\.genre_test\history.sqlite3
C:\GIT\Genre_test\.genre_test\logs\genre_test.log
C:\GIT\Genre_test\.genre_test\huggingface\
```

`.genre_test/` and `results/` are gitignored.

The GUI exposes clickable History/log locations. Validation and build-comparison reports are stored under `results/validation`; large scripted regressions use `results/large_regression/<timestamp>/`.

## History

SQLite history is append-oriented and stores build-aware run metadata, detailed MAEST evidence and comparison/validation data.

Track identity is SHA-256 of file contents, so a track can move or be renamed without becoming a new logical track.

Historical JSON import remains available for migration/data recovery when old snapshots need to be associated with current track identities. Old release bootstraps are not retained in the active runtime.

## Unreadable audio

A file decode failure does not terminate a large GUI/Validation run. The file is skipped, logged and represented as an error in Validation output where applicable; processing continues with the next file.

## Hugging Face

Genre_test uses normal user authentication state and shared Hugging Face/pip download caches where available. Project runtime remains isolated by `.venv`.

Public pinned models do not require an HF token. A configured token may still be used normally.

## Packaged release

A portable source package creates its own `.venv` inside the extracted release folder on first launch. Python/PyTorch/model weights are not embedded in the ZIP.

Current package bootstrap:

```text
Genre_test_START.cmd
scripts\release_bootstrap.ps1
```

## Overrides

Advanced/debug use may override runtime paths with supported environment variables such as:

```text
GENRE_TEST_PROJECT_ROOT
GENRE_TEST_DATA_DIR
HF_HOME
```

Do not commit generated SQLite databases, model caches, audio corpora or regression output folders.

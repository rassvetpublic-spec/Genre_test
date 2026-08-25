# Safe Stop — v0.4.0

Genre_test uses cooperative cancellation for long GUI analysis jobs.

## GUI behavior

`Анализ` and `Validation` expose `ОСТАНОВИТЬ` while a cancellable job is running.

Safe Stop does not kill the Python worker thread and does not interrupt an active CUDA/PyTorch kernel mid-call. It sets a cancellation flag and exits at safe boundaries between model/decode stages.

A stop request can therefore take until the current inference unit finishes.

## Ordinary analysis

- completed tracks are already written to JSON/history;
- partial batch output remains usable;
- the currently incomplete track is not committed as a completed result;
- GUI state ends as stopped rather than error;
- unreadable files are logged/skipped and do not terminate a folder batch.

## Validation

- completed tracks/comparisons remain durable;
- a track is committed only after the requested analysis for that track completes;
- the incomplete current track is not committed;
- the session records stopped/cancelled state and remaining tracks;
- partial JSON/CSV reports are still generated;
- decode failures are reported and Validation continues.

If cancellation occurs during initial scanning/identity work, only already-completed safe identity/cache writes may remain.

## Проверка

Saved-build comparison and repeatability do not run MAEST/AST inference and are normally short. They are not treated as long cancellable analysis jobs.

## Runtime locations

Default working-copy log:

```text
C:\GIT\Genre_test\.genre_test\logs\genre_test.log
```

See `docs/RUNTIME_DATA.md` for history, reports and cache locations.

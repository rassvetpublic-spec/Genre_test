# Safe Stop — v0.3.1

Genre_test uses cooperative cancellation for long GUI analysis jobs.

## GUI behavior

Both `Анализ` and `Validation / Перепроверка` expose an `ОСТАНОВИТЬ` button while a cancellable job is running.

The button does not terminate the Python worker thread and does not interrupt a CUDA/PyTorch inference call in the middle. It sets a cancellation flag. The analyzer checks that flag before and after each MAEST inference window and at other safe boundaries.

Therefore a stop request may take until the current inference window finishes.

## Ordinary analysis

- completed tracks are already written to JSON and SQLite history;
- a partial batch also receives a partial `summary.csv`;
- the currently incomplete track is not written to history;
- the GUI ends in `Остановлено`, not `Ошибка`.

## Validation Lab

- completed tracks and comparisons remain durable;
- a track is committed only after all requested modes for that track complete;
- the incomplete current track is not committed;
- the validation session is finalized with `status=stopped` and `cancelled=true`;
- partial JSON/CSV validation reports are still generated;
- `remaining_tracks` records how many scanned tracks were left unprocessed.

If cancellation is requested during the pre-session scan/identity phase, no validation session is created and history remains unchanged apart from safe file-location/hash cache entries that may already have completed.

## Non-cancellable short operations

History JSON import and version-only comparison remain non-cancellable in v0.3.1 because they do not run MAEST inference and are normally short. The Stop button is disabled for those operations.

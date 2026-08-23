# Runtime data — v0.3.1

For the current development phase, Genre_test keeps runtime-generated project data inside the project checkout.

Default checkout on Windows:

```text
C:\GIT\Genre_test
```

## Default locations

```text
C:\GIT\Genre_test\results\
C:\GIT\Genre_test\.genre_test\history.sqlite3
C:\GIT\Genre_test\.genre_test\logs\genre_test.log
C:\GIT\Genre_test\.genre_test\huggingface\
```

`.genre_test/` and `results/` are gitignored and must not be committed.

The GUI displays the active History SQLite and log paths. Both Analysis and Validation output panes have a `СКОПИРОВАТЬ СОДЕРЖИМОЕ` button. The log can be opened directly from the GUI.

## Migration from v0.3.0

v0.3.0 stored the default history database outside the checkout, for example:

```text
%LOCALAPPDATA%\Genre_test\history.sqlite3
```

When v0.3.1 first resolves the new default history path and the repo-local database does not yet exist, it uses SQLite backup semantics to copy the legacy database into:

```text
C:\GIT\Genre_test\.genre_test\history.sqlite3
```

This preserves already imported legacy JSON history and existing analysis runs.

The old database is not deleted automatically. This avoids destructive migration. After the repo-local history has been verified, the old external copy may be removed manually.

## Unreadable audio in large validation runs

A single file that cannot be decoded by SoundFile/librosa no longer terminates the entire Validation session.

The failed file is:

- skipped;
- written to the persistent log with its traceback;
- listed in the Validation JSON/CSV report with `status=ERROR`;
- included in the final GUI summary under `File errors skipped`.

Validation then continues with the next track.

The same skip-and-continue policy is used by ordinary GUI folder batch analysis.

## Hugging Face model cache

If `HF_HOME` is not already defined by the environment, Genre_test sets it to:

```text
C:\GIT\Genre_test\.genre_test\huggingface
```

The first v0.3.1 model load can therefore download/cache MAEST again inside the checkout even if an older user-level Hugging Face cache already exists.

## Overrides

Advanced/debug use can override the checkout root or state directory with:

```text
GENRE_TEST_PROJECT_ROOT
GENRE_TEST_DATA_DIR
HF_HOME
```

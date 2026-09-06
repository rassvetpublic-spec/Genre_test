from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TEXT_EXTENSIONS = {
    ".py", ".json", ".yaml", ".yml", ".toml", ".md", ".txt",
    ".ini", ".cfg", ".csv", ".ps1", ".psm1", ".psd1", ".cmd", ".bat",
}
NO_BOM_EXTENSIONS = {
    ".py", ".json", ".yaml", ".yml", ".toml", ".md", ".txt",
    ".ini", ".cfg", ".csv",
}
UTF8_BOM = b"\xef\xbb\xbf"


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    names = result.stdout.decode("utf-8", errors="strict").split("\0")
    return [root / name for name in names if name]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures: list[str] = []
    checked = 0

    for path in tracked_files(root):
        if path.suffix.lower() not in TEXT_EXTENSIONS or not path.is_file():
            continue
        checked += 1
        raw = path.read_bytes()
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() in NO_BOM_EXTENSIONS and raw.startswith(UTF8_BOM):
            failures.append(f"{rel}: UTF-8 BOM is not allowed")
            continue
        try:
            text = raw.decode("utf-8-sig" if raw.startswith(UTF8_BOM) else "utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            failures.append(f"{rel}: invalid UTF-8 ({exc})")
            continue
        if "\ufffd" in text:
            failures.append(f"{rel}: contains Unicode replacement character U+FFFD")

    if failures:
        print("ENCODING_POLICY=FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"ENCODING_POLICY=PASS files={checked}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

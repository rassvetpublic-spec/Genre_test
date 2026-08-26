from __future__ import annotations

import json

from genre_test.retrieval import detect_retrieval_health


def main() -> int:
    health = detect_retrieval_health()
    print(
        json.dumps(
            {
                "backend": health.backend_name,
                "status": health.status,
                "value": health.value,
                "details": health.details,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if health.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

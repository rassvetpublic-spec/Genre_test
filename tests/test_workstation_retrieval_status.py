from __future__ import annotations

import http.client
import json
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

from genre_test import runtime_meta
from genre_test.workstation.retrieval_adapter import collect_retrieval_status
from genre_test.workstation.server import create_server
from genre_test.workstation.service import WorkstationService
from genre_test.workstation.settings import SettingsStore


def _disable_legacy_history(monkeypatch) -> None:
    monkeypatch.setattr(runtime_meta, "legacy_history_path", lambda: None)


def _create_minimal_history(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE tracks (
                track_id TEXT PRIMARY KEY,
                last_path TEXT
            );
            CREATE TABLE runs (
                track_id TEXT,
                result_json TEXT,
                analyzed_at TEXT
            );
            """
        )


def _get_json(host: str, port: int, path: str) -> tuple[int, dict[str, object]]:
    connection = http.client.HTTPConnection(host, port, timeout=3)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        assert isinstance(payload, dict)
        return response.status, payload
    finally:
        connection.close()


def test_workstation_import_does_not_eagerly_import_retrieval_or_heavy_ml() -> None:
    code = """
import sys
import genre_test.workstation.service
import genre_test.workstation.server
for name in (
    'torch',
    'transformers',
    'genre_test.retrieval.clamp3_sidecar_backend',
    'genre_test.retrieval.service',
    'genre_test.retrieval.storage',
):
    assert name not in sys.modules, name
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_missing_history_is_na_and_does_not_create_retrieval_store(
    tmp_path: Path, monkeypatch
) -> None:
    state = tmp_path / "state"
    monkeypatch.setenv("GENRE_TEST_DATA_DIR", str(state))
    _disable_legacy_history(monkeypatch)

    payload = collect_retrieval_status()

    assert payload["status"] == "N/A"
    assert payload["available"] is False
    assert payload["code"] == "history_source_missing"
    assert payload["index"] is None
    assert not (state / "retrieval.sqlite3").exists()
    assert isinstance(payload["backend_fingerprint"], str)
    assert len(str(payload["backend_fingerprint"])) == 64


def test_valid_history_without_store_is_not_misreported_as_empty_index(
    tmp_path: Path, monkeypatch
) -> None:
    state = tmp_path / "state"
    monkeypatch.setenv("GENRE_TEST_DATA_DIR", str(state))
    _disable_legacy_history(monkeypatch)
    _create_minimal_history(state / "history.sqlite3")

    payload = collect_retrieval_status()

    assert payload["status"] == "N/A"
    assert payload["available"] is False
    assert payload["code"] == "retrieval_store_missing"
    assert payload["index"] is None
    assert not (state / "retrieval.sqlite3").exists()


def test_invalid_history_fails_closed_before_store_creation(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "state"
    state.mkdir(parents=True)
    (state / "history.sqlite3").write_text("not sqlite", encoding="utf-8")
    monkeypatch.setenv("GENRE_TEST_DATA_DIR", str(state))
    _disable_legacy_history(monkeypatch)

    payload = collect_retrieval_status()

    assert payload["status"] == "N/A"
    assert payload["available"] is False
    assert str(payload["code"]).startswith("history_source_")
    assert not (state / "retrieval.sqlite3").exists()


def test_capability_contract_exposes_status_but_keeps_catalog_search_deferred() -> None:
    items = WorkstationService().capabilities()["items"]
    assert isinstance(items, list)
    states = {str(item["key"]): str(item["state"]) for item in items}
    assert states["retrieval_status"] == "available"
    assert states["catalog"] == "deferred"
    assert states["search"] == "deferred"


def test_retrieval_status_endpoint_returns_na_without_degrading_shell(
    tmp_path: Path, monkeypatch
) -> None:
    state = tmp_path / "state"
    monkeypatch.setenv("GENRE_TEST_DATA_DIR", str(state))
    _disable_legacy_history(monkeypatch)
    service = WorkstationService(
        settings_store=SettingsStore(tmp_path / "workstation-settings.json")
    )
    server = create_server("127.0.0.1", 0, service=service, quiet=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        status, retrieval = _get_json(str(host), int(port), "/api/v1/retrieval/status")
        assert status == 200
        assert retrieval["status"] == "N/A"
        assert retrieval["available"] is False
        assert retrieval["code"] == "history_source_missing"

        status, health = _get_json(str(host), int(port), "/api/v1/health")
        assert status == 200
        assert health["ok"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

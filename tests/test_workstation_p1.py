from __future__ import annotations

import http.client
import json
import subprocess
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from types import SimpleNamespace

import pytest

from genre_test.workstation.contracts import API_VERSION, NAVIGATION_IDS, ApiError
from genre_test.workstation.i18n import (
    SUPPORTED_LANGUAGES,
    catalog,
    normalize_language,
    translate,
    validate_catalog,
)
from genre_test.workstation.runtime_adapter import collect_runtime_hud
from genre_test.workstation.server import create_server, is_loopback_host
from genre_test.workstation.service import WorkstationService, validate_project_output
from genre_test.workstation.settings import SettingsStore


@contextmanager
def running_server(tmp_path: Path) -> Iterator[tuple[str, int]]:
    service = WorkstationService(
        settings_store=SettingsStore(tmp_path / "workstation-settings.json")
    )
    server = create_server("127.0.0.1", 0, service=service, quiet=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield str(host), int(port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(
    host: str,
    port: int,
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    connection = http.client.HTTPConnection(host, port, timeout=3)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {} if payload is None else {"Content-Type": "application/json"}
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def request_json(
    host: str,
    port: int,
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
) -> tuple[int, dict[str, object]]:
    status, _headers, body = request(host, port, method, path, payload)
    decoded = json.loads(body.decode("utf-8"))
    assert isinstance(decoded, dict)
    return status, decoded


def test_static_package_contains_p1_shell_assets() -> None:
    package = resources.files("genre_test.workstation.static")
    index = package.joinpath("index.html").read_text(encoding="utf-8")
    javascript = package.joinpath("app.js").read_text(encoding="utf-8")
    stylesheet = package.joinpath("app.css").read_text(encoding="utf-8")

    for navigation_id in NAVIGATION_IDS:
        assert f'data-view="{navigation_id}"' in index
    assert "/api/v1/runtime" in javascript
    assert "/api/v1/settings/language" in javascript
    assert "deferred-notice" in index
    assert ".app-shell" in stylesheet


def test_server_serves_shell_assets_and_security_headers(tmp_path: Path) -> None:
    with running_server(tmp_path) as (host, port):
        for path, content_type in (
            ("/", "text/html"),
            ("/assets/app.css", "text/css"),
            ("/assets/app.js", "text/javascript"),
        ):
            status, headers, body = request(host, port, "GET", path)
            assert status == 200
            assert headers["Content-Type"].startswith(content_type)
            assert headers["Cache-Control"] == "no-store"
            assert headers["X-Content-Type-Options"] == "nosniff"
            assert headers["X-Frame-Options"] == "DENY"
            assert headers["Content-Security-Policy"].startswith("default-src 'self'")
            assert body


def test_server_is_loopback_only() -> None:
    assert is_loopback_host("127.0.0.1") is True
    assert is_loopback_host("::1") is True
    assert is_loopback_host("localhost") is True
    assert is_loopback_host("0.0.0.0") is False

    with pytest.raises(ValueError, match="loopback"):
        create_server("0.0.0.0", 0, quiet=True)


def test_health_navigation_and_capabilities_are_bounded_p1(tmp_path: Path) -> None:
    with running_server(tmp_path) as (host, port):
        status, health = request_json(host, port, "GET", "/api/v1/health")
        assert status == 200
        assert health["api_version"] == API_VERSION
        assert health["localhost_only"] is True
        donor = health["donor"]
        assert isinstance(donor, dict)
        assert donor["direct_code_port"] is False
        assert donor["revision"] == "ff8344ae1a77bd7eb5be46b55c83813e923d3d2c"

        status, navigation = request_json(host, port, "GET", "/api/v1/navigation")
        assert status == 200
        items = navigation["items"]
        assert isinstance(items, list)
        assert [item["id"] for item in items] == list(NAVIGATION_IDS)
        phases = {item["id"]: item["phase"] for item in items}
        assert phases["project"] == "p1"
        assert phases["settings"] == "p1"
        assert phases["repair"] == "deferred"
        assert phases["master"] == "deferred"

        status, capabilities = request_json(host, port, "GET", "/api/v1/capabilities")
        assert status == 200
        states = {item["key"]: item["state"] for item in capabilities["items"]}
        assert states["workstation_shell"] == "available"
        assert states["runtime_hud"] == "available"
        assert states["repair"] == "deferred"
        assert states["stems"] == "deferred"
        assert states["mastering"] == "deferred"


def test_ru_en_catalog_is_complete_and_missing_key_is_explicit() -> None:
    validate_catalog()
    assert SUPPORTED_LANGUAGES == ("ru", "en")
    assert set(catalog("ru")) == set(catalog("en"))
    assert catalog("ru")["nav.settings"] == "Настройки"
    assert catalog("en")["nav.settings"] == "Settings"
    assert normalize_language("de") == "ru"
    assert translate("en", "missing.key") == "missing.key"
    assert translate("ru", "panel.runtime.backend") == "Бэкенд"


def test_language_setting_persists_and_invalid_write_fails(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    assert store.load().language == "ru"
    assert store.save_language("EN").language == "en"
    assert SettingsStore(store.path).load().language == "en"

    with pytest.raises(ValueError, match="unsupported"):
        store.save_language("de")


def test_language_api_persists_and_returns_structured_error(tmp_path: Path) -> None:
    with running_server(tmp_path) as (host, port):
        status, saved = request_json(
            host,
            port,
            "PUT",
            "/api/v1/settings/language",
            {"language": "en"},
        )
        assert status == 200
        assert saved == {"language": "en"}

        status, current = request_json(host, port, "GET", "/api/v1/settings")
        assert status == 200
        assert current == {"language": "en"}

        status, error = request_json(
            host,
            port,
            "PUT",
            "/api/v1/settings/language",
            {"language": "de"},
        )
        assert status == 400
        assert error["ok"] is False
        assert error["error"]["code"] == "invalid_language"


def test_api_error_contract_is_typed_and_stable() -> None:
    error = ApiError(code="example", message="Example failure", status=409)
    assert error.to_dict() == {
        "ok": False,
        "error": {"code": "example", "message": "Example failure"},
    }
    assert error.status == 409


def test_job_contract_has_heartbeat_progress_and_cancel(tmp_path: Path) -> None:
    with running_server(tmp_path) as (host, port):
        status, created = request_json(
            host,
            port,
            "POST",
            "/api/v1/jobs",
            {"kind": "acceptance_fixture"},
        )
        assert status == 201
        assert created["kind"] == "acceptance_fixture"
        assert created["state"] == "queued"
        assert created["progress"] == 0.0
        assert created["cancellable"] is True
        assert str(created["heartbeat_utc"]).endswith("Z")
        job_id = str(created["job_id"])

        status, cancelled = request_json(
            host,
            port,
            "POST",
            f"/api/v1/jobs/{job_id}/cancel",
        )
        assert status == 200
        assert cancelled["state"] == "cancelled"
        assert cancelled["cancellable"] is False
        assert str(cancelled["heartbeat_utc"]).endswith("Z")

        status, fetched = request_json(host, port, "GET", f"/api/v1/jobs/{job_id}")
        assert status == 200
        assert fetched == cancelled


def test_unknown_route_and_unknown_job_fail_structurally(tmp_path: Path) -> None:
    with running_server(tmp_path) as (host, port):
        status, missing_route = request_json(host, port, "GET", "/api/v1/nope")
        assert status == 404
        assert missing_route["error"]["code"] == "not_found"

        status, missing_job = request_json(host, port, "GET", "/api/v1/jobs/not-real")
        assert status == 404
        assert missing_job["error"]["code"] == "job_not_found"


def test_source_path_can_never_be_derived_output_target(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    source.write_bytes(b"fixture")

    with pytest.raises(ValueError, match="must not overwrite"):
        validate_project_output(source, source)

    output = tmp_path / "derived" / "candidate.wav"
    assert Path(validate_project_output(source, output)) == output.resolve(strict=False)


def test_runtime_hud_adapter_has_explicit_na_state_without_gpu() -> None:
    snapshot = SimpleNamespace(
        sampled_at=123.0,
        system_status="OK",
        gpu_status="nvidia-smi unavailable",
        cpu_percent=12.34,
        ram_used_bytes=512 * 1024 * 1024,
        ram_available_bytes=1024 * 1024 * 1024,
        ram_total_bytes=1536 * 1024 * 1024,
        ram_percent=33.3,
        process_rss_bytes=64 * 1024 * 1024,
        process_cpu_percent=1.25,
        gpu=None,
        torch_cuda=None,
    )

    hud = collect_runtime_hud(lambda: snapshot)
    assert hud["cpu_percent"] == 12.3
    assert hud["gpu"] is None
    assert hud["torch_cuda"] is None
    assert hud["active_backend"] is None
    assert hud["active_model"] is None
    assert hud["active_job"] is None


def test_runtime_hud_adapter_uses_canonical_snapshot_fields() -> None:
    gpu = SimpleNamespace(
        index=0,
        name="Fixture GPU",
        utilization_percent=50.0,
        memory_used_mib=2048.0,
        memory_free_mib=6144.0,
        memory_total_mib=8192.0,
        memory_percent=25.0,
        temperature_c=55.0,
        power_draw_w=120.0,
        power_limit_w=250.0,
    )
    torch_cuda = SimpleNamespace(
        device_name="Fixture GPU",
        allocated_mib=512.0,
        reserved_mib=768.0,
        peak_allocated_mib=1024.0,
    )
    snapshot = SimpleNamespace(
        sampled_at=123.0,
        system_status="OK",
        gpu_status="OK",
        cpu_percent=10.0,
        ram_used_bytes=None,
        ram_available_bytes=None,
        ram_total_bytes=None,
        ram_percent=None,
        process_rss_bytes=None,
        process_cpu_percent=None,
        gpu=gpu,
        torch_cuda=torch_cuda,
    )

    hud = collect_runtime_hud(lambda: snapshot)
    assert hud["gpu"]["name"] == "Fixture GPU"
    assert hud["gpu"]["memory_free_mib"] == 6144.0
    assert hud["torch_cuda"]["allocated_mib"] == 512.0


def test_workstation_startup_does_not_import_optional_heavy_backends() -> None:
    code = r'''
import sys
import genre_test.workstation.server
forbidden = (
    "torch",
    "transformers",
    "librosa",
    "genre_test.retrieval",
    "genre_test.mastering",
)
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden)
)
if loaded:
    raise SystemExit("unexpected heavy imports: " + ", ".join(loaded))
'''
    completed = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

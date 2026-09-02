from __future__ import annotations

import http.client
import json
import os
import socket
import threading
from contextlib import contextmanager
from importlib import resources
from pathlib import Path

import pytest

from genre_test.workstation.contracts import validate_derived_output_path
from genre_test.workstation.i18n import catalog, validate_catalog
from genre_test.workstation.server import create_server, is_loopback_host
from genre_test.workstation.service import WorkstationService
from genre_test.workstation.settings import SettingsStore


@contextmanager
def _running_server(tmp_path: Path, host: str = "127.0.0.1"):
    service = WorkstationService(settings_store=SettingsStore(tmp_path / "settings.json"))
    server = create_server(host, 0, service=service, quiet=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        bound_host, port = server.server_address[:2]
        yield str(bound_host), int(port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _request(
    host: str,
    port: int,
    method: str,
    path: str,
    *,
    authority: str | None = None,
) -> tuple[int, dict[str, str], bytes]:
    connection = http.client.HTTPConnection(host, port, timeout=3)
    headers = {}
    if authority is not None:
        headers["Host"] = authority
    try:
        connection.request(method, path, headers=headers)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_dns_rebinding_host_is_rejected_before_api_dispatch(tmp_path: Path) -> None:
    with _running_server(tmp_path) as (host, port):
        status, headers, body = _request(
            host,
            port,
            "GET",
            "/api/v1/health",
            authority="attacker.example",
        )
    payload = json.loads(body.decode("utf-8"))
    assert status == 421
    assert payload["error"]["code"] == "invalid_host"
    assert headers["X-Content-Type-Options"] == "nosniff"


def test_loopback_literal_authority_is_accepted(tmp_path: Path) -> None:
    with _running_server(tmp_path) as (host, port):
        status, _headers, body = _request(
            host,
            port,
            "GET",
            "/api/v1/health",
            authority=f"127.0.0.1:{port}",
        )
    assert status == 200
    assert json.loads(body.decode("utf-8"))["ok"] is True


def test_localhost_bind_requires_resolved_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_getaddrinfo(*_args: object, **_kwargs: object):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.10", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    assert is_loopback_host("localhost") is False


def test_ipv6_loopback_uses_ipv6_server_when_available(tmp_path: Path) -> None:
    if not socket.has_ipv6:
        pytest.skip("IPv6 unavailable")
    try:
        with _running_server(tmp_path, "::1") as (host, port):
            connection = http.client.HTTPConnection(host, port, timeout=3)
            try:
                connection.request("GET", "/api/v1/health", headers={"Host": f"[::1]:{port}"})
                response = connection.getresponse()
                body = response.read()
            finally:
                connection.close()
    except OSError as exc:
        pytest.skip(f"IPv6 loopback unavailable: {exc}")
    assert response.status == 200
    assert json.loads(body.decode("utf-8"))["ok"] is True


def test_unsupported_api_method_is_structured_json(tmp_path: Path) -> None:
    with _running_server(tmp_path) as (host, port):
        status, headers, body = _request(host, port, "PATCH", "/api/v1/health")
    payload = json.loads(body.decode("utf-8"))
    assert status == 405
    assert payload["error"]["code"] == "method_not_allowed"
    assert headers["Content-Type"].startswith("application/json")
    assert headers["Content-Security-Policy"].startswith("default-src 'self'")


def test_hard_link_output_alias_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    alias = tmp_path / "alias.wav"
    source.write_bytes(b"fixture")
    try:
        os.link(source, alias)
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")
    with pytest.raises(ValueError, match="alias the source"):
        validate_derived_output_path(source, alias)


def test_shell_does_not_probe_runtime_until_explicit_refresh() -> None:
    javascript = (
        resources.files("genre_test.workstation.static")
        .joinpath("app.js")
        .read_text(encoding="utf-8")
    )
    initialize_body = javascript.split("async function initialize()", 1)[1].split(
        "document.getElementById", 1
    )[0]
    assert "loadRuntime(" not in initialize_body
    assert 'runtime-refresh")?.addEventListener' in javascript
    assert "void loadRuntime()" in javascript


def test_settings_and_capabilities_have_complete_ru_en_ui_strings() -> None:
    validate_catalog()
    ru = catalog("ru")
    en = catalog("en")
    assert ru["panel.settings.body"] != ru["panel.deferred.body"]
    assert en["panel.settings.body"] != en["panel.deferred.body"]
    keys = (
        "workstation_shell",
        "runtime_hud",
        "analysis",
        "catalog",
        "search",
        "compare_transport",
        "repair",
        "stems",
        "mastering",
        "delivery",
    )
    for key in keys:
        assert ru[f"capability.{key}"]
        assert en[f"capability.{key}"]
    for state in ("available", "unavailable", "deferred"):
        assert ru[f"capability.state.{state}"]
        assert en[f"capability.state.{state}"]
    for phase in ("p2", "p3", "p5", "p6", "p7", "p8"):
        assert ru[f"capability.reason.workstation_{phase}"]
        assert en[f"capability.reason.workstation_{phase}"]

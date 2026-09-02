from __future__ import annotations

import argparse
import ipaddress
import json
import mimetypes
import socket
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .contracts import API_VERSION, ApiError
from .service import WorkstationService

MAX_JSON_BODY = 16 * 1024
STATIC_MAP = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/assets/app.css": ("app.css", "text/css; charset=utf-8"),
    "/assets/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


def is_loopback_host(host: str) -> bool:
    """Resolve a bind host and require every returned address to be loopback."""

    value = host.strip().lower()
    if not value:
        return False
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(value, None, type=socket.SOCK_STREAM)
            if item and item[4]
        }
    except socket.gaierror:
        return False
    if not addresses:
        return False
    try:
        return all(ipaddress.ip_address(address).is_loopback for address in addresses)
    except ValueError:
        return False


def _request_authority_is_allowed(authority: str | None) -> bool:
    """Reject DNS-rebinding Host values; allow only localhost or loopback literals."""

    if authority is None or not authority.strip():
        return False
    raw = authority.strip()
    try:
        parsed = urlsplit(f"//{raw}")
        host = parsed.hostname
        _ = parsed.port
    except ValueError:
        return False
    if parsed.username is not None or parsed.password is not None or host is None:
        return False
    normalized = host.rstrip(".").lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _static_bytes(name: str) -> bytes:
    return resources.files("genre_test.workstation.static").joinpath(name).read_bytes()


def _handler(service: WorkstationService) -> type[BaseHTTPRequestHandler]:
    class WorkstationHandler(BaseHTTPRequestHandler):
        server_version = "GenreTestWorkstation/1"
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:
            if getattr(self.server, "quiet", False):
                return
            super().log_message(format, *args)

        def _headers(self, status: int, content_type: str, length: int) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'",
            )
            self.end_headers()

        def _json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
            body = json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
            self._headers(int(status), "application/json; charset=utf-8", len(body))
            self.wfile.write(body)

        def _error(self, code: str, message: str, status: int) -> None:
            self._json(
                ApiError(code=code, message=message, status=status).to_dict(),
                status,
            )

        def _validate_authority(self) -> bool:
            if _request_authority_is_allowed(self.headers.get("Host")):
                return True
            self._error(
                "invalid_host",
                "Host must be localhost or a loopback IP literal",
                HTTPStatus.MISDIRECTED_REQUEST,
            )
            return False

        def _read_json(self) -> dict[str, Any] | None:
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                self._error("missing_content_length", "Content-Length is required", 411)
                return None
            try:
                length = int(raw_length)
            except ValueError:
                self._error("invalid_content_length", "Content-Length is invalid", 400)
                return None
            if length < 0 or length > MAX_JSON_BODY:
                self._error("request_too_large", "JSON request body is too large", 413)
                return None
            content_type = (
                self.headers.get("Content-Type", "")
                .split(";", 1)[0]
                .strip()
                .lower()
            )
            if content_type != "application/json":
                self._error("unsupported_media_type", "application/json is required", 415)
                return None
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._error(
                    "invalid_json",
                    "Request body must be valid UTF-8 JSON",
                    400,
                )
                return None
            if not isinstance(payload, dict):
                self._error(
                    "invalid_json_shape",
                    "JSON request body must be an object",
                    400,
                )
                return None
            return payload

        def _serve_static(self, path: str) -> bool:
            selected = STATIC_MAP.get(path)
            if selected is None:
                return False
            name, content_type = selected
            try:
                body = _static_bytes(name)
            except (FileNotFoundError, OSError):
                self._error(
                    "static_asset_missing",
                    f"Workstation asset is unavailable: {name}",
                    500,
                )
                return True
            guessed = mimetypes.guess_type(name)[0] or "application/octet-stream"
            self._headers(200, content_type or guessed, len(body))
            self.wfile.write(body)
            return True

        def _unsupported_method(self) -> None:
            if not self._validate_authority():
                return
            path = urlsplit(self.path).path
            if path.startswith("/api/v1/"):
                self._error(
                    "method_not_allowed",
                    "HTTP method is not supported for this API endpoint",
                    HTTPStatus.METHOD_NOT_ALLOWED,
                )
                return
            self._error("not_found", "Endpoint not found", HTTPStatus.NOT_FOUND)

        def do_GET(self) -> None:
            if not self._validate_authority():
                return
            parsed = urlsplit(self.path)
            path = parsed.path
            if self._serve_static(path):
                return
            if path == "/api/v1/health":
                self._json(service.health())
                return
            if path == "/api/v1/navigation":
                self._json(service.navigation())
                return
            if path == "/api/v1/capabilities":
                self._json(service.capabilities())
                return
            if path == "/api/v1/runtime":
                try:
                    self._json(service.runtime())
                except (ImportError, OSError, RuntimeError) as exc:
                    self._error(
                        "runtime_unavailable",
                        f"Runtime telemetry unavailable: {type(exc).__name__}",
                        503,
                    )
                return
            if path == "/api/v1/settings":
                self._json(service.settings())
                return
            if path == "/api/v1/i18n":
                query = parse_qs(parsed.query, keep_blank_values=True)
                self._json(service.translations(query.get("lang", [None])[0]))
                return
            if path == "/api/v1/jobs":
                self._json(service.list_jobs())
                return
            if path.startswith("/api/v1/jobs/"):
                job_id = path.removeprefix("/api/v1/jobs/").strip("/")
                if not job_id or "/" in job_id:
                    self._error("not_found", "Endpoint not found", 404)
                    return
                job = service.get_job(job_id)
                if job is None:
                    self._error("job_not_found", "Job does not exist", 404)
                else:
                    self._json(job)
                return
            self._error("not_found", "Endpoint not found", 404)

        def do_POST(self) -> None:
            if not self._validate_authority():
                return
            parsed = urlsplit(self.path)
            if parsed.path == "/api/v1/jobs":
                payload = self._read_json()
                if payload is None:
                    return
                kind = str(payload.get("kind", "contract_stub")).strip() or "contract_stub"
                if len(kind) > 80:
                    self._error("invalid_job_kind", "Job kind is too long", 400)
                    return
                self._json(service.create_contract_job(kind), 201)
                return
            if (
                parsed.path.startswith("/api/v1/jobs/")
                and parsed.path.endswith("/cancel")
            ):
                job_id = (
                    parsed.path.removeprefix("/api/v1/jobs/")
                    .removesuffix("/cancel")
                    .strip("/")
                )
                if not job_id or "/" in job_id:
                    self._error("not_found", "Endpoint not found", 404)
                    return
                job = service.cancel_job(job_id)
                if job is None:
                    self._error("job_not_found", "Job does not exist", 404)
                else:
                    self._json(job)
                return
            self._error("not_found", "Endpoint not found", 404)

        def do_PUT(self) -> None:
            if not self._validate_authority():
                return
            if urlsplit(self.path).path != "/api/v1/settings/language":
                self._error("not_found", "Endpoint not found", 404)
                return
            payload = self._read_json()
            if payload is None:
                return
            language = payload.get("language")
            if not isinstance(language, str):
                self._error("invalid_language", "language must be a string", 400)
                return
            try:
                settings = service.set_language(language)
            except (OSError, ValueError) as exc:
                status = 400 if isinstance(exc, ValueError) else 500
                code = "invalid_language" if status == 400 else "settings_write_failed"
                self._error(code, str(exc), status)
                return
            self._json(settings)

        def do_PATCH(self) -> None:
            self._unsupported_method()

        def do_DELETE(self) -> None:
            self._unsupported_method()

        def do_OPTIONS(self) -> None:
            self._unsupported_method()

    return WorkstationHandler


class WorkstationHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        service: WorkstationService | None = None,
        *,
        quiet: bool = False,
    ) -> None:
        host, _port = server_address
        if not is_loopback_host(host):
            raise ValueError("workstation P1 may bind only to a loopback host")
        self.service = service or WorkstationService()
        self.quiet = quiet
        super().__init__(server_address, _handler(self.service))


class WorkstationHTTPServerV6(WorkstationHTTPServer):
    address_family = socket.AF_INET6


def _server_class_for_host(host: str) -> type[WorkstationHTTPServer]:
    try:
        literal = ipaddress.ip_address(host.strip())
    except ValueError:
        return WorkstationHTTPServer
    return WorkstationHTTPServerV6 if literal.version == 6 else WorkstationHTTPServer


def create_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    service: WorkstationService | None = None,
    quiet: bool = False,
) -> WorkstationHTTPServer:
    if port < 0 or port > 65535:
        raise ValueError("port must be between 0 and 65535")
    server_class = _server_class_for_host(host)
    return server_class((host, port), service=service, quiet=quiet)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Start the Genre_test local workstation P1 shell."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    try:
        server = create_server(args.host, args.port, quiet=args.quiet)
    except (OSError, ValueError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    host, port = server.server_address[:2]
    url_host = f"[{host}]" if ":" in str(host) else host
    print(f"Genre_test Workstation {API_VERSION}: http://{url_host}:{port}")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

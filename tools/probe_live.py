#!/usr/bin/env python3
"""HTTP probe for a site that has actually been deployed.

This does not look at dist/ or warhammer-dist/. A green local build is not a
passing probe. Retries are capped. A redirect, a wrong body, or a bad asset
fails the run, except the one Pages hop from /login.html to /login.
pull_request cannot call the live sites: that event has not deployed anything.

--self-test serves the same contracts on 127.0.0.1 and requires the failures
to fail. It does not contact production.
"""
from __future__ import annotations

import argparse
import http.client
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import urljoin, urlsplit

ROUNDS = 4
TIMEOUT = 10
PAUSE = 8
USER_AGENT = "sephiria-guide-probe/1"

Check = dict
Fetch = Callable[[str, int], tuple[int, str, bytes, str]]


def site_checks(site: str) -> tuple[str, list[Check]]:
    if site == "sephiria":
        origin = "https://sephiria-guide.com"
        checks = [
            {"path": "/", "contains": ["Your adventure starts here.", "beginner-guide", "app/2436940"]},
            {"path": "/beginner-guide/", "contains": ["Sephiria beginner guide", "Side Bag"]},
            {"path": "/guides/", "contains": ["Sephiria guide hub", "/beginner-guide/"]},
            {
                "path": "/login.html",
                # Cloudflare Pages permanently redirects the file URL to /login.
                "allow_redirect": "/login",
                "contains": ["Log in", "/assets/login.js", 'id="providers"'],
            },
            {"path": "/assets/styles.css", "content_type": "text/css", "contains": ["box-sizing"]},
            {"path": "/assets/theme.css", "content_type": "text/css", "contains": ["--accent:"]},
            {"path": "/assets/img/village.png", "content_type": "image/", "magic": b"\x89PNG"},
            {
                "path": "/assets/login.js",
                "content_types": ("text/javascript", "application/javascript"),
                "contains": ["/api/auth/start?provider="],
            },
        ]
    elif site == "warhammer":
        origin = "https://warhammersurvivors.com"
        checks = [
            {"path": "/", "contains": ["Warhammer Survivors", "10 November 2026", 'href="/guide/"']},
            {"path": "/guide/", "contains": ["Warhammer Survivors Beginner Guide", "paint pots"]},
            {"path": "/codex/characters/", "contains": ['id="cx-q"', 'class="cx-card']},
            {"path": "/assets/wh.css", "content_type": "text/css", "contains": ["--gold:"]},
            {"path": "/assets/ss1.jpg", "content_type": "image/", "magic": b"\xff\xd8"},
        ]
    else:
        raise SystemExit(f"unknown site {site}")
    return origin, checks


def fetch(url: str, timeout: int) -> tuple[int, str, bytes, str]:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError(f"unsupported probe URL {url}")
    connection_cls = http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
    port = parts.port or (443 if parts.scheme == "https" else 80)
    path = parts.path or "/"
    if parts.query:
        path = f"{path}?{parts.query}"
    connection = connection_cls(parts.hostname, port, timeout=timeout)
    try:
        connection.request(
            "GET",
            path,
            headers={
                "User-Agent": USER_AGENT,
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Accept": "*/*",
            },
        )
        response = connection.getresponse()
        body = response.read()
        content_type = response.getheader("Content-Type") or ""
        return response.status, content_type, body, response.getheader("Location") or ""
    finally:
        connection.close()


def evaluate(check: Check, status: int, content_type: str, body: bytes) -> str | None:
    path = check["path"]
    if status != 200:
        return f"{path} HTTP {status}"
    header = content_type.strip().lower()
    want_types = list(check.get("content_types") or [])
    if check.get("content_type"):
        want_types.append(check["content_type"])
    if want_types and not any(header.startswith(item) for item in want_types):
        return f"{path} content-type {content_type!r} is not one of {want_types}"
    magic = check.get("magic")
    if magic and not body.startswith(magic):
        return f"{path} body does not start with the expected bytes"
    text = body.decode("utf-8", "replace")
    for needle in check.get("contains") or []:
        if needle not in text:
            return f"{path} missing {needle!r}"
    if not body:
        return f"{path} empty body"
    return None


def read_check(origin: str, check: Check, timeout: int, fetch_url: Fetch) -> str | None:
    """Return an error string, or None when the check holds.

    One same-origin redirect is accepted only when the check names the exact
    destination path. Any other redirect fails without being followed.
    """
    url = origin.rstrip("/") + check["path"]
    status, content_type, body, location = fetch_url(url, timeout)
    allowed = check.get("allow_redirect")
    if allowed and status in (301, 302, 303, 307, 308):
        dest = urlsplit(urljoin(url, location))
        base = urlsplit(origin)
        if (
            dest.scheme == base.scheme
            and dest.netloc == base.netloc
            and dest.path == allowed
            and not dest.query
        ):
            status, content_type, body, _location = fetch_url(origin.rstrip("/") + allowed, timeout)
        else:
            return f"{check['path']} redirected to {location or '(nowhere)'}"
    return evaluate(check, status, content_type, body)


def probe(
    origin: str,
    checks: list[Check],
    *,
    rounds: int = ROUNDS,
    timeout: int = TIMEOUT,
    pause: float = PAUSE,
    fetch_url: Fetch = fetch,
) -> list[str]:
    pending = list(checks)
    last: list[str] = []
    for round_index in range(1, rounds + 1):
        last = []
        still: list[Check] = []
        for check in pending:
            url = origin.rstrip("/") + check["path"]
            try:
                error = read_check(origin, check, timeout, fetch_url)
            except Exception as exc:  # noqa: BLE001 — network failures are probe failures
                error = f"{check['path']} {type(exc).__name__}: {exc}"
            if error:
                still.append(check)
                last.append(error)
                print(f"RETRY {round_index}/{rounds} {error}", flush=True)
            else:
                print(f"PASS {url}", flush=True)
        pending = still
        if not pending:
            return []
        if round_index < rounds and pause:
            time.sleep(pause)
    print(f"FAIL after {rounds} rounds", flush=True)
    for error in last:
        print(f"FAIL {error}", flush=True)
    return last


def _serve(routes: dict[str, tuple[int, dict[str, str], bytes]], hits: dict[str, int]) -> tuple[ThreadingHTTPServer, str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            hits["n"] = hits.get("n", 0) + 1
            path = self.path.split("?", 1)[0]
            status, headers, body = routes.get(path, (404, {"Content-Type": "text/plain"}, b"missing"))
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    return server, f"http://{host}:{port}"


def _body_for(check: Check) -> tuple[dict[str, str], bytes]:
    declared = check.get("content_type") or (check.get("content_types") or ["text/html"])[0]
    content_type = "text/html; charset=utf-8"
    if declared == "text/css":
        content_type = "text/css; charset=utf-8"
    elif declared.startswith("text/javascript") or declared.startswith("application/javascript"):
        content_type = "text/javascript; charset=utf-8"
    elif declared.startswith("image/"):
        content_type = "image/png" if check["path"].endswith(".png") else "image/jpeg"
    body = check.get("magic", b"") + " ".join(check.get("contains") or []).encode()
    if not body:
        body = b"ok"
    return {"Content-Type": content_type}, body


def _assert(condition: bool, message: str, failures: list[str]) -> None:
    if condition:
        print(f"PASS {message}")
    else:
        failures.append(message)
        print(f"FAIL {message}")


def self_test() -> int:
    failures: list[str] = []
    for site in ("sephiria", "warhammer"):
        _origin, checks = site_checks(site)
        routes = {check["path"]: (200, *_body_for(check)) for check in checks}
        server, origin = _serve(routes, {})
        try:
            if not origin.startswith("http://127.0.0.1:"):
                raise SystemExit(f"self-test left localhost: {origin}")
            found = probe(origin, checks, rounds=1, timeout=2, pause=0)
            _assert(found == [], f"{site} local contract is accepted", failures)
        finally:
            server.shutdown()
            server.server_close()

    _origin, checks = site_checks("sephiria")
    bad_routes = {check["path"]: (200, *_body_for(check)) for check in checks}
    headers, _body = _body_for(checks[0])
    bad_routes["/"] = (200, headers, b"this page has neither marker")
    server, origin = _serve(bad_routes, {})
    try:
        found = probe(origin, checks, rounds=2, timeout=2, pause=0)
        _assert(any("Your adventure starts here." in item for item in found), "missing home marker fails", failures)
    finally:
        server.shutdown()
        server.server_close()

    hits: dict[str, int] = {"n": 0}
    only = {"path": "/down", "contains": ["ready"]}
    server, origin = _serve({"/down": (500, {"Content-Type": "text/plain"}, b"nope")}, hits)
    try:
        found = probe(origin, [only], rounds=4, timeout=2, pause=0)
        _assert(found == ["/down HTTP 500"], "HTTP 500 fails closed", failures)
        _assert(hits["n"] == 4, "a failing URL is retried exactly 4 times", failures)
    finally:
        server.shutdown()
        server.server_close()

    redirected = {
        "/": (302, {"Location": "/real", "Content-Type": "text/html"}, b""),
        "/real": (200, *_body_for(checks[0])),
    }
    server, origin = _serve(redirected, {})
    try:
        found = probe(origin, [checks[0]], rounds=1, timeout=2, pause=0)
        _assert(found == ["/ HTTP 302"], "a redirect is not treated as the page", failures)
    finally:
        server.shutdown()
        server.server_close()

    login = next(check for check in checks if check["path"] == "/login.html")
    login_body = b'Log in <script src="/assets/login.js"></script> <div id="providers">'
    hopped = {
        "/login.html": (308, {"Location": "/login", "Content-Type": "text/html"}, b""),
        "/login": (200, {"Content-Type": "text/html; charset=utf-8"}, login_body),
    }
    server, origin = _serve(hopped, {})
    try:
        found = probe(origin, [login], rounds=1, timeout=2, pause=0)
        _assert(found == [], "the Pages /login.html hop to /login is accepted", failures)
    finally:
        server.shutdown()
        server.server_close()

    escaped = {
        "/login.html": (308, {"Location": "https://evil.example/login", "Content-Type": "text/html"}, b""),
    }
    server, origin = _serve(escaped, {})
    try:
        found = probe(origin, [login], rounds=1, timeout=2, pause=0)
        _assert(
            any("redirected to https://evil.example/login" in item for item in found),
            "an off-site login redirect fails",
            failures,
        )
    finally:
        server.shutdown()
        server.server_close()

    if failures:
        print(f"FAIL probe self-test ({len(failures)})")
        return 1
    print("PASS probe self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", choices=("sephiria", "warhammer"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event in ("pull_request", "pull_request_target"):
        print(f"FAIL live probe cannot run from {event}")
        return 1
    if not args.site:
        parser.error("--site is required")
    origin, checks = site_checks(args.site)
    print(f"probing {origin} after deploy", flush=True)
    failures = probe(origin, checks)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

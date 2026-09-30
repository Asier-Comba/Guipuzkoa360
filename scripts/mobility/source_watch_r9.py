"""Bounded, opt-in source watcher for W1 maintenance; never used by runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit
from urllib.request import Request, urlopen


ALLOWED_HOSTS = {
    "api.openstreetmap.org",
    "opendata.euskadi.eus",
    "www.euskadi.eus",
    "www.osakidetza.euskadi.eus",
    "moveuskadi.euskadi.eus",
}
SENSITIVE_QUERY_KEYS = {"access_token", "api_key", "apikey", "key", "password", "secret", "signature", "token"}
USER_AGENT = "GIPUZKOA360-W1-source-governance/1.0 (+https://github.com/Asier-Comba/Guipuzkoa360)"
DEFAULT_MAX_BYTES = 25_000_000


def validate_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("URL must use HTTPS and an allowlisted host")
    if parsed.username or parsed.password:
        raise ValueError("credentials in URL are forbidden")
    if any(key.lower() in SENSITIVE_QUERY_KEYS for key, _ in parse_qsl(parsed.query, keep_blank_values=True)):
        raise ValueError("credential-like query parameter is forbidden")


def fetch(url: str, output: Path, *, max_bytes: int = DEFAULT_MAX_BYTES, timeout: float = 20.0, opener=urlopen) -> dict:
    validate_url(url)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    checked_at = datetime.now(timezone.utc).isoformat()
    try:
        with opener(request, timeout=timeout) as response:
            status = int(getattr(response, "status", response.getcode()))
            if not 200 <= status < 300:
                return {"url": url, "checked_at_utc": checked_at, "status": "HTTP_ERROR", "http_status": status}
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > max_bytes:
                raise ValueError("declared body exceeds byte limit")
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError("body exceeds byte limit")
    except Exception as exc:
        return {"url": url, "checked_at_utc": checked_at, "status": "FETCH_ERROR", "error_type": type(exc).__name__, "error": str(exc)}
    output.write_bytes(body)
    return {"url": url, "checked_at_utc": checked_at, "status": "FETCHED", "http_status": status,
            "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "output": output.as_posix()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()
    result = fetch(args.url, args.output, max_bytes=args.max_bytes, timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    raise SystemExit(0 if result["status"] == "FETCHED" else 2)


if __name__ == "__main__":
    main()

"""WHOOP v2 API client for the history exporter.

Resolves a usable access token from the whoop-ai-mcp token store
(~/.whoop-mcp/tokens.json) and performs paginated GETs against the WHOOP v2 API.

Design notes:
- HTTP goes through `curl` with a browser User-Agent. Some environments get a
  Cloudflare 403 (error 1010) for urllib/requests User-Agents; curl with a
  browser UA returns 200.
- The common path is READ-ONLY: if the on-disk access token is still valid, the
  exporter reads it and makes GETs — no token refresh, so it never rotates the
  refresh token or collides with a running Whoop MCP. Schedule the export shortly
  after something else refreshes the token (e.g. a daily brief) to stay on this
  path.
- If the on-disk token is expired, do exactly ONE atomic, flock-guarded refresh
  (re-read fresh under the lock, refresh, write .tmp->rename + .bak).

Stdlib only: no requests/pandas; curl via subprocess.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import time
from urllib.parse import urlencode

# --- Constants (matched to the whoop-ai-mcp package endpoints) ----------------

BASE_URL = "https://api.prod.whoop.com/developer"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

TOKENS_PATH = os.path.expanduser("~/.whoop-mcp/tokens.json")
LOCK_PATH = os.path.expanduser("~/.whoop-mcp/.export.lock")
CLAUDE_JSON_PATH = os.path.expanduser("~/.claude.json")

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Treat a token with less than this much life left as expired (safety margin).
VALIDITY_MARGIN_S = 300
# WHOOP collection page size cap.
PAGE_LIMIT = 25
# Defensive cap so a runaway loop can never hammer the API.
MAX_PAGES = 400

# Endpoint paths relative to BASE_URL.
ENDPOINTS = {
    "recovery": "/v2/recovery",
    "sleep": "/v2/activity/sleep",
    "cycle": "/v2/cycle",
    "workout": "/v2/activity/workout",
    "body": "/v2/user/measurement/body",
    "profile": "/v2/user/profile/basic",
}


class WhoopClientError(RuntimeError):
    """Raised on auth or HTTP failures the caller should surface."""


# --- token store --------------------------------------------------------------


def _now_ms() -> int:
    return int(time.time() * 1000)


def _read_tokens(path: str = TOKENS_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_tokens_atomic(data: dict, path: str = TOKENS_PATH) -> None:
    """Atomically replace the token file, keeping a .bak of the prior contents."""
    tmp = path + ".tmp"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as src:
                prior = src.read()
            with open(path + ".bak", "w", encoding="utf-8") as bak:
                bak.write(prior)
        except OSError:
            pass  # backup is best-effort; never block the write on it
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _token_is_valid(tokens: dict) -> bool:
    exp = tokens.get("expires_at")
    if not exp:
        return False
    # expires_at is epoch MILLISECONDS.
    return (exp - _now_ms()) > VALIDITY_MARGIN_S * 1000


def _load_client_creds() -> tuple[str, str]:
    """WHOOP client_id/secret, from env first, then ~/.claude.json mcpServers.whoop.env."""
    cid = os.environ.get("WHOOP_CLIENT_ID")
    secret = os.environ.get("WHOOP_CLIENT_SECRET")
    if cid and secret:
        return cid, secret
    try:
        conf = json.load(open(CLAUDE_JSON_PATH, "r", encoding="utf-8"))
    except OSError as exc:
        raise WhoopClientError(f"cannot read {CLAUDE_JSON_PATH}: {exc}") from exc

    def _find(obj):
        if isinstance(obj, dict):
            if "whoop" in obj and isinstance(obj["whoop"], dict):
                env = obj["whoop"].get("env", {})
                if "WHOOP_CLIENT_ID" in env and "WHOOP_CLIENT_SECRET" in env:
                    return env["WHOOP_CLIENT_ID"], env["WHOOP_CLIENT_SECRET"]
            for v in obj.values():
                found = _find(v)
                if found:
                    return found
        return None

    found = _find(conf)
    if not found:
        raise WhoopClientError(
            "WHOOP_CLIENT_ID/SECRET not in env or ~/.claude.json mcpServers.whoop.env"
        )
    return found


# --- HTTP via curl ------------------------------------------------------------


def _curl(args: list[str]) -> tuple[int, str]:
    """Run curl, returning (http_status, body). Appends status via -w sentinel."""
    sentinel = "\n__HTTP_STATUS__:"
    full = ["curl", "-sS", "-A", BROWSER_UA, "-w", f"{sentinel}%{{http_code}}"] + args
    proc = subprocess.run(full, capture_output=True, text=True)
    if proc.returncode != 0:
        raise WhoopClientError(f"curl failed (exit {proc.returncode}): {proc.stderr.strip()}")
    out = proc.stdout
    body, _, status = out.rpartition(sentinel)
    try:
        return int(status.strip()), body
    except ValueError as exc:
        raise WhoopClientError(f"could not parse curl status from output: {out[-200:]!r}") from exc


def _curl_get_json(url: str, token: str) -> tuple[int, dict]:
    status, body = _curl([url, "-H", f"Authorization: Bearer {token}"])
    if status == 401:
        return status, {}
    if status < 200 or status >= 300:
        raise WhoopClientError(f"GET {url} -> HTTP {status}: {body[:300]}")
    return status, (json.loads(body) if body.strip() else {})


# --- token refresh (fallback only) --------------------------------------------


def _refresh_guarded() -> str:
    """One atomic, flock-guarded refresh. Returns the new access token.

    WHOOP rotates refresh tokens on every refresh (RFC 6749 §6), so this must
    never run concurrently and must persist the rotated token immediately:
    re-read fresh under the lock, refresh, save at once. The flock serializes
    against another export run sharing the same token store.
    """
    cid, secret = _load_client_creds()
    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
    with open(LOCK_PATH, "w") as lockfh:
        fcntl.flock(lockfh, fcntl.LOCK_EX)
        try:
            tokens = _read_tokens()
            # Another holder of the lock may have just refreshed.
            if _token_is_valid(tokens):
                return tokens["access_token"]
            refresh_token = tokens.get("refresh_token")
            if not refresh_token:
                raise WhoopClientError("no refresh_token in token store")
            payload = urlencode(
                {
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": cid,
                    "client_secret": secret,
                    "scope": "offline",
                }
            )
            status, body = _curl(
                [
                    TOKEN_URL,
                    "-X", "POST",
                    "-H", "Content-Type: application/x-www-form-urlencoded",
                    "--data", payload,
                ]
            )
            if status < 200 or status >= 300:
                raise WhoopClientError(f"token refresh -> HTTP {status}: {body[:300]}")
            data = json.loads(body)
            new = {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
                "expires_at": _now_ms() + int(data.get("expires_in", 3600)) * 1000,
                "token_type": data.get("token_type", "bearer"),
            }
            _write_tokens_atomic(new)
            return new["access_token"]
        finally:
            fcntl.flock(lockfh, fcntl.LOCK_UN)


def load_token() -> str:
    """Return a usable access token. Read-only if the on-disk token is fresh."""
    tokens = _read_tokens()
    if _token_is_valid(tokens):
        return tokens["access_token"]
    return _refresh_guarded()


# --- public API ---------------------------------------------------------------


def get(domain: str, start: str | None = None, end: str | None = None) -> list[dict]:
    """Fetch all records for a paginated collection domain in [start, end].

    `start`/`end` are ISO-8601 (e.g. 2026-01-01T00:00:00.000Z). Sends `nextToken`
    on subsequent pages; reads `next_token` / `records` from the response.
    Refreshes once on a mid-pull 401 (rare) and retries the page.
    """
    if domain not in ENDPOINTS:
        raise WhoopClientError(f"unknown domain {domain!r}")
    token = load_token()
    base = BASE_URL + ENDPOINTS[domain]

    params: dict[str, str] = {"limit": str(PAGE_LIMIT)}
    if start:
        params["start"] = start
    if end:
        params["end"] = end

    records: list[dict] = []
    next_token: str | None = None
    refreshed = False
    for _ in range(MAX_PAGES):
        q = dict(params)
        if next_token:
            q["nextToken"] = next_token
        url = f"{base}?{urlencode(q)}"
        status, payload = _curl_get_json(url, token)
        if status == 401:
            if refreshed:
                raise WhoopClientError(f"GET {url} -> 401 after refresh")
            token = _refresh_guarded()
            refreshed = True
            continue
        records.extend(payload.get("records", []))
        next_token = payload.get("next_token")
        if not next_token:
            break
    return records


def get_single(domain: str) -> dict:
    """Fetch a non-paginated single-object endpoint (body, profile)."""
    if domain not in ENDPOINTS:
        raise WhoopClientError(f"unknown domain {domain!r}")
    token = load_token()
    url = BASE_URL + ENDPOINTS[domain]
    status, payload = _curl_get_json(url, token)
    if status == 401:
        token = _refresh_guarded()
        status, payload = _curl_get_json(url, token)
        if status == 401:
            raise WhoopClientError(f"GET {url} -> 401 after refresh")
    return payload

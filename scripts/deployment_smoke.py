"""Read-only smoke checks for a deployed NEXUS API and PWA."""

import json
import os
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


REQUIRED_PATHS = {
    "/auth/login",
    "/profile/me",
    "/knowledge/documents",
    "/learn/goals",
    "/money/transactions",
    "/work/projects",
    "/intelligence/search",
    "/notifications",
}


def normalized_url(variable: str) -> str:
    value = os.getenv(variable, "").strip().rstrip("/")
    if not value:
        raise RuntimeError(f"Set {variable} before running this script")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"{variable} must be an absolute HTTP(S) origin")
    if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise RuntimeError(f"{variable} must use HTTPS outside localhost")
    return value


def get(url: str, expected_content_type: str | None = None) -> bytes:
    request = Request(url, headers={"User-Agent": "NEXUS-deployment-smoke/1.0"})
    with urlopen(request, timeout=90, context=ssl.create_default_context()) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        if expected_content_type and expected_content_type not in response.headers.get("Content-Type", ""):
            raise RuntimeError(f"{url} returned an unexpected content type")
        return response.read()


def main() -> None:
    api = normalized_url("NEXUS_API_URL")
    frontend = normalized_url("NEXUS_FRONTEND_URL")

    health = json.loads(get(f"{api}/health", "application/json"))
    if health != {"status": "healthy"}:
        raise RuntimeError("API health response did not match the contract")
    print("PASS API health")

    schema = json.loads(get(f"{api}/openapi.json", "application/json"))
    if schema.get("info", {}).get("version") != "0.12.0":
        raise RuntimeError("Deployed API version is not 0.12.0")
    missing = REQUIRED_PATHS - set(schema.get("paths", {}))
    if missing:
        raise RuntimeError(f"Deployed OpenAPI is missing paths: {sorted(missing)}")
    print("PASS API version and required routes")

    html = get(frontend, "text/html").decode("utf-8")
    if "NEXUS AI" not in html or "manifest.webmanifest" not in html:
        raise RuntimeError("Frontend HTML does not contain the NEXUS PWA shell")
    print("PASS frontend HTML")

    manifest = json.loads(get(f"{frontend}/manifest.webmanifest"))
    if manifest.get("name") != "NEXUS AI" or manifest.get("display") != "standalone":
        raise RuntimeError("PWA manifest does not match the install contract")
    print("PASS PWA manifest")

    service_worker = get(f"{frontend}/sw.js").decode("utf-8")
    if "addEventListener" not in service_worker or "fetch" not in service_worker:
        raise RuntimeError("Service worker does not contain the expected handlers")
    print("PASS service worker")
    print("Deployment smoke checks passed")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        raise SystemExit(1) from error

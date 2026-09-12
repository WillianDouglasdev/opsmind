import os
import re
from collections.abc import Mapping, Sequence
from urllib.parse import urlsplit


VERCEL_HOST_VARIABLES = (
    "VERCEL_URL",
    "VERCEL_PROJECT_PRODUCTION_URL",
    "VERCEL_BRANCH_URL",
)

HOSTNAME_PATTERN = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)


def unique_values(values: Sequence[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def normalize_vercel_host(value: str | None) -> str | None:
    candidate = (value or "").strip()
    if not candidate:
        return None

    parsed = urlsplit(candidate if "://" in candidate else f"https://{candidate}")
    try:
        port = parsed.port
    except ValueError:
        return None

    hostname = (parsed.hostname or "").rstrip(".").lower()
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.username
        or parsed.password
        or port is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or not HOSTNAME_PATTERN.fullmatch(hostname)
    ):
        return None
    return hostname


def vercel_hosts(environ: Mapping[str, str] | None = None) -> list[str]:
    source = os.environ if environ is None else environ
    hosts = [normalize_vercel_host(source.get(name)) for name in VERCEL_HOST_VARIABLES]
    return unique_values([host for host in hosts if host])


def build_allowed_hosts(
    manual_hosts: Sequence[str],
    *,
    environ: Mapping[str, str] | None = None,
    include_testserver: bool = False,
) -> list[str]:
    local_hosts = ["127.0.0.1", "localhost"]
    if include_testserver:
        local_hosts.append("testserver")
    return unique_values([*local_hosts, *manual_hosts, *vercel_hosts(environ)])


def build_csrf_trusted_origins(
    manual_origins: Sequence[str],
    *,
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    vercel_origins = [f"https://{host}" for host in vercel_hosts(environ)]
    return unique_values([*manual_origins, *vercel_origins])

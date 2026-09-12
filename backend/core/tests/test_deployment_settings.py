from config.environment import build_allowed_hosts, build_csrf_trusted_origins


def test_local_development_hosts_are_always_available() -> None:
    hosts = build_allowed_hosts([], environ={})

    assert "localhost" in hosts
    assert "127.0.0.1" in hosts


def test_vercel_deployment_host_is_allowed() -> None:
    hosts = build_allowed_hosts(
        [],
        environ={"VERCEL_URL": "opsmind-abc123.vercel.app"},
    )

    assert "opsmind-abc123.vercel.app" in hosts


def test_vercel_production_and_branch_hosts_are_allowed_without_duplicates() -> None:
    environ = {
        "VERCEL_PROJECT_PRODUCTION_URL": "opsmind.vercel.app",
        "VERCEL_BRANCH_URL": "opsmind-git-main.vercel.app",
        "VERCEL_URL": "opsmind.vercel.app",
    }
    hosts = build_allowed_hosts([], environ=environ)
    origins = build_csrf_trusted_origins([], environ=environ)

    assert hosts.count("opsmind.vercel.app") == 1
    assert "opsmind-git-main.vercel.app" in hosts
    assert origins == [
        "https://opsmind.vercel.app",
        "https://opsmind-git-main.vercel.app",
    ]


def test_manual_hosts_and_origins_remain_available() -> None:
    hosts = build_allowed_hosts(
        ["api.opsmind.example"],
        environ={"VERCEL_PROJECT_PRODUCTION_URL": "opsmind.vercel.app"},
    )
    origins = build_csrf_trusted_origins(
        ["https://app.opsmind.example"],
        environ={"VERCEL_PROJECT_PRODUCTION_URL": "opsmind.vercel.app"},
    )

    assert "api.opsmind.example" in hosts
    assert "opsmind.vercel.app" in hosts
    assert "https://app.opsmind.example" in origins
    assert "https://opsmind.vercel.app" in origins


def test_unrelated_or_malformed_environment_values_are_ignored() -> None:
    environ = {
        "DATABASE_URL": "valor-ficticio-que-nao-deve-ser-usado",
        "DJANGO_SECRET_KEY": "valor-ficticio-que-nao-deve-ser-usado",
        "VERCEL_URL": "https://usuario@opsmind.vercel.app/caminho",
    }

    assert build_allowed_hosts([], environ=environ) == ["127.0.0.1", "localhost"]
    assert build_csrf_trusted_origins([], environ=environ) == []

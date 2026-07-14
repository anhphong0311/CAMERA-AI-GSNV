"""Validate production deployment artifacts (Sprint 11)."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def test_production_compose_exists_and_valid():
    compose_path = ROOT / "docker-compose.production.yml"
    assert compose_path.exists()
    data = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    services = data.get("services", {})
    required = {"postgres", "redis", "backend", "ai-worker", "frontend", "nginx", "prometheus", "grafana", "watchdog"}
    assert required.issubset(services.keys())


def test_production_dockerfiles_exist():
    assert (ROOT / "backend" / "Dockerfile.production").exists()
    assert (ROOT / "frontend" / "Dockerfile.production").exists()


def test_nginx_production_config_exists():
    assert (ROOT / "deploy" / "docker" / "nginx" / "nginx.production.conf").exists()


def test_env_examples_exist():
    for name in (".env.production.example", ".env.staging.example", ".env.development.example"):
        assert (ROOT / name).exists(), f"Missing {name}"


def test_install_scripts_exist():
    scripts = ROOT / "deploy" / "scripts"
    for name in ("install.sh", "install.ps1", "update.sh", "rollback.sh", "backup.sh", "restore.sh"):
        assert (scripts / name).exists(), f"Missing {name}"

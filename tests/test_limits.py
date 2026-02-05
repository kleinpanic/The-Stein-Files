import os

from scripts.ingest import load_config, select_limits


def test_no_cap_by_default(monkeypatch):
    monkeypatch.delenv("EPPIE_MAX_DOWNLOADS_PER_SOURCE", raising=False)
    monkeypatch.delenv("EPPIE_MAX_BYTES_PER_RUN", raising=False)
    monkeypatch.setenv("CI", "false")
    limits = select_limits(load_config())
    assert limits["max_docs"] == 0
    assert limits["max_bytes"] == 0


def test_env_cap_overrides(monkeypatch):
    monkeypatch.setenv("EPPIE_MAX_DOWNLOADS_PER_SOURCE", "5")
    monkeypatch.setenv("EPPIE_MAX_BYTES_PER_RUN", "1000")
    limits = select_limits(load_config())
    assert limits["max_docs"] == 5
    assert limits["max_bytes_run"] == 1000

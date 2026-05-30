# ABOUTME: Tests that startup loads credentials from a local .env file.
# ABOUTME: Verifies .env fills missing vars, real env wins, and missing vars raise SystemExit.
import os

import pytest

from avocet.app import _load_environment


def _write_env(path, **values):
    path.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n")


def test_load_environment_reads_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv("RAINDROP", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _write_env(tmp_path / ".env", RAINDROP="token-from-dotenv", ANTHROPIC_API_KEY="key-from-dotenv")
    monkeypatch.chdir(tmp_path)

    _load_environment()

    assert os.environ["RAINDROP"] == "token-from-dotenv"
    assert os.environ["ANTHROPIC_API_KEY"] == "key-from-dotenv"


def test_real_env_var_takes_precedence_over_dotenv(tmp_path, monkeypatch):
    monkeypatch.setenv("RAINDROP", "real-token")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "real-key")
    _write_env(tmp_path / ".env", RAINDROP="token-from-dotenv", ANTHROPIC_API_KEY="key-from-dotenv")
    monkeypatch.chdir(tmp_path)

    _load_environment()

    # The exported environment must win over the .env file (override=False).
    assert os.environ["RAINDROP"] == "real-token"
    assert os.environ["ANTHROPIC_API_KEY"] == "real-key"


def test_missing_required_var_raises_system_exit(tmp_path, monkeypatch):
    monkeypatch.delenv("RAINDROP", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)  # no .env present

    with pytest.raises(SystemExit):
        _load_environment()


@pytest.fixture(autouse=True)
def _isolate_provider_env(monkeypatch):
    # Keep provider selection deterministic regardless of the caller's shell.
    for var in ("AVOCET_SUMMARY_PROVIDER", "AVOCET_SUMMARY_MODEL", "OPENAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)


def test_openai_key_alone_satisfies_startup(tmp_path, monkeypatch):
    monkeypatch.delenv("RAINDROP", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _write_env(tmp_path / ".env", RAINDROP="r", OPENAI_API_KEY="o")
    monkeypatch.chdir(tmp_path)

    _load_environment()  # auto-detects openai, its key is present -> no error

    assert os.environ["OPENAI_API_KEY"] == "o"


def test_explicit_openai_without_its_key_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _write_env(tmp_path / ".env", RAINDROP="r", AVOCET_SUMMARY_PROVIDER="openai")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
        _load_environment()


def test_unknown_provider_raises_system_exit(tmp_path, monkeypatch):
    _write_env(tmp_path / ".env", RAINDROP="r", AVOCET_SUMMARY_PROVIDER="grok")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit):
        _load_environment()

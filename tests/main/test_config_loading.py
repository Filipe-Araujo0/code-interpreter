from pathlib import Path

from app.shared.config import get_settings


def test_settings_precedence_and_toml_loading(monkeypatch, tmp_path: Path):
    repo_root = tmp_path / "repo"
    config_dir = repo_root / "config"
    repo_root.mkdir()
    config_dir.mkdir()

    (repo_root / "settings.toml").write_text(
        """
[api]
port = 8100

[logging]
level = "WARNING"

[files]
allowed_extensions = ["csv", "xlsx"]
""".strip(),
        encoding="utf-8",
    )
    (repo_root / "settings.local.toml").write_text(
        """
[api]
port = 8200
""".strip(),
        encoding="utf-8",
    )
    (repo_root / ".env").write_text(
        "PORT=8300\nLOG_LEVEL=DEBUG\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("HOST_PATH", str(repo_root))
    monkeypatch.setenv("HOST_CONFIG_PATH", "config")
    monkeypatch.setenv("PORT", "8400")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.PORT == 8400, "Process env must override .env and TOML values."
    assert settings.LOG_LEVEL == "DEBUG", ".env must override TOML defaults."
    assert settings.FILE_ALLOWED_EXTENSIONS == {"csv", "xlsx"}, "TOML lists must be coerced into the declared set."
    assert settings.CONFIG_PATH == config_dir, "HOST_CONFIG_PATH must still control mutable runtime data."
    get_settings.cache_clear()


def test_settings_support_legacy_top_level_toml_keys(monkeypatch, tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (repo_root / "settings.toml").write_text(
        'FILE_MAX_UPLOAD_SIZE = 1234\n',
        encoding="utf-8",
    )

    monkeypatch.setenv("HOST_PATH", str(repo_root))

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.FILE_MAX_UPLOAD_SIZE == 1234, "Top-level TOML keys matching settings names must remain valid."
    get_settings.cache_clear()

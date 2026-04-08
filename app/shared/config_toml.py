from pathlib import Path
from typing import Any
import tomllib

from loguru import logger

SETTINGS_TOML_FILENAMES = ("settings.toml", "settings.local.toml")

SECTION_FIELD_MAP: dict[tuple[str, str], str] = {
    ("api", "port"): "PORT",
    ("api", "prefix"): "API_PREFIX",
    ("sandbox", "max_execution_time"): "SANDBOX_MAX_EXECUTION_TIME",
    ("files", "max_upload_size"): "FILE_MAX_UPLOAD_SIZE",
    ("files", "allowed_extensions"): "FILE_ALLOWED_EXTENSIONS",
    ("paths", "host_path"): "HOST_PATH",
    ("paths", "host_config_path"): "HOST_CONFIG_PATH",
    ("paths", "host_file_upload_path"): "HOST_FILE_UPLOAD_PATH",
    ("cleanup", "run_interval"): "CLEANUP_RUN_INTERVAL",
    ("cleanup", "file_max_age"): "CLEANUP_FILE_MAX_AGE",
    ("logging", "level"): "LOG_LEVEL",
    ("logging", "serialize"): "LOG_SERIALIZE",
    ("containers", "py_image"): "PY_CONTAINER_IMAGE",
    ("containers", "r_image"): "R_CONTAINER_IMAGE",
    ("docker", "max_concurrent_containers"): "MAX_CONCURRENT_CONTAINERS",
    ("docker", "memory_limit_mb"): "CONTAINER_MEMORY_LIMIT_MB",
    ("docker", "cpu_limit"): "CONTAINER_CPU_LIMIT",
    ("docker", "network_enabled"): "DOCKER_NETWORK_ENABLED",
}


def load_settings_toml(project_root: Path, valid_fields: set[str]) -> dict[str, Any]:
    """Load baseline and local TOML config files from the project root."""
    values: dict[str, Any] = {}
    for filename in SETTINGS_TOML_FILENAMES:
        path = project_root / filename
        if not path.exists():
            continue
        values.update(_load_single_settings_toml(path, valid_fields))
    return values


def _load_single_settings_toml(path: Path, valid_fields: set[str]) -> dict[str, Any]:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    values: dict[str, Any] = {}

    for key, value in raw.items():
        if isinstance(value, dict):
            section = key.lower()
            for nested_key, nested_value in value.items():
                field_name = SECTION_FIELD_MAP.get((section, nested_key.lower()))
                if field_name and field_name in valid_fields:
                    values[field_name] = nested_value
            continue

        field_name = key.upper()
        if field_name in valid_fields:
            values[field_name] = value

    logger.debug(f"Loaded TOML settings from {path}")
    return values

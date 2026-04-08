import os
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
from typing import Dict, Set
from dotenv import dotenv_values

from .config_toml import load_settings_toml


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(case_sensitive=True, env_file=None, extra="ignore", env_prefix="")

    # Configuration
    HOST_PATH: Path = (
        "."  # This is used to fully qualify relative paths for Docker code execution container volume mounts
    )
    HOST_CONFIG_PATH: Path = Path("config")  # Base directory for configuration files
    LOG_LEVEL: str = "INFO"  # Log level for logging
    LOG_SERIALIZE: bool = False  # Whether to serialize log messages to JSON

    @property
    def CONFIG_PATH_ABS(self) -> Path:
        """Full path to the configuration directory."""
        return self.HOST_CONFIG_PATH if self.HOST_CONFIG_PATH.is_absolute() else self.HOST_PATH / self.HOST_CONFIG_PATH

    @property
    def CONFIG_PATH(self) -> Path:
        """Compatibility alias for code that expects an absolute config path."""
        return self.CONFIG_PATH_ABS

    # API settings
    PORT: int = 8000  # Port exposed from the container
    API_PREFIX: str = "/v1"  # API prefix

    # Code execution sandbox settings
    SANDBOX_MAX_EXECUTION_TIME: int = 300  # Docker container execution time limit in seconds

    # File management
    FILE_MAX_UPLOAD_SIZE: int = 32 * 1024 * 1024  # 32MiB
    FILE_ALLOWED_EXTENSIONS: Set[str] = {
        # Programming languages
        "py",
        "c",
        "cpp",
        "java",
        "php",
        "rb",
        "js",
        "ts",
        # Documents
        "txt",
        "md",
        "html",
        "css",
        "tex",
        "json",
        "csv",
        "xml",
        "docx",
        "xlsx",
        "pptx",
        "pdf",
        # Data formats
        "ipynb",
        "yml",
        "yaml",
        # Archives
        "zip",
        "tar",
        # Images
        "jpg",
        "jpeg",
        "png",
        "gif",
        # CAD / drawings
        "dwg",
    }

    HOST_FILE_UPLOAD_PATH: Path = Path("uploads")  # Base directory for uploaded files

    @property
    def HOST_FILE_UPLOAD_PATH_ABS(self) -> Path:
        """Full path to the file upload directory. Absolute path is required for Docker volume mounts."""
        return (
            self.HOST_FILE_UPLOAD_PATH
            if self.HOST_FILE_UPLOAD_PATH.is_absolute()
            else self.HOST_PATH / self.HOST_FILE_UPLOAD_PATH
        )

    @property
    def UPLOAD_PATH(self) -> Path:
        """Compatibility alias for code that expects an absolute upload path."""
        return self.HOST_FILE_UPLOAD_PATH_ABS

    # File cleanup settings
    CLEANUP_RUN_INTERVAL: int = 3600  # How often to run the cleanup in seconds
    CLEANUP_FILE_MAX_AGE: int = 86400  # How old files can be before they are deleted in seconds

    PY_CONTAINER_IMAGE: str = "code-interpreter-py:latest"
    R_CONTAINER_IMAGE: str = "jupyter/r-notebook:latest"

    @property
    def LANGUAGE_CONTAINERS(self) -> Dict[str, str]:
        """Map language codes to container images."""
        return {
            "py": self.PY_CONTAINER_IMAGE,
            "r": self.R_CONTAINER_IMAGE,
        }

    # Docker execution settings
    MAX_CONCURRENT_CONTAINERS: int = 10  # Maximum number of concurrent Docker containers
    CONTAINER_MEMORY_LIMIT_MB: int = 512  # Memory limit for Docker containers in MB
    CONTAINER_CPU_LIMIT: float = 1.0  # CPU limit for Docker containers (number of cores)

    # Docker network settings
    DOCKER_NETWORK_ENABLED: bool = False  # Whether Docker containers have network access


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    bootstrap_dotenv = dotenv_values(Path.cwd() / ".env")
    bootstrap_host_path = Path(
        os.environ.get("HOST_PATH") or bootstrap_dotenv.get("HOST_PATH") or "."
    )
    valid_fields = set(Settings.model_fields)
    env_file_path = Path.cwd() / ".env"
    merged_values = load_settings_toml(bootstrap_host_path, valid_fields)
    merged_values.update(
        {
            key: value
            for key, value in dotenv_values(env_file_path).items()
            if key in valid_fields and value is not None
        }
    )
    merged_values.update(
        {
            key: value
            for key, value in os.environ.items()
            if key in valid_fields
        }
    )

    settings = Settings(**merged_values)
    logger.info(f"Settings: {settings.HOST_FILE_UPLOAD_PATH_ABS}")
    return settings

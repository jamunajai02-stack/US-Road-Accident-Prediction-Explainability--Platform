"""Typed configuration loader merging YAML files with environment variable overrides."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from libs.common.exceptions import ConfigurationError


class ConfigLoader:
    """Utility for loading and caching hierarchical YAML configuration files."""

    _cached_configs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def load(cls, config_name: str, configs_dir: Optional[str] = None) -> Dict[str, Any]:
        """Load a YAML configuration file by name (e.g., 'base', 'model', 'thresholds')."""
        if config_name in cls._cached_configs:
            return cls._cached_configs[config_name]

        base_dir = Path(configs_dir) if configs_dir else Path(__file__).parent.parent.parent / "configs"
        config_file = base_dir / f"{config_name}.yaml"
        if not config_file.exists():
            config_file = base_dir / f"{config_name}.yml"

        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_file.resolve()}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to parse YAML config at {config_file}: {e}") from e

        # Merge environment overrides (e.g., APP_DEBUG=true -> config['app']['debug'] = True)
        config_data = cls._apply_env_overrides(config_data)
        cls._cached_configs[config_name] = config_data
        return config_data

    @classmethod
    def _apply_env_overrides(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively check for uppercase ENV variables to override nested dictionary keys."""
        # Check standard common env variables
        if "POSTGIS_URL" in os.environ and "database" in config:
            config["database"]["postgis_url"] = os.environ["POSTGIS_URL"]
        if "REDIS_URL" in os.environ and "providers" in config and "cache" in config["providers"]:
            config["providers"]["cache"]["redis_url"] = os.environ["REDIS_URL"]
        if "VALHALLA_URL" in os.environ and "providers" in config and "routing" in config["providers"]:
            config["providers"]["routing"]["base_url"] = os.environ["VALHALLA_URL"]
        return config

    @classmethod
    def clear_cache(cls) -> None:
        """Clear memory cache for testing purposes."""
        cls._cached_configs.clear()

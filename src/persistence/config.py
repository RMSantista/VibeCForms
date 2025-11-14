"""
Configuration management for VibeCForms persistence layer.

This module handles reading and validating persistence configuration
from the persistence.json file, including backend selection based on
form path mappings and wildcard patterns.
"""

import os
import json
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class PersistenceConfig:
    """
    Manages persistence configuration for VibeCForms.

    Reads configuration from src/config/persistence.json and provides
    methods to get backend configuration based on form paths, with
    support for wildcard mappings and environment variable substitution.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to persistence.json file.
                        If None, uses default path: src/config/persistence.json
        """
        if config_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "src" / "config" / "persistence.json"

        self.config_path = Path(config_path)
        # Store business case root (parent of config directory)
        self.business_case_root = self.config_path.parent.parent
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.

        Returns:
            Dictionary with configuration data

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is not valid JSON
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Persistence configuration file not found: {self.config_path}"
            )

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"Loaded persistence configuration from {self.config_path}")
            return config
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in persistence configuration: {e.msg}", e.doc, e.pos
            )

    def _validate_config(self) -> None:
        """
        Validate configuration structure and required fields.

        Raises:
            ValueError: If configuration is invalid
        """
        # Check required top-level keys
        required_keys = ["version", "default_backend", "backends"]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(
                    f"Missing required key '{key}' in persistence configuration"
                )

        # Validate default_backend exists in backends
        default_backend = self.config["default_backend"]
        backends = self.config["backends"]

        if default_backend not in backends:
            raise ValueError(
                f"Default backend '{default_backend}' not defined in backends"
            )

        # Validate each backend has a 'type' field
        for backend_name, backend_config in backends.items():
            if "type" not in backend_config:
                raise ValueError(
                    f"Backend '{backend_name}' missing required 'type' field"
                )

        logger.info("Persistence configuration validation passed")

    def get_backend_for_form(self, form_path: str) -> str:
        """
        Get the backend name configured for a specific form.

        Supports wildcard patterns like "financeiro/*" matching "financeiro/contas".

        Args:
            form_path: Path to the form (e.g., 'contatos', 'financeiro/contas')

        Returns:
            Backend name (e.g., 'txt', 'sqlite', 'mysql')

        Example:
            >>> config.get_backend_for_form('contatos')
            'txt'
            >>> config.get_backend_for_form('financeiro/contas')
            'mysql'  # if 'financeiro/*' is mapped to mysql
        """
        form_mappings = self.config.get("form_mappings", {})

        # First: Try exact match
        if form_path in form_mappings:
            backend = form_mappings[form_path]
            # If backend is "default_backend", use the actual default
            if backend == "default_backend":
                backend = self.config["default_backend"]
            logger.debug(
                f"Form '{form_path}' mapped to backend '{backend}' (exact match)"
            )
            return backend

        # Second: Try wildcard patterns
        for pattern, backend in form_mappings.items():
            if "*" in pattern:
                # Convert glob pattern to regex
                # 'financeiro/*' becomes '^financeiro/.*$'
                regex_pattern = (
                    "^" + pattern.replace("/", r"\/").replace("*", ".*") + "$"
                )
                if re.match(regex_pattern, form_path):
                    # If backend is "default_backend", use the actual default
                    if backend == "default_backend":
                        backend = self.config["default_backend"]
                    logger.debug(
                        f"Form '{form_path}' matched pattern '{pattern}', "
                        f"using backend '{backend}'"
                    )
                    return backend

        # Third: Use default backend
        default_backend = self.config["default_backend"]
        logger.debug(f"Form '{form_path}' using default backend '{default_backend}'")
        return default_backend

    def get_backend_config(self, form_path: str) -> Dict[str, Any]:
        """
        Get the full backend configuration for a form.

        Args:
            form_path: Path to the form

        Returns:
            Dictionary with backend configuration, with environment
            variables substituted and relative paths resolved

        Example:
            >>> config.get_backend_config('usuarios')
            {
                'type': 'sqlite',
                'database': '/absolute/path/to/business/case/data/vibecforms.db',
                'timeout': 10
            }
        """
        backend_name = self.get_backend_for_form(form_path)
        backend_config = self.config["backends"][backend_name].copy()

        # Substitute environment variables
        backend_config = self._substitute_env_vars(backend_config)

        # Resolve relative paths to absolute paths
        backend_config = self._resolve_paths(backend_config)

        return backend_config

    def _substitute_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively substitute environment variables in configuration.

        Replaces strings like "${VAR_NAME}" with the value of the
        environment variable VAR_NAME.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with environment variables substituted

        Example:
            {"password": "${DB_PASSWORD}"} -> {"password": "secret123"}
        """
        result = {}
        for key, value in config.items():
            if isinstance(value, str):
                # Replace ${VAR_NAME} with environment variable value
                result[key] = self._expand_env_var(value)
            elif isinstance(value, dict):
                # Recursively process nested dicts
                result[key] = self._substitute_env_vars(value)
            else:
                result[key] = value
        return result

    def _expand_env_var(self, value: str) -> str:
        """
        Expand a single environment variable in a string.

        Args:
            value: String that may contain ${VAR_NAME}

        Returns:
            String with environment variables expanded

        Example:
            "${HOME}/data" -> "/home/user/data"
            "mysql://${DB_HOST}:3306" -> "mysql://localhost:3306"
        """
        # Pattern to match ${VAR_NAME}
        pattern = r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}"

        def replace_var(match):
            var_name = match.group(1)
            var_value = os.environ.get(var_name, "")
            if not var_value:
                logger.warning(
                    f"Environment variable '{var_name}' not set, using empty string"
                )
            return var_value

        return re.sub(pattern, replace_var, value)

    def _resolve_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve relative paths in configuration to absolute paths.

        Paths that are relative (not starting with /) are resolved relative
        to the business case root directory.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with paths resolved to absolute paths

        Example:
            {"path": "data/"} -> {"path": "/absolute/path/to/business/case/data/"}
            {"database": "data/db.sqlite"} -> {"database": "/absolute/path/to/business/case/data/db.sqlite"}
        """
        # Keys that typically contain file/directory paths
        path_keys = ["path", "database", "backup_path"]

        result = {}
        for key, value in config.items():
            if key in path_keys and isinstance(value, str):
                # Convert relative paths to absolute
                if not os.path.isabs(value):
                    value = str(self.business_case_root / value)
            result[key] = value
        return result

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a top-level configuration setting.

        Args:
            key: Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default

        Example:
            >>> config.get_setting('auto_create_storage', True)
            True
        """
        return self.config.get(key, default)

    @property
    def form_mappings(self) -> Dict[str, str]:
        """
        Get the form_mappings dictionary from configuration.

        Returns:
            Dictionary mapping form paths to backend names

        Example:
            >>> config.form_mappings['contatos']
            'sqlite'
        """
        return self.config.get("form_mappings", {})

    @property
    def backends(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the backends dictionary from configuration.

        Returns:
            Dictionary of backend configurations

        Example:
            >>> config.backends['sqlite']
            {'type': 'sqlite', 'database': 'src/vibecforms.db', ...}
        """
        return self.config.get("backends", {})

    def save(self) -> None:
        """
        Save configuration back to the JSON file.

        Useful when form_mappings or other settings are modified at runtime.
        """
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        logger.info(f"Persistence configuration saved to {self.config_path}")

    def reload(self) -> None:
        """
        Reload configuration from file.

        Useful if configuration file was modified at runtime.
        """
        self.config = self._load_config()
        self._validate_config()
        logger.info("Persistence configuration reloaded")

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"PersistenceConfig(path={self.config_path}, "
            f"default_backend={self.config.get('default_backend')}, "
            f"backends={list(self.config.get('backends', {}).keys())})"
        )


# Global configuration instance (singleton)
_config_instance: Optional[PersistenceConfig] = None


def get_config(config_path: Optional[str] = None) -> PersistenceConfig:
    """
    Get the global persistence configuration instance.

    This implements a singleton pattern to ensure only one configuration
    instance exists throughout the application lifecycle.

    Args:
        config_path: Path to configuration file (only used on first call)

    Returns:
        PersistenceConfig instance

    Example:
        >>> config = get_config()
        >>> backend = config.get_backend_for_form('contatos')
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = PersistenceConfig(config_path)

    return _config_instance


def reset_config() -> None:
    """
    Reset the global configuration instance.

    Useful for testing to force configuration reload.
    """
    global _config_instance
    _config_instance = None

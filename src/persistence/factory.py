"""
Factory for creating persistence repository instances.

This module implements the Factory pattern to create the appropriate
repository adapter based on configuration and form path.
"""

import logging
from typing import Dict, Optional
from persistence.base import BaseRepository
from persistence.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Cache of repository instances (singleton per backend type)
_repository_cache: Dict[str, BaseRepository] = {}


class RepositoryFactory:
    """
    Factory class for creating persistence repository instances.

    Uses the configured persistence settings to determine which
    adapter to use for each form, and maintains a cache of instances
    to avoid recreating connections.
    """

    @staticmethod
    def get_repository(form_path: str) -> BaseRepository:
        """
        Get the appropriate repository instance for a form.

        Determines which backend to use based on configuration,
        creates the adapter instance (or returns cached instance),
        and returns it.

        Args:
            form_path: Path to the form (e.g., 'contatos', 'financeiro/contas')

        Returns:
            BaseRepository instance for the configured backend

        Raises:
            ValueError: If backend type is not supported
            ImportError: If adapter module cannot be imported

        Example:
            >>> repo = RepositoryFactory.get_repository('contatos')
            >>> forms = repo.read_all('contatos', spec)
        """
        # Get configuration
        config = get_config()
        backend_config = config.get_backend_config(form_path)
        backend_type = backend_config["type"]

        # Check cache first
        if backend_type in _repository_cache:
            logger.debug(f"Using cached repository for backend '{backend_type}'")
            return _repository_cache[backend_type]

        # Create new repository instance
        repository = RepositoryFactory._create_repository(backend_type, backend_config)

        # Cache it
        _repository_cache[backend_type] = repository

        logger.info(
            f"Created and cached repository for backend '{backend_type}' "
            f"(form: {form_path})"
        )

        return repository

    @staticmethod
    def _create_repository(backend_type: str, backend_config: Dict) -> BaseRepository:
        """
        Create a repository instance for the given backend type.

        Args:
            backend_type: Type of backend ('txt', 'sqlite', 'mysql', etc.)
            backend_config: Configuration dictionary for the backend

        Returns:
            BaseRepository instance

        Raises:
            ValueError: If backend type is not supported
            ImportError: If adapter module cannot be imported
        """
        # Map backend types to adapter classes
        adapter_map = {
            "txt": ("persistence.adapters.txt_adapter", "TxtRepository"),
            "sqlite": ("persistence.adapters.sqlite_adapter", "SQLiteRepository"),
            "mysql": ("persistence.adapters.mysql_adapter", "MySQLRepository"),
            "postgres": ("persistence.adapters.postgres_adapter", "PostgresRepository"),
            "mongodb": ("persistence.adapters.mongodb_adapter", "MongoDBRepository"),
            "redis": ("persistence.adapters.redis_adapter", "RedisRepository"),
            "csv": ("persistence.adapters.csv_adapter", "CSVRepository"),
            "json": ("persistence.adapters.json_adapter", "JSONRepository"),
            "xml": ("persistence.adapters.xml_adapter", "XMLRepository"),
        }

        if backend_type not in adapter_map:
            raise ValueError(
                f"Unsupported backend type: '{backend_type}'. "
                f"Supported types: {list(adapter_map.keys())}"
            )

        module_name, class_name = adapter_map[backend_type]

        try:
            # Dynamic import of adapter module
            module = __import__(module_name, fromlist=[class_name])
            adapter_class = getattr(module, class_name)

            # Instantiate adapter with its configuration
            repository = adapter_class(backend_config)

            logger.debug(f"Created {class_name} instance with config: {backend_config}")

            return repository

        except ImportError as e:
            raise ImportError(
                f"Failed to import adapter '{class_name}' from '{module_name}': {e}"
            )
        except AttributeError as e:
            raise ImportError(
                f"Adapter class '{class_name}' not found in module '{module_name}': {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to create repository instance for backend '{backend_type}': {e}"
            )

    @staticmethod
    def get_repository_by_type(backend_type: str) -> BaseRepository:
        """
        Get a repository instance directly by backend type.

        Useful for data migration or testing. Bypasses form_path mapping
        and uses default configuration for the backend.

        Args:
            backend_type: Type of backend ('txt', 'sqlite', etc.)

        Returns:
            BaseRepository instance

        Example:
            >>> txt_repo = RepositoryFactory.get_repository_by_type('txt')
            >>> sqlite_repo = RepositoryFactory.get_repository_by_type('sqlite')
        """
        # Check cache first
        if backend_type in _repository_cache:
            return _repository_cache[backend_type]

        # Get backend configuration
        config = get_config()
        backends = config.config.get("backends", {})

        if backend_type not in backends:
            raise ValueError(
                f"Backend type '{backend_type}' not defined in configuration"
            )

        backend_config = backends[backend_type].copy()

        # Substitute environment variables
        backend_config = config._substitute_env_vars(backend_config)

        # Create and cache repository
        repository = RepositoryFactory._create_repository(backend_type, backend_config)
        _repository_cache[backend_type] = repository

        return repository

    @staticmethod
    def clear_cache() -> None:
        """
        Clear the repository cache.

        Useful for testing or when configuration changes at runtime.
        Forces creation of new repository instances on next access.
        """
        global _repository_cache
        _repository_cache = {}
        logger.info("Repository cache cleared")

    @staticmethod
    def get_cached_backends() -> list:
        """
        Get list of currently cached backend types.

        Returns:
            List of backend type names currently in cache

        Example:
            >>> RepositoryFactory.get_cached_backends()
            ['txt', 'sqlite']
        """
        return list(_repository_cache.keys())

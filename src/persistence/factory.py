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

    @staticmethod
    def create_relationship_repository(form_path: str):
        """
        Create a RelationshipRepository instance for managing relationships.

        FASE 3.1: Factory Pattern Integration

        This method creates a RelationshipRepository with appropriate configuration:
        - Reads sync_strategy from persistence.json
        - Reads cardinality_rules from persistence.json
        - Uses the same connection as the form's repository

        Args:
            form_path: Path to the form (e.g., 'pedidos', 'contatos')

        Returns:
            RelationshipRepository instance configured for the form

        Example:
            >>> rel_repo = RepositoryFactory.create_relationship_repository('pedidos')
            >>> rel_repo.create_relationship(...)
        """
        from persistence.relationship_repository import RelationshipRepository
        from persistence.contracts.relationship_interface import (
            SyncStrategy,
            CardinalityType,
        )

        # Get main repository to access its connection
        repo = RepositoryFactory.get_repository(form_path)

        # Check if repository supports relationships
        if not hasattr(repo, "get_relationship_repository"):
            logger.warning(
                f"Repository for '{form_path}' does not support relationships "
                f"(backend does not implement get_relationship_repository)"
            )
            return None

        # Get relationship repository from base repository
        # This ensures connection is initialized properly
        rel_repo = repo.get_relationship_repository()

        if rel_repo is None:
            logger.warning(
                f"Failed to create relationship repository for '{form_path}'"
            )
            return None

        # Update sync strategy and cardinality rules from config
        sync_strategy = RepositoryFactory.get_sync_strategy(form_path)
        cardinality_rules = RepositoryFactory.get_cardinality_rules()

        rel_repo.sync_strategy = sync_strategy
        rel_repo.cardinality_rules = cardinality_rules

        logger.info(
            f"Created RelationshipRepository for '{form_path}' "
            f"with sync_strategy={sync_strategy.name}"
        )

        return rel_repo

    @staticmethod
    def get_sync_strategy(form_path: str):
        """
        Get the sync strategy for a specific form's relationships.

        Reads from persistence.json:
        - relationships.sync_strategy_mappings.<form>.<field>
        - relationships.default_sync_strategy

        Args:
            form_path: Path to the form (e.g., 'pedidos')

        Returns:
            SyncStrategy enum value (EAGER, LAZY, or SCHEDULED)

        Example:
            >>> strategy = RepositoryFactory.get_sync_strategy('pedidos')
            >>> # Returns SyncStrategy.EAGER for most critical forms
        """
        from persistence.contracts.relationship_interface import SyncStrategy

        config = get_config()
        relationships_config = config.config.get("relationships", {})

        # Get default strategy
        default_strategy = relationships_config.get("default_sync_strategy", "eager")

        # Try to map string to enum
        strategy_map = {
            "eager": SyncStrategy.EAGER,
            "lazy": SyncStrategy.LAZY,
            "scheduled": SyncStrategy.SCHEDULED,
        }

        strategy = strategy_map.get(default_strategy.lower(), SyncStrategy.EAGER)

        logger.debug(
            f"Sync strategy for '{form_path}': {strategy.name} "
            f"(default: {default_strategy})"
        )

        return strategy

    @staticmethod
    def get_cardinality_rules() -> Dict:
        """
        Get cardinality rules from configuration.

        Reads from persistence.json:
        - relationships.cardinality_rules

        Returns:
            Dictionary mapping relationship names to CardinalityType
            Example: {"pedidos.cliente": CardinalityType.ONE_TO_ONE}

        Example:
            >>> rules = RepositoryFactory.get_cardinality_rules()
            >>> rules.get("pedidos.cliente")
            CardinalityType.ONE_TO_ONE
        """
        from persistence.contracts.relationship_interface import CardinalityType

        config = get_config()
        relationships_config = config.config.get("relationships", {})
        cardinality_config = relationships_config.get("cardinality_rules", {})

        # Map string values to CardinalityType enum
        cardinality_map = {
            "one_to_one": CardinalityType.ONE_TO_ONE,
            "one_to_many": CardinalityType.ONE_TO_MANY,
            "many_to_many": CardinalityType.MANY_TO_MANY,
        }

        # Convert strings to enums
        cardinality_rules = {}
        for key, value in cardinality_config.items():
            cardinality_rules[key] = cardinality_map.get(
                value.lower(), CardinalityType.ONE_TO_MANY  # Default
            )

        logger.debug(f"Loaded {len(cardinality_rules)} cardinality rules from config")

        return cardinality_rules

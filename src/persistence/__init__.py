"""
VibeCForms Persistence Layer

This package provides a pluggable persistence system that allows
VibeCForms to work with multiple storage backends (TXT, SQLite,
MySQL, PostgreSQL, MongoDB, CSV, JSON, XML, etc.) without changing
application code.

Main components:
- BaseRepository: Abstract interface all adapters must implement
- RepositoryFactory: Creates appropriate repository instances
- PersistenceConfig: Manages configuration from persistence.json

Usage:
    from persistence.factory import RepositoryFactory

    # Get repository for a form (automatically selects backend)
    repo = RepositoryFactory.get_repository('contatos')

    # Use repository
    forms = repo.read_all('contatos', spec)
    repo.create('contatos', spec, new_data)
"""

from persistence.base import BaseRepository
from persistence.config import PersistenceConfig, get_config, reset_config
from persistence.factory import RepositoryFactory

__all__ = [
    "BaseRepository",
    "PersistenceConfig",
    "get_config",
    "reset_config",
    "RepositoryFactory",
]

__version__ = "3.0.0"

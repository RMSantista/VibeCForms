"""
Persistence adapters for VibeCForms.

This package contains implementations of BaseRepository for various
storage backends.

Available adapters:
- TxtRepository: Semicolon-delimited text files (original format)
- SQLiteRepository: SQLite database (local, zero-config)
- MySQLRepository: MySQL/MariaDB (remote, high performance)
- PostgresRepository: PostgreSQL (remote, advanced features)
- MongoDBRepository: MongoDB (NoSQL document store)
- RedisRepository: Redis (cache and sessions)
- CSVRepository: CSV files (spreadsheets, import/export)
- JSONRepository: JSON files (structured, readable)
- XMLRepository: XML files (structured with schema)

Each adapter implements the BaseRepository interface and can be
used interchangeably through the RepositoryFactory.
"""

# Adapters will be imported dynamically by the factory
# to avoid loading dependencies for backends not in use.
# This keeps the application lightweight.

__all__ = []

__version__ = '3.0.0'

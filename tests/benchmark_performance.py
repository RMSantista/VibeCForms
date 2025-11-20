"""
Performance Benchmarks for VibeCForms Persistence System.

This module benchmarks critical operations:
- Bulk create operations (TXT vs SQLite)
- Migration performance (TXT → SQLite)
- Tag operations latency
- Read operations performance

Run with: python tests/benchmark_performance.py
"""

import pytest
import json
import time
import tempfile
import statistics
from pathlib import Path
from typing import List, Dict, Any

# Import from src
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from persistence.factory import RepositoryFactory
from persistence.config import get_config
from persistence.migration_manager import MigrationManager
from services.tag_service import TagService
from utils.crockford import generate_id


class BenchmarkResult:
    """Store and display benchmark results."""

    def __init__(self, name: str):
        self.name = name
        self.timings: List[float] = []

    def add_timing(self, duration: float):
        """Add a timing measurement in seconds."""
        self.timings.append(duration)

    def get_stats(self) -> Dict[str, float]:
        """Get statistical summary of timings."""
        if not self.timings:
            return {}

        return {
            "min": min(self.timings),
            "max": max(self.timings),
            "mean": statistics.mean(self.timings),
            "median": statistics.median(self.timings),
            "stdev": statistics.stdev(self.timings) if len(self.timings) > 1 else 0,
        }

    def print_report(self, record_count: int = None):
        """Print formatted benchmark report."""
        if not self.timings:
            print(f"⚠️  {self.name}: No data")
            return

        stats = self.get_stats()
        print(f"\n📊 {self.name}")
        if record_count:
            print(f"   Records: {record_count}")
        print(f"   Runs: {len(self.timings)}")
        print(f"   Mean: {stats['mean']:.4f}s")
        print(f"   Median: {stats['median']:.4f}s")
        print(f"   Min: {stats['min']:.4f}s")
        print(f"   Max: {stats['max']:.4f}s")
        if stats["stdev"] > 0:
            print(f"   StdDev: {stats['stdev']:.4f}s")

        if record_count and stats["mean"] > 0:
            throughput = record_count / stats["mean"]
            print(f"   Throughput: {throughput:.0f} records/sec")


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory for benchmarking."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create data directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create persistence.json
    persistence_config = {
        "default_backend": "txt",
        "backends": {
            "txt": {"type": "txt", "base_path": str(data_dir), "encoding": "utf-8"},
            "sqlite": {
                "type": "sqlite",
                "database_path": str(tmp_path / "benchmark.db"),
                "timeout": 10,
            },
        },
        "form_mappings": {"benchmark_form": "sqlite", "*": "default_backend"},
    }

    config_file = config_dir / "persistence.json"
    with open(config_file, "w") as f:
        json.dump(persistence_config, f, indent=2)

    # Create schema_history.json
    history_file = config_dir / "schema_history.json"
    with open(history_file, "w") as f:
        json.dump({}, f)

    return config_dir


@pytest.fixture
def benchmark_spec():
    """Sample form specification for benchmarking."""
    return {
        "title": "Benchmark Form",
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email", "required": True},
            {"name": "phone", "label": "Phone", "type": "tel", "required": False},
            {"name": "company", "label": "Company", "type": "text", "required": False},
            {"name": "notes", "label": "Notes", "type": "textarea", "required": False},
        ],
    }


def generate_sample_record(index: int) -> Dict[str, Any]:
    """Generate a sample record for benchmarking."""
    return {
        "name": f"User {index:05d}",
        "email": f"user{index:05d}@example.com",
        "phone": f"+1-555-{index:04d}",
        "company": f"Company {index % 100}",
        "notes": f"This is a test record number {index} with some additional notes.",
    }


class TestBulkCreatePerformance:
    """Benchmark bulk create operations."""

    @pytest.mark.parametrize("record_count", [10, 100, 1000])
    def test_txt_bulk_create(self, temp_config_dir, benchmark_spec, record_count):
        """Benchmark bulk create on TXT backend."""
        import os

        os.environ["VIBECFORMS_CONFIG_DIR"] = str(temp_config_dir)

        # Clear cache
        RepositoryFactory._repository_cache = {}

        # Get TXT repository
        from persistence.adapters.txt_adapter import TxtRepository

        config = get_config()
        txt_config = config.config["backends"]["txt"]
        repo = TxtRepository(txt_config)

        # Create storage
        form_path = f"benchmark_txt_{record_count}"
        if repo.exists(form_path):
            repo.drop_storage(form_path, force=True)
        repo.create_storage(form_path, benchmark_spec)

        # Generate records
        records = [generate_sample_record(i) for i in range(record_count)]

        # Benchmark
        benchmark = BenchmarkResult(f"TXT Bulk Create ({record_count} records)")

        # Run 3 times for statistical significance
        for run in range(3):
            # Clear data
            repo.drop_storage(form_path, force=True)
            repo.create_storage(form_path, benchmark_spec)

            start = time.time()
            result_ids = repo.bulk_create(form_path, benchmark_spec, records)
            duration = time.time() - start

            benchmark.add_timing(duration)

            # Verify
            assert len(result_ids) == record_count
            assert all(id is not None for id in result_ids)

        # Print results
        benchmark.print_report(record_count)

        # Cleanup
        repo.drop_storage(form_path, force=True)
        del os.environ["VIBECFORMS_CONFIG_DIR"]

    @pytest.mark.parametrize("record_count", [10, 100, 1000])
    def test_sqlite_bulk_create(self, temp_config_dir, benchmark_spec, record_count):
        """Benchmark bulk create on SQLite backend."""
        import os

        os.environ["VIBECFORMS_CONFIG_DIR"] = str(temp_config_dir)

        # Clear cache
        RepositoryFactory._repository_cache = {}

        # Get SQLite repository
        from persistence.adapters.sqlite_adapter import SQLiteRepository

        config = get_config()
        sqlite_config = config.config["backends"]["sqlite"]
        repo = SQLiteRepository(sqlite_config)

        # Create storage
        form_path = f"benchmark_sqlite_{record_count}"
        if repo.exists(form_path):
            repo.drop_storage(form_path, force=True)
        repo.create_storage(form_path, benchmark_spec)

        # Generate records
        records = [generate_sample_record(i) for i in range(record_count)]

        # Benchmark
        benchmark = BenchmarkResult(f"SQLite Bulk Create ({record_count} records)")

        # Run 3 times for statistical significance
        for run in range(3):
            # Clear data
            repo.drop_storage(form_path, force=True)
            repo.create_storage(form_path, benchmark_spec)

            start = time.time()
            result_ids = repo.bulk_create(form_path, benchmark_spec, records)
            duration = time.time() - start

            benchmark.add_timing(duration)

            # Verify
            assert len(result_ids) == record_count
            assert all(id is not None for id in result_ids)

        # Print results
        benchmark.print_report(record_count)

        # Cleanup
        repo.drop_storage(form_path, force=True)
        del os.environ["VIBECFORMS_CONFIG_DIR"]


class TestMigrationPerformance:
    """Benchmark migration operations."""

    @pytest.mark.parametrize("record_count", [100, 500])
    def test_txt_to_sqlite_migration(
        self, temp_config_dir, benchmark_spec, record_count
    ):
        """Benchmark TXT → SQLite migration."""
        import os

        os.environ["VIBECFORMS_CONFIG_DIR"] = str(temp_config_dir)

        # Clear cache
        RepositoryFactory._repository_cache = {}

        # Get repositories
        from persistence.adapters.txt_adapter import TxtRepository
        from persistence.adapters.sqlite_adapter import SQLiteRepository

        config = get_config()
        txt_repo = TxtRepository(config.config["backends"]["txt"])
        sqlite_repo = SQLiteRepository(config.config["backends"]["sqlite"])

        form_path = f"migration_benchmark_{record_count}"

        # Benchmark
        benchmark = BenchmarkResult(f"TXT → SQLite Migration ({record_count} records)")

        # Run 3 times
        for run in range(3):
            # Setup: Create TXT data
            if txt_repo.exists(form_path):
                txt_repo.drop_storage(form_path, force=True)
            if sqlite_repo.exists(form_path):
                sqlite_repo.drop_storage(form_path, force=True)

            txt_repo.create_storage(form_path, benchmark_spec)
            records = [generate_sample_record(i) for i in range(record_count)]
            txt_repo.bulk_create(form_path, benchmark_spec, records)

            # Benchmark migration
            start = time.time()
            success = MigrationManager.migrate_backend(
                form_path=form_path,
                spec=benchmark_spec,
                old_backend="txt",
                new_backend="sqlite",
                record_count=record_count,
            )
            duration = time.time() - start

            benchmark.add_timing(duration)

            # Verify
            assert success is True
            migrated_data = sqlite_repo.read_all(form_path, benchmark_spec)
            assert len(migrated_data) == record_count

        # Print results
        benchmark.print_report(record_count)

        # Cleanup
        if txt_repo.exists(form_path):
            txt_repo.drop_storage(form_path, force=True)
        if sqlite_repo.exists(form_path):
            sqlite_repo.drop_storage(form_path, force=True)

        del os.environ["VIBECFORMS_CONFIG_DIR"]


class TestTagOperationsPerformance:
    """Benchmark tag operations."""

    def test_tag_operations_latency(self, temp_config_dir, benchmark_spec):
        """Benchmark individual tag operations."""
        import os

        os.environ["VIBECFORMS_CONFIG_DIR"] = str(temp_config_dir)

        # Clear cache
        RepositoryFactory._repository_cache = {}

        # Setup
        repo = RepositoryFactory.get_repository("benchmark_form")
        if repo.exists("benchmark_form"):
            repo.drop_storage("benchmark_form", force=True)
        repo.create_storage("benchmark_form", benchmark_spec)

        # Create test records
        record_ids = []
        for i in range(100):
            record_data = generate_sample_record(i)
            record_id = repo.create("benchmark_form", benchmark_spec, record_data)
            record_ids.append(record_id)

        tag_service = TagService()

        # Benchmark: add_tag
        add_benchmark = BenchmarkResult("Tag Add Operation")
        for record_id in record_ids[:50]:
            start = time.time()
            tag_service.add_tag("benchmark_form", record_id, "test_tag", "benchmark")
            duration = time.time() - start
            add_benchmark.add_timing(duration)

        add_benchmark.print_report()

        # Benchmark: has_tag
        check_benchmark = BenchmarkResult("Tag Check Operation")
        for record_id in record_ids[:50]:
            start = time.time()
            tag_service.has_tag("benchmark_form", record_id, "test_tag")
            duration = time.time() - start
            check_benchmark.add_timing(duration)

        check_benchmark.print_report()

        # Benchmark: get_objects_with_tag
        query_benchmark = BenchmarkResult("Tag Query Operation")
        for _ in range(10):
            start = time.time()
            tag_service.get_objects_with_tag("benchmark_form", "test_tag")
            duration = time.time() - start
            query_benchmark.add_timing(duration)

        query_benchmark.print_report()

        # Benchmark: remove_tag
        remove_benchmark = BenchmarkResult("Tag Remove Operation")
        for record_id in record_ids[:50]:
            start = time.time()
            tag_service.remove_tag("benchmark_form", record_id, "test_tag", "benchmark")
            duration = time.time() - start
            remove_benchmark.add_timing(duration)

        remove_benchmark.print_report()

        # Cleanup
        repo.drop_storage("benchmark_form", force=True)
        del os.environ["VIBECFORMS_CONFIG_DIR"]


class TestReadPerformance:
    """Benchmark read operations."""

    @pytest.mark.parametrize("record_count", [100, 1000])
    def test_read_all_performance(self, temp_config_dir, benchmark_spec, record_count):
        """Benchmark read_all operation on SQLite."""
        import os

        os.environ["VIBECFORMS_CONFIG_DIR"] = str(temp_config_dir)

        # Clear cache
        RepositoryFactory._repository_cache = {}

        # Setup
        from persistence.adapters.sqlite_adapter import SQLiteRepository

        config = get_config()
        repo = SQLiteRepository(config.config["backends"]["sqlite"])

        form_path = f"read_benchmark_{record_count}"
        if repo.exists(form_path):
            repo.drop_storage(form_path, force=True)
        repo.create_storage(form_path, benchmark_spec)

        # Create data
        records = [generate_sample_record(i) for i in range(record_count)]
        repo.bulk_create(form_path, benchmark_spec, records)

        # Benchmark read_all
        benchmark = BenchmarkResult(f"Read All ({record_count} records)")

        for _ in range(10):
            start = time.time()
            data = repo.read_all(form_path, benchmark_spec)
            duration = time.time() - start

            benchmark.add_timing(duration)
            assert len(data) == record_count

        benchmark.print_report(record_count)

        # Cleanup
        repo.drop_storage(form_path, force=True)
        del os.environ["VIBECFORMS_CONFIG_DIR"]


def print_summary_header():
    """Print benchmark suite header."""
    print("\n" + "=" * 80)
    print(" " * 20 + "VibeCForms Performance Benchmarks")
    print("=" * 80)
    print("\n🎯 Testing:")
    print("   • Bulk create operations (TXT vs SQLite)")
    print("   • Migration performance (TXT → SQLite)")
    print("   • Tag operations latency")
    print("   • Read operations performance")
    print("\n" + "=" * 80 + "\n")


def print_summary_footer():
    """Print benchmark suite footer."""
    print("\n" + "=" * 80)
    print("✅ Benchmark suite complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Run benchmarks with custom output
    print_summary_header()

    # Run pytest with verbose output
    exit_code = pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "-s",  # Show print output
        ]
    )

    print_summary_footer()

    sys.exit(exit_code)

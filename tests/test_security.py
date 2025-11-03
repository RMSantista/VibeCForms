"""
Security tests for workflow system

Tests that verify:
1. Custom scripts are properly sandboxed with RestrictedPython
2. Dangerous operations (file I/O, imports, etc.) are blocked
3. Only safe operations are permitted
"""

import pytest
from pathlib import Path
import sys
import os

# Add src to path (use absolute path)
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from workflow.prerequisite_checker import PrerequisiteChecker


@pytest.fixture
def checker(tmp_path):
    """Create a PrerequisiteChecker with temporary scripts directory"""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    return PrerequisiteChecker(scripts_dir=str(scripts_dir))


@pytest.fixture
def sample_process():
    """Sample process for testing"""
    return {
        "process_id": "test_123",
        "kanban_id": "test_kanban",
        "current_state": "pending",
        "field_values": {"value": 100, "name": "Test"},
        "created_at": "2025-11-05T10:00:00",
    }


@pytest.fixture
def sample_kanban():
    """Sample kanban for testing"""
    return {
        "kanban_id": "test_kanban",
        "name": "Test Kanban",
        "columns": [
            {"id": "pending", "name": "Pending"},
            {"id": "approved", "name": "Approved"},
        ],
    }


# ========== Test 1: File I/O is blocked ==========


def test_custom_script_blocks_file_read(
    checker, sample_process, sample_kanban, tmp_path
):
    """Test that custom scripts cannot read files"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "malicious_read.py"

    # Create malicious script that tries to read a file
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    try:
        # Try to read /etc/passwd
        with open('/etc/passwd', 'r') as f:
            data = f.read()
        return {'satisfied': True, 'message': 'File read succeeded (BAD!)'}
    except:
        return {'satisfied': False, 'message': 'File read blocked (GOOD)'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "malicious_read.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should fail - either compilation error or script returns False (blocked in try/except)
    assert results[0]["satisfied"] is False
    # Verify it was blocked (not allowed to read files)
    assert (
        "blocked" in results[0]["message"].lower()
        or "error" in results[0]["message"].lower()
    )


def test_custom_script_blocks_file_write(
    checker, sample_process, sample_kanban, tmp_path
):
    """Test that custom scripts cannot write files"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "malicious_write.py"

    # Create malicious script that tries to write a file
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    try:
        # Try to write a file
        with open('/tmp/malicious.txt', 'w') as f:
            f.write('Hacked!')
        return {'satisfied': True, 'message': 'File write succeeded (BAD!)'}
    except:
        return {'satisfied': False, 'message': 'File write blocked (GOOD)'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "malicious_write.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should fail - either compilation error or script returns False (blocked in try/except)
    assert results[0]["satisfied"] is False
    # Verify it was blocked (not allowed to write files)
    assert (
        "blocked" in results[0]["message"].lower()
        or "error" in results[0]["message"].lower()
    )


# ========== Test 2: Imports are blocked ==========


def test_custom_script_blocks_import(checker, sample_process, sample_kanban, tmp_path):
    """Test that custom scripts cannot import modules"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "malicious_import.py"

    # Create malicious script that tries to import
    with open(script_path, "w") as f:
        f.write(
            """
import os

def validate(process, kanban):
    # Try to execute system command
    os.system('echo Hacked!')
    return {'satisfied': True, 'message': 'Import succeeded (BAD!)'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "malicious_import.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should fail with compilation error
    assert results[0]["satisfied"] is False
    assert "error" in results[0]["message"].lower()


def test_custom_script_blocks_import_from(
    checker, sample_process, sample_kanban, tmp_path
):
    """Test that custom scripts cannot use 'from' imports"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "malicious_from_import.py"

    # Create malicious script with from import
    with open(script_path, "w") as f:
        f.write(
            """
from subprocess import call

def validate(process, kanban):
    call(['echo', 'Hacked!'])
    return {'satisfied': True, 'message': 'Import succeeded (BAD!)'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "malicious_from_import.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should fail with compilation error
    assert results[0]["satisfied"] is False
    assert "error" in results[0]["message"].lower()


# ========== Test 3: Dangerous builtins are blocked ==========


def test_custom_script_blocks_exec(checker, sample_process, sample_kanban, tmp_path):
    """Test that custom scripts cannot use exec()"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "malicious_exec.py"

    # Create malicious script that tries to use exec
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    try:
        exec('import os; os.system("echo Hacked!")')
        return {'satisfied': True, 'message': 'exec() succeeded (BAD!)'}
    except:
        return {'satisfied': False, 'message': 'exec() blocked (GOOD)'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "malicious_exec.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should fail (exec not available)
    assert results[0]["satisfied"] is False


def test_custom_script_blocks_eval(checker, sample_process, sample_kanban, tmp_path):
    """Test that custom scripts cannot use eval()"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "malicious_eval.py"

    # Create malicious script that tries to use eval
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    try:
        result = eval('__import__("os").system("echo Hacked!")')
        return {'satisfied': True, 'message': 'eval() succeeded (BAD!)'}
    except:
        return {'satisfied': False, 'message': 'eval() blocked (GOOD)'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "malicious_eval.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should fail (eval not available)
    assert results[0]["satisfied"] is False


def test_custom_script_blocks_compile(checker, sample_process, sample_kanban, tmp_path):
    """Test that custom scripts cannot use compile()"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "malicious_compile.py"

    # Create malicious script that tries to use compile
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    try:
        code = compile('import os', '<string>', 'exec')
        exec(code)
        return {'satisfied': True, 'message': 'compile() succeeded (BAD!)'}
    except:
        return {'satisfied': False, 'message': 'compile() blocked (GOOD)'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "malicious_compile.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should fail (compile and exec not available)
    assert results[0]["satisfied"] is False


# ========== Test 4: Safe operations work correctly ==========


def test_custom_script_allows_safe_math(
    checker, sample_process, sample_kanban, tmp_path
):
    """Test that custom scripts can use safe math operations"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "safe_math.py"

    # Create safe script with math operations
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    value = int(process['field_values'].get('value', 0))
    doubled = value * 2
    is_valid = doubled > 100

    if is_valid:
        return {'satisfied': True, 'message': f'Math works: {value} * 2 = {doubled}'}
    else:
        return {'satisfied': False, 'message': 'Value too small'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "safe_math.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should succeed (safe operations)
    assert results[0]["satisfied"] is True
    assert "Math works" in results[0]["message"]


def test_custom_script_allows_safe_string_operations(
    checker, sample_process, sample_kanban, tmp_path
):
    """Test that custom scripts can use safe string operations"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "safe_strings.py"

    # Create safe script with string operations
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    name = str(process['field_values'].get('name', ''))
    upper_name = name.upper()
    is_valid = len(name) > 0

    if is_valid:
        return {'satisfied': True, 'message': f'String ops work: {upper_name}'}
    else:
        return {'satisfied': False, 'message': 'Name is empty'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "safe_strings.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should succeed (safe operations)
    assert results[0]["satisfied"] is True
    assert "String ops work: TEST" in results[0]["message"]


def test_custom_script_allows_safe_list_operations(
    checker, sample_process, sample_kanban, tmp_path
):
    """Test that custom scripts can use safe list operations"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "safe_lists.py"

    # Create safe script with list operations
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    average = total / len(numbers)

    return {'satisfied': True, 'message': f'List ops work: sum={total}, avg={average}'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "safe_lists.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should succeed (safe operations)
    assert results[0]["satisfied"] is True
    assert "sum=15" in results[0]["message"]
    assert "avg=3" in results[0]["message"]


def test_custom_script_allows_safe_dict_operations(
    checker, sample_process, sample_kanban, tmp_path
):
    """Test that custom scripts can use safe dict operations"""
    scripts_dir = Path(checker.scripts_dir)
    script_path = scripts_dir / "safe_dicts.py"

    # Create safe script with dict operations
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    data = {'a': 1, 'b': 2, 'c': 3}
    total = sum(data.values())
    keys = list(data.keys())

    return {'satisfied': True, 'message': f'Dict ops work: keys={keys}, total={total}'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "safe_dicts.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Should succeed (safe operations)
    assert results[0]["satisfied"] is True
    assert "total=6" in results[0]["message"]

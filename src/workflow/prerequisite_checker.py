"""
PrerequisiteChecker - Validates prerequisites for workflow transitions

Supports 4 types of prerequisites:
1. field_check - Check if field meets condition (not_empty, equals, greater_than, etc.)
2. external_api - Call external API to validate
3. time_elapsed - Check if minimum time has passed since state entry
4. custom_script - Execute custom Python script for validation

Philosophy: "Warn, Not Block"
- Prerequisites NEVER block transitions
- They warn users and require justification for forced transitions
- Users maintain autonomy to override with business justification
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import re
import requests
from pathlib import Path
from RestrictedPython import compile_restricted_exec, safe_globals
from RestrictedPython.Guards import guarded_iter_unpack_sequence


def _getitem(obj, key):
    """Safe getitem for dictionary/list access"""
    return obj[key]


class PrerequisiteChecker:
    """
    Checker for workflow transition prerequisites

    Validates prerequisites and returns results with warnings.
    Never blocks - only informs.
    """

    def __init__(self, scripts_dir: str = "src/workflow/scripts"):
        """
        Initialize PrerequisiteChecker

        Args:
            scripts_dir: Directory containing custom validation scripts
        """
        self.scripts_dir = scripts_dir

    # ========== Main Validation ==========

    def check_prerequisites(
        self, prerequisites: List[dict], process: dict, kanban: dict
    ) -> List[dict]:
        """
        Check all prerequisites for a transition

        Args:
            prerequisites: List of prerequisite definitions
            process: Current process state
            kanban: Kanban definition

        Returns:
            List of prerequisite results:
            [
                {
                    'type': str,
                    'satisfied': bool,
                    'message': str,
                    'details': dict (optional)
                },
                ...
            ]
        """
        results = []

        for prereq in prerequisites:
            prereq_type = prereq.get("type")

            if prereq_type == "field_check":
                result = self._check_field(prereq, process)
            elif prereq_type == "external_api":
                result = self._check_external_api(prereq, process)
            elif prereq_type == "time_elapsed":
                result = self._check_time_elapsed(prereq, process)
            elif prereq_type == "custom_script":
                result = self._check_custom_script(prereq, process, kanban)
            else:
                result = {
                    "type": prereq_type,
                    "satisfied": False,
                    "message": f"Unknown prerequisite type: {prereq_type}",
                }

            results.append(result)

        return results

    def are_all_satisfied(self, results: List[dict]) -> bool:
        """
        Check if all prerequisite results are satisfied

        Args:
            results: List of prerequisite check results

        Returns:
            True if all satisfied
        """
        return all(r.get("satisfied", False) for r in results)

    def get_unsatisfied(self, results: List[dict]) -> List[dict]:
        """
        Get list of unsatisfied prerequisites

        Args:
            results: List of prerequisite check results

        Returns:
            List of unsatisfied results
        """
        return [r for r in results if not r.get("satisfied", False)]

    # ========== Type 1: Field Check ==========

    def _check_field(self, prereq: dict, process: dict) -> dict:
        """
        Check field value condition

        Supported conditions:
        - not_empty: Field must have a value
        - equals: Field must equal specific value
        - not_equals: Field must not equal value
        - contains: Field must contain substring
        - greater_than: Field must be > value (numeric)
        - less_than: Field must be < value (numeric)
        - greater_or_equal: Field must be >= value
        - less_or_equal: Field must be <= value
        - regex: Field must match regex pattern

        Args:
            prereq: Prerequisite definition
            process: Process data

        Returns:
            Result dict with satisfied/message
        """
        field = prereq.get("field")
        condition = prereq.get("condition")
        expected_value = prereq.get("value")
        message = prereq.get(
            "message", f"Field '{field}' does not meet condition '{condition}'"
        )

        field_values = process.get("field_values", {})
        actual_value = field_values.get(field)

        satisfied = False

        if condition == "not_empty":
            satisfied = actual_value is not None and actual_value != ""

        elif condition == "equals":
            satisfied = actual_value == expected_value

        elif condition == "not_equals":
            satisfied = actual_value != expected_value

        elif condition == "contains":
            if isinstance(actual_value, str):
                satisfied = expected_value in actual_value

        elif condition in [
            "greater_than",
            "less_than",
            "greater_or_equal",
            "less_or_equal",
        ]:
            try:
                actual_num = float(actual_value) if actual_value is not None else 0
                expected_num = float(expected_value)

                if condition == "greater_than":
                    satisfied = actual_num > expected_num
                elif condition == "less_than":
                    satisfied = actual_num < expected_num
                elif condition == "greater_or_equal":
                    satisfied = actual_num >= expected_num
                elif condition == "less_or_equal":
                    satisfied = actual_num <= expected_num
            except (ValueError, TypeError):
                satisfied = False

        elif condition == "regex":
            if isinstance(actual_value, str):
                try:
                    pattern = re.compile(expected_value)
                    satisfied = pattern.match(actual_value) is not None
                except re.error:
                    satisfied = False

        return {
            "type": "field_check",
            "satisfied": satisfied,
            "message": message,
            "details": {
                "field": field,
                "condition": condition,
                "actual_value": actual_value,
                "expected_value": expected_value,
            },
        }

    # ========== Type 2: External API ==========

    def _check_external_api(self, prereq: dict, process: dict) -> dict:
        """
        Call external API to validate

        API should return JSON with:
        {
            "satisfied": true/false,
            "message": "Reason if not satisfied"
        }

        Args:
            prereq: Prerequisite definition with 'url' and optional 'method', 'headers', 'payload'
            process: Process data

        Returns:
            Result dict
        """
        url = prereq.get("url")
        method = prereq.get("method", "GET").upper()
        headers = prereq.get("headers", {})
        payload = prereq.get("payload", {})
        timeout = prereq.get("timeout", 5)  # 5 seconds default
        message = prereq.get("message", "External API validation failed")

        # Replace placeholders in URL with process data
        url = self._replace_placeholders(url, process)

        # Replace placeholders in payload
        if payload:
            payload = self._replace_placeholders_dict(payload, process)

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(
                    url, headers=headers, json=payload, timeout=timeout
                )
            else:
                return {
                    "type": "external_api",
                    "satisfied": False,
                    "message": f"Unsupported HTTP method: {method}",
                }

            if response.status_code == 200:
                data = response.json()
                satisfied = data.get("satisfied", False)
                api_message = data.get("message", message)

                return {
                    "type": "external_api",
                    "satisfied": satisfied,
                    "message": api_message,
                    "details": {
                        "url": url,
                        "status_code": response.status_code,
                        "response": data,
                    },
                }
            else:
                return {
                    "type": "external_api",
                    "satisfied": False,
                    "message": f"API returned status {response.status_code}",
                    "details": {"url": url, "status_code": response.status_code},
                }

        except requests.exceptions.Timeout:
            return {
                "type": "external_api",
                "satisfied": False,
                "message": f"API call timed out after {timeout}s",
            }
        except requests.exceptions.RequestException as e:
            return {
                "type": "external_api",
                "satisfied": False,
                "message": f"API call failed: {str(e)}",
            }
        except Exception as e:
            return {
                "type": "external_api",
                "satisfied": False,
                "message": f"Unexpected error: {str(e)}",
            }

    # ========== Type 3: Time Elapsed ==========

    def _check_time_elapsed(self, prereq: dict, process: dict) -> dict:
        """
        Check if minimum time has elapsed since state entry

        Args:
            prereq: Prerequisite with 'hours' or 'minutes'
            process: Process data

        Returns:
            Result dict
        """
        min_hours = prereq.get("hours", 0)
        min_minutes = prereq.get("minutes", 0)
        message = prereq.get(
            "message", f"Minimum {min_hours}h {min_minutes}m not elapsed"
        )

        # Total minimum time in seconds
        min_seconds = (min_hours * 3600) + (min_minutes * 60)

        # Get time of last state change (or creation if no history)
        history = process.get("history", [])

        if history:
            # Last transition time
            last_transition = history[-1]
            timestamp_str = last_transition.get("timestamp")
        else:
            # Process creation time
            timestamp_str = process.get("created_at")

        try:
            timestamp = datetime.fromisoformat(timestamp_str)

            # Make timezone-aware if needed
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            elapsed = (now - timestamp).total_seconds()

            satisfied = elapsed >= min_seconds

            return {
                "type": "time_elapsed",
                "satisfied": satisfied,
                "message": message,
                "details": {
                    "required_seconds": min_seconds,
                    "elapsed_seconds": elapsed,
                    "since": timestamp_str,
                },
            }

        except (ValueError, TypeError) as e:
            return {
                "type": "time_elapsed",
                "satisfied": False,
                "message": f"Invalid timestamp: {str(e)}",
            }

    # ========== Type 4: Custom Script ==========

    def _check_custom_script(self, prereq: dict, process: dict, kanban: dict) -> dict:
        """
        Execute custom Python script for validation (SANDBOXED)

        Script should define a function:
        def validate(process, kanban):
            # Custom logic
            return {
                'satisfied': True/False,
                'message': 'Reason'
            }

        SECURITY: Uses RestrictedPython for sandboxing:
        - No file I/O operations
        - No imports
        - No access to dangerous builtins (__import__, open, etc.)
        - Limited to safe operations only

        Args:
            prereq: Prerequisite with 'script' filename
            process: Process data
            kanban: Kanban definition

        Returns:
            Result dict
        """
        script_name = prereq.get("script")
        message = prereq.get("message", "Custom script validation failed")

        if not script_name:
            return {
                "type": "custom_script",
                "satisfied": False,
                "message": "No script specified",
            }

        script_path = Path(self.scripts_dir) / script_name

        if not script_path.exists():
            return {
                "type": "custom_script",
                "satisfied": False,
                "message": f"Script not found: {script_name}",
            }

        try:
            # Read script
            with open(script_path, "r") as f:
                script_code = f.read()

            # Compile with RestrictedPython (sandboxed)
            byte_code = compile_restricted_exec(script_code)

            if byte_code.errors:
                return {
                    "type": "custom_script",
                    "satisfied": False,
                    "message": f"Script compilation errors: {', '.join(byte_code.errors)}",
                }

            # Create SAFE namespace with restricted builtins
            # Use RestrictedPython's safe_globals as base
            restricted_globals = safe_globals.copy()

            # Add additional safe builtins that are useful but not included in safe_globals
            restricted_globals["__builtins__"].update(
                {
                    # Math functions
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    # Type conversions
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "frozenset": frozenset,
                    # Iteration
                    "enumerate": enumerate,
                    "zip": zip,
                    "reversed": reversed,
                    "filter": filter,
                    "map": map,
                    # Utilities
                    "any": any,
                    "all": all,
                }
            )

            # Add process and kanban data to namespace
            restricted_globals.update(
                {
                    "process": process,
                    "kanban": kanban,
                    # Add guards for dictionary/list access
                    "_getitem_": _getitem,
                    "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
                }
            )

            # Execute script in sandboxed environment
            exec(byte_code.code, restricted_globals)

            # Call validate function
            if "validate" not in restricted_globals:
                return {
                    "type": "custom_script",
                    "satisfied": False,
                    "message": "Script does not define validate() function",
                }

            result = restricted_globals["validate"](process, kanban)

            return {
                "type": "custom_script",
                "satisfied": result.get("satisfied", False),
                "message": result.get("message", message),
                "details": {"script": script_name},
            }

        except Exception as e:
            return {
                "type": "custom_script",
                "satisfied": False,
                "message": f"Script execution error: {str(e)}",
            }

    # ========== Helper Methods ==========

    def _replace_placeholders(self, text: str, process: dict) -> str:
        """
        Replace {field_name} placeholders with process values

        Example: "{process_id}" → "pedidos_123_abc"
        """
        if not isinstance(text, str):
            return text

        # Replace process fields
        for key, value in process.items():
            placeholder = f"{{{key}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(value))

        # Replace field_values
        field_values = process.get("field_values", {})
        for key, value in field_values.items():
            placeholder = f"{{{key}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(value))

        return text

    def _replace_placeholders_dict(self, data: dict, process: dict) -> dict:
        """Replace placeholders in dictionary recursively"""
        result = {}

        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._replace_placeholders(value, process)
            elif isinstance(value, dict):
                result[key] = self._replace_placeholders_dict(value, process)
            else:
                result[key] = value

        return result

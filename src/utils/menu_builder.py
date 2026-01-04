"""
Menu builder utilities for VibeCForms.

This module provides high-level functions for building navigation menus
and form lists. Internal implementation details are private (prefixed with _).
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from flask import current_app

from utils.spec_loader import load_spec

logger = logging.getLogger(__name__)

# Private constants
_DEFAULT_FOLDER_ICON = "fa-folder"


def _load_folder_config(folder_path: str) -> Optional[Dict[str, Any]]:
    """Load folder configuration from _folder.json if it exists.

    Args:
        folder_path: Full path to the folder

    Returns:
        Dictionary with config or None if file doesn't exist
    """
    config_path = os.path.join(folder_path, "_folder.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config {config_path}: {e}")
            return None
        except PermissionError as e:
            logger.error(f"Permission denied reading {config_path}: {e}")
            return None
    return None


def _scan_specs_directory(base_path=None, relative_path=""):
    """Recursively scan the specs directory and build menu structure.

    Returns a list of menu items, where each item is either:
    - {"type": "form", "name": str, "path": str, "title": str, "icon": str}
    - {"type": "folder", "name": str, "path": str, "icon": str, "children": list, "description": str (optional)}
    """
    # Use specs directory from app config if base_path not provided
    if base_path is None:
        try:
            # Try to get from Flask app context first
            specs_dir = current_app.config.get("SPECS_DIR")
        except RuntimeError:
            # If no app context, fall back to global variable (for tests)
            from src import VibeCForms

            specs_dir = VibeCForms.SPECS_DIR
        base_path = specs_dir

    items = []
    full_path = os.path.join(base_path, relative_path) if relative_path else base_path

    if not os.path.exists(full_path):
        return items

    # Get all items in directory
    entries = sorted(os.listdir(full_path))

    for entry in entries:
        # Skip folder config files
        if entry == "_folder.json":
            continue

        entry_path = os.path.join(full_path, entry)
        relative_entry_path = (
            os.path.join(relative_path, entry) if relative_path else entry
        )

        if os.path.isdir(entry_path):
            # It's a folder - recursively scan it
            children = _scan_specs_directory(base_path, relative_entry_path)
            if children:  # Only add folder if it has content
                # Try to load folder configuration
                folder_config = _load_folder_config(entry_path)

                if folder_config:
                    # Use config values
                    folder_item = {
                        "type": "folder",
                        "name": folder_config.get("name", entry.capitalize()),
                        "path": relative_entry_path,
                        "icon": folder_config.get("icon", _DEFAULT_FOLDER_ICON),
                        "children": children,
                    }
                    # Add description if present
                    if "description" in folder_config:
                        folder_item["description"] = folder_config["description"]
                    # Add order if present
                    if "order" in folder_config:
                        folder_item["order"] = folder_config["order"]
                else:
                    # Fallback to default behavior
                    folder_item = {
                        "type": "folder",
                        "name": entry.capitalize(),
                        "path": relative_entry_path,
                        "icon": _DEFAULT_FOLDER_ICON,
                        "children": children,
                    }

                items.append(folder_item)

        elif entry.endswith(".json"):
            # It's a form spec file
            form_name = entry[:-5]  # Remove .json extension
            form_path = (
                os.path.join(relative_path, form_name) if relative_path else form_name
            )

            try:
                spec = load_spec(form_path)
                # Read icon from spec (optional field)
                icon = spec.get("icon", "")

                # Fallback: root level forms without icon get default
                if not icon and not relative_path:
                    icon = "fa-file-alt"

                items.append(
                    {
                        "type": "form",
                        "name": form_name,
                        "path": form_path,
                        "title": spec.get("title", form_name.capitalize()),
                        "icon": icon,
                    }
                )
            except Exception:
                # Skip invalid spec files
                continue

    # Sort items by order field if present, then by name
    items.sort(key=lambda x: (x.get("order", 999), x.get("name", "")))

    return items


def _get_all_forms_flat(menu_items=None, prefix=""):
    """Flatten the hierarchical menu structure to get all forms.

    Returns a list of all form items with their full path and category.
    Each item: {"title": str, "path": str, "icon": str, "category": str}
    """
    if menu_items is None:
        menu_items = _scan_specs_directory()

    forms = []

    for item in menu_items:
        if item["type"] == "form":
            category = prefix if prefix else "Geral"

            # Get icon from item (already resolved in _scan_specs_directory)
            icon = item.get("icon", "fa-file-alt")

            forms.append(
                {
                    "title": item["title"],
                    "path": item["path"],
                    "icon": icon,
                    "category": category,
                }
            )
        elif item["type"] == "folder":
            # Recursively get forms from folder
            folder_name = item["name"]
            nested_forms = _get_all_forms_flat(item["children"], folder_name)
            forms.extend(nested_forms)

    return forms


def _generate_menu_html(menu_items, current_form_path="", level=0):
    """Generate HTML for menu items recursively with submenu support.

    Args:
        menu_items: List of menu items from _scan_specs_directory()
        current_form_path: Current form path to highlight active items
        level: Nesting level (0 = root)
    """
    if not menu_items:
        return ""

    html = ""
    for item in menu_items:
        if item["type"] == "form":
            # Form item
            is_active = item["path"] == current_form_path
            active_class = "active" if is_active else ""
            icon_html = f'<i class="fa {item["icon"]}"></i> ' if item["icon"] else ""

            html += f'<li><a href="/{item["path"]}" class="{active_class}">{icon_html}{item["title"]}</a></li>\n'

        elif item["type"] == "folder":
            # Folder item with submenu
            # Check if any child is active
            is_path_active = current_form_path.startswith(item["path"])
            icon_html = f'<i class="fa {item["icon"]}"></i> '

            html += f"""<li class="has-submenu">
                <a href="javascript:void(0)" class="folder-item {'active-path' if is_path_active else ''}">
                    {icon_html}{item["name"]}
                    <i class="fa fa-chevron-right submenu-arrow"></i>
                </a>
                <ul class="submenu level-{level + 1}">
                    {_generate_menu_html(item["children"], current_form_path, level + 1)}
                </ul>
            </li>\n"""

    return html


# =============================================================================
# PUBLIC API (only 2 functions)
# =============================================================================


def get_forms_for_landing_page() -> List[Dict[str, str]]:
    """Get flat list of all forms for landing page cards.

    Returns:
        List of form items with structure:
        [{"title": str, "path": str, "icon": str, "category": str}, ...]

    Example:
        >>> forms = get_forms_for_landing_page()
        >>> for form in forms:
        ...     print(f"{form['title']} - {form['category']}")
    """
    return _get_all_forms_flat()


def get_menu_html(current_form_path: str = "") -> str:
    """Generate HTML for navigation menu with current form highlighted.

    Args:
        current_form_path: Path to highlight as active (e.g., "financeiro/contas")

    Returns:
        HTML string for sidebar menu

    Example:
        >>> menu_html = get_menu_html("contatos")
        >>> # Returns HTML with "contatos" highlighted as active
    """
    menu_items = _scan_specs_directory()
    return _generate_menu_html(menu_items, current_form_path)

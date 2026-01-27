import os
import sys
import logging
import argparse
from flask import Flask
from dotenv import load_dotenv

# Add src directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from utils.spec_loader import set_specs_dir

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default fallback directories (src-relative)
DATA_FILE = os.path.join(os.path.dirname(__file__), "registros.txt")
FALLBACK_SPECS_DIR = os.path.join(os.path.dirname(__file__), "specs")
FALLBACK_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Active directories (will be set by initialize_app or default to fallback)
SPECS_DIR = FALLBACK_SPECS_DIR
TEMPLATE_DIR = FALLBACK_TEMPLATE_DIR
BUSINESS_CASE_ROOT = None

# Table column widths (percentage) - stored in app.config for controllers
TABLE_FIELDS_TOTAL_WIDTH = 60
TABLE_TAGS_WIDTH = 15
TABLE_ACTIONS_WIDTH = 25

# Create app with fallback template directory (will be updated during initialization)
app = Flask(__name__, template_folder=FALLBACK_TEMPLATE_DIR)

# Register blueprints at module load time (before initialize_app)
# This allows tests that import `app` directly to have routes available
from controllers.forms import forms_bp
from controllers.tags import tags_bp
from controllers.kanban import kanban_bp
from controllers.migration import migration_bp
from controllers.relationships import relationships_bp

app.register_blueprint(forms_bp)
app.register_blueprint(tags_bp)
app.register_blueprint(kanban_bp)
app.register_blueprint(migration_bp)
app.register_blueprint(relationships_bp)


def parse_arguments():
    """Parse command-line arguments for business case path."""
    parser = argparse.ArgumentParser(
        description="VibeCForms - AI-first framework for process tracking systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/VibeCForms.py examples/ponto-de-vendas
  python src/VibeCForms.py examples/processo-seletivo
  uv run app examples/demo
        """,
    )
    parser.add_argument(
        "business_case_path",
        help="Path to the business case directory (e.g., examples/ponto-de-vendas)",
    )
    return parser.parse_args()


def initialize_app(business_case_path):
    """Initialize the Flask app with the given business case path.

    Args:
        business_case_path: Path to the business case directory
    """
    global BUSINESS_CASE_ROOT, SPECS_DIR, TEMPLATE_DIR

    # Convert to absolute path
    BUSINESS_CASE_ROOT = os.path.abspath(business_case_path)

    # Validate business case directory exists
    if not os.path.isdir(BUSINESS_CASE_ROOT):
        print(f"Error: Business case directory not found: {BUSINESS_CASE_ROOT}")
        print("\nAvailable examples:")
        examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
        if os.path.isdir(examples_dir):
            for item in os.listdir(examples_dir):
                item_path = os.path.join(examples_dir, item)
                if os.path.isdir(item_path):
                    print(f"  - examples/{item}")
        sys.exit(1)

    # Set up directory paths
    SPECS_DIR = os.path.join(BUSINESS_CASE_ROOT, "specs")
    TEMPLATE_DIR = os.path.join(BUSINESS_CASE_ROOT, "templates")

    # Validate required directories exist
    if not os.path.isdir(SPECS_DIR):
        print(f"Error: specs/ directory not found in {BUSINESS_CASE_ROOT}")
        sys.exit(1)

    # Configure spec loader to use business case specs directory
    set_specs_dir(SPECS_DIR)

    # Template directory is optional (will fallback to src/templates)
    if not os.path.isdir(TEMPLATE_DIR):
        logger.info(f"templates/ not found in business case, using fallback templates")
        TEMPLATE_DIR = FALLBACK_TEMPLATE_DIR

    # Update Flask app template folder
    app.template_folder = TEMPLATE_DIR

    # Store global state in app.config for access by controllers
    app.config["BUSINESS_CASE_ROOT"] = BUSINESS_CASE_ROOT
    app.config["SPECS_DIR"] = SPECS_DIR
    app.config["TEMPLATE_DIR"] = TEMPLATE_DIR
    app.config["FALLBACK_TEMPLATE_DIR"] = FALLBACK_TEMPLATE_DIR
    app.config["TABLE_FIELDS_TOTAL_WIDTH"] = TABLE_FIELDS_TOTAL_WIDTH
    app.config["TABLE_TAGS_WIDTH"] = TABLE_TAGS_WIDTH
    app.config["TABLE_ACTIONS_WIDTH"] = TABLE_ACTIONS_WIDTH

    # Initialize persistence configuration with business case config path
    from persistence.config import get_config, reset_config
    from persistence.schema_history import get_history, reset_history

    reset_config()  # Reset any existing config
    reset_history()  # Reset any existing history
    config_path = os.path.join(BUSINESS_CASE_ROOT, "config", "persistence.json")
    history_path = os.path.join(BUSINESS_CASE_ROOT, "config", "schema_history.json")
    get_config(config_path)  # Initialize with business case config
    get_history(history_path)  # Initialize with business case history

    logger.info(f"Initialized VibeCForms with business case: {BUSINESS_CASE_ROOT}")
    logger.info(f"  - Specs: {SPECS_DIR}")
    logger.info(f"  - Templates: {TEMPLATE_DIR}")
    logger.info(f"  - Config: {config_path}")
    logger.info(f"  - History: {history_path}")


# ===============================================9
# RE-EXPORTS FOR Testing
# ===============================================
# These imports allow tests to continue importing

from controllers.forms import (
    read_forms,
    write_forms,
)

# Import from new menu_builder module, with compatibility wrappers
from utils.menu_builder import (
    get_forms_for_landing_page,
    _scan_specs_directory as scan_specs_directory,
    _load_folder_config as load_folder_config,
    _generate_menu_html,
    _get_all_forms_flat,
)

# Import from new spec_renderer module, with compatibility wrappers
from utils.spec_renderer import (
    render_form_fields,
    render_table,
    validate_form as validate_form_data,
    _render_field as generate_form_field,
    _render_table_headers as generate_table_headers,
    _render_table_row as generate_table_row,
    _get_template_path as get_template_path,
    _read_template as read_template,
)


# Compatibility wrapper for get_all_forms_flat
def get_all_forms_flat(menu_items=None, prefix=""):
    """Compatibility wrapper for tests that pass menu_items directly."""
    if menu_items is not None:
        # Called with menu_items (legacy test usage)
        return _get_all_forms_flat(menu_items, prefix)
    # Called without arguments (new usage)
    return get_forms_for_landing_page()


# Compatibility wrapper for generate_menu_html
def generate_menu_html(menu_items, current_form_path="", level=0):
    """Compatibility wrapper for tests that pass menu_items directly."""
    return _generate_menu_html(menu_items, current_form_path, level)


from utils.spec_loader import load_spec

# Make these available for import
__all__ = [
    "app",
    "initialize_app",
    "parse_arguments",
    "read_forms",
    "write_forms",
    "validate_form_data",
    "scan_specs_directory",
    "get_all_forms_flat",
    "generate_menu_html",
    "generate_form_field",
    "generate_table_headers",
    "generate_table_row",
    "get_template_path",
    "read_template",
    "load_folder_config",
    "load_spec",
]


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()

    # Initialize app with business case path
    initialize_app(args.business_case_path)

    print(f"Iniciando VibeCForms com business case: {BUSINESS_CASE_ROOT}")
    print("Servidor Flask em http://0.0.0.0:5000 ...")
    try:
        app.run(debug=True, host="0.0.0.0", port=5000)
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")
        print("Verifique se a porta 5000 está livre ou se há outro serviço rodando.")

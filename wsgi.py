"""
WSGI entry point for VibeCForms application.

This module serves as the entry point for WSGI servers like Gunicorn.
It imports the Flask application instance from the main application module.

Usage:
    BUSINESS_CASE_PATH=examples/ponto-de-vendas gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

Environment Variables:
    BUSINESS_CASE_PATH: Path to the business case directory (required)
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Get business case path from environment variable
business_case_path = os.environ.get("BUSINESS_CASE_PATH")

if not business_case_path:
    print("Error: BUSINESS_CASE_PATH environment variable not set")
    print("\nUsage:")
    print(
        "  BUSINESS_CASE_PATH=examples/ponto-de-vendas gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app"
    )
    sys.exit(1)

# Initialize application with business case path
from VibeCForms import app, initialize_app

initialize_app(business_case_path)

if __name__ == "__main__":
    # This allows running the WSGI file directly for testing
    app.run(debug=False, host="0.0.0.0", port=5000)

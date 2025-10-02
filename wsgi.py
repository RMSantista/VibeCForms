"""
WSGI entry point for VibeCForms application.

This module serves as the entry point for WSGI servers like Gunicorn.
It imports the Flask application instance from the main application module.

Usage:
    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from VibeCForms import app

if __name__ == "__main__":
    # This allows running the WSGI file directly for testing
    app.run(debug=False, host="0.0.0.0", port=5000)

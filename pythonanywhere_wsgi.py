"""WSGI entrypoint for PythonAnywhere's standard Web app configuration.

The main application is FastAPI, which is ASGI. PythonAnywhere's standard
Web tab loads a WSGI callable named ``application``. a2wsgi bridges the two
so the same FastAPI app can run without using PythonAnywhere's ASGI beta.
"""

import sys
from pathlib import Path

from a2wsgi import ASGIMiddleware

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.main import app  # noqa: E402

application = ASGIMiddleware(app)

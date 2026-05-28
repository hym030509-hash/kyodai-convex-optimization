# Deployment

## PythonAnywhere standard Web app

This project is a FastAPI app. FastAPI is ASGI, while PythonAnywhere's
standard Web app configuration expects WSGI. Use `pythonanywhere_wsgi.py`
as the WSGI entrypoint.

1. Pull the latest branch on PythonAnywhere:

```bash
cd ~/kyodai-convex-optimization
git checkout ryukayuiii-work
git pull origin ryukayuiii-work
```

2. Install dependencies in the virtual environment used by the Web app:

```bash
pip install -r requirements.txt
```

3. In the PythonAnywhere WSGI configuration file, use:

```python
import sys

project_home = "/home/YOUR_USERNAME/kyodai-convex-optimization"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from pythonanywhere_wsgi import application
```

Replace `YOUR_USERNAME` with the PythonAnywhere username.

4. Reload the Web app from the PythonAnywhere Web tab.

## Local development

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

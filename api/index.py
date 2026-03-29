import sys
from pathlib import Path

# Ensure the project root is on the path so `app` and `application.*` can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import app as flask_app  # noqa: E402


# Expose a plain WSGI callable that Vercel can detect reliably
application = flask_app.wsgi_app
app = flask_app

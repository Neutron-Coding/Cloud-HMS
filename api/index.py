import sys
from pathlib import Path

# Ensure the project root is on the path so `app` and `application.*` can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import app as application  # noqa: E402


# Expose the pre-built Flask WSGI app
app = application

from flask import Flask

import os

from .routes import register_routes
from .settings import LOG_DIR, UPLOAD_DIR


def create_app():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    app = Flask(__name__, template_folder="templates")
    register_routes(app)
    return app

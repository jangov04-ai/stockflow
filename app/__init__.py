"""StockFlow: sistema de gestión de inventario."""

from flask import Flask

from .config import CONFIGS
from .models import db


def create_app(config_name="development", **overrides):
    app = Flask(__name__)
    app.config.from_object(CONFIGS[config_name])
    app.config.update(overrides)

    db.init_app(app)

    from .routes.api import api_bp
    from .routes.web import web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()

    return app

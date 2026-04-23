import math

from flask import Flask
from .extensions import db, migrate
from .config import Config


def srm_to_hex(srm):
    """Convert SRM color value to an approximate hex color."""
    srm = max(0, min(srm or 0, 40))
    r = min(255, max(0, int(255 * math.pow(0.975, srm))))
    g = min(255, max(0, int(255 * math.pow(0.88, srm))))
    b = min(255, max(0, int(255 * math.pow(0.7, srm))))
    return f"#{r:02x}{g:02x}{b:02x}"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Template globals
    app.jinja_env.globals["srm_color"] = srm_to_hex

    from .routes import recipes, brewday, styles, fermentation, admin
    app.register_blueprint(recipes.bp)
    app.register_blueprint(brewday.bp)
    app.register_blueprint(styles.bp)
    app.register_blueprint(fermentation.bp)
    app.register_blueprint(admin.bp)

    return app

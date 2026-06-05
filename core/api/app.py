from quart import Quart

from .routes.verify import verify_bp
from .routes.members import members_bp
from .routes.restore import restore_bp


def create_app() -> Quart:
    app = Quart(__name__)

    app.register_blueprint(verify_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(restore_bp)

    return app

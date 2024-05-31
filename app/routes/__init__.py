from flask import Blueprint
from .message_routes import main as main_blueprint
from .assistant_routes import assistant as assistant_blueprint

def register_blueprints(app):
    app.register_blueprint(main_blueprint)
    app.register_blueprint(assistant_blueprint)
    # Register other blueprints as needed

from flask import Blueprint
from .message_routes import main as main_blueprint

def register_blueprints(app):
    app.register_blueprint(main_blueprint)
    # Register other blueprints as needed

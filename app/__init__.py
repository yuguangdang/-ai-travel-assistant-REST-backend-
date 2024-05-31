import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import redis
import json
import logging
from colorama import init
from app.utils import ColoredFormatter


load_dotenv()

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter('{levelname}: {message}', style='{'))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARNING)


def create_app():
    setup_logging()
    
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    CORS(app)

    jwt = JWTManager(app)  # Initialize JWTManager with the app

    # Initialize Redis
    try:
        redis_client = redis.StrictRedis(
            host=os.getenv("REDIS_HOST"),
            port=6379,
            password=os.getenv("REDIS_PASSWORD"),
            ssl=False,  # Ensure SSL is disabled
        )
        redis_client.ping()
        print("Connected to Redis server.")
    except redis.ConnectionError as e:
        print(f"Could not connect to Redis server: {e}")
        exit(1)

    # Helper functions to save and retrieve session data from Redis
    def save_session_to_redis(token, data):
        # Convert the data dictionary to a JSON string
        redis_client.set(f"session:{token}", json.dumps(data))

    def get_session_from_redis(token):
        # Retrieve the data from Redis and convert it back to a dictionary
        data = redis_client.get(f"session:{token}")
        if data:
            return json.loads(
                data.decode("utf-8")
            )  # Decode bytes to string and parse JSON
        return None

    # Add the Redis client and helper functions to the Flask app config
    app.config["REDIS_CLIENT"] = redis_client
    app.config["SAVE_SESSION"] = save_session_to_redis
    app.config["GET_SESSION"] = get_session_from_redis

    # Register blueprints
    from app.routes import register_blueprints

    register_blueprints(app)

    return app

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import decode_token
from openai import AzureOpenAI
import os
import logging
import requests

from app.assistant_handlers import get_response_from_assistant
from app.utils import extract_info_from_request, get_user_chat_status
from app.platform_handlers import reply_Teams, reply_WhatsApp

main = Blueprint("main", __name__)

# Initialize Azure OpenAI client with environment variables
assistant_id = os.getenv("ASSISTANT_ID")
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)


@main.route("/")
def index():
    return "Chatbot REST API Server is running"


@main.route("/init", methods=["POST"])
def handle_init():
    try:
        data = request.json
        platform = data["platform"]
        token = data["token"]
        message = data["message"]

        if not platform or not token or not message:
            return jsonify({"error": "Missing platform, token, or message"}), 400

        # Retrieve session data from Redis
        session_data = current_app.config["GET_SESSION"](token)
        if not session_data:
            # Decode token to get user metadata
            metadata = decode_token(token)
            session_data = {"metadata": metadata}

            # Create a new thread if no session data is found
            thread = client.beta.threads.create()
            session_data["thread_id"] = thread.id
            current_app.config["SAVE_SESSION"](token, session_data)

            message = f"Hello, please remember my metadata through our conversation: {session_data['metadata']}"
        else:
            message = f"Hi, I'm back. Let's continue our conversation."

        # Interact with Azure OpenAI assistant
        reply = get_response_from_assistant(
            platform, token, session_data["thread_id"], message, client
        )

        return jsonify(
            {
                "platform": platform,
                "thread_id": session_data["thread_id"],
                "message": message,
                "reply": reply,
            }
        )

    except Exception as e:
        print("Error handling chat:", e)
        return jsonify({"error": "Internal Server Error"}), 500


@main.route("/chat", methods=["POST"])
def handle_chat():
    try:
        # Extract data from the request
        data = request.json
        platform = data["platform"]
        token = data["token"]
        message = data["message"]

        # Validate input data
        if not platform or not token or not message:
            return jsonify({"error": "Missing platform, token, or message"}), 400

        # Retrieve session data from Redis
        session_data = current_app.config["GET_SESSION"](token)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404

        # Interact with Azure OpenAI assistant
        reply = get_response_from_assistant(
            platform, token, session_data["thread_id"], message, client
        )

        # Check if the reply is valid
        if not reply:
            return jsonify({"error": "Failed to get a reply from the assistant"}), 500

        return jsonify(
            {
                "platform": platform,
                "thread_id": session_data["thread_id"],
                "message": message,
                "reply": reply,
            }
        )

    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error handling chat: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@main.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Check the content type of the request
        if request.content_type == 'application/json':
            data = request.json
        elif request.content_type == 'application/x-www-form-urlencoded':
            data = request.form.to_dict()
        else:
            return jsonify({"error": "Unsupported Media Type"}), 415
        # print(f"Request data: {data}")

        platform, token, message, conversation_id = extract_info_from_request(data)

        # Retrieve session data from Redis
        session_data = current_app.config["GET_SESSION"](token)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404

        # Retrieve user chat status and URL
        email = session_data["metadata"][
            "email"
        ]
        user_chat_data = get_user_chat_status(email)
        chat_status = user_chat_data["chatStatus"]
        chat_url = user_chat_data["chatUrl"]

        # If the chat status is 'agent', forward the message to the consultant
        if chat_status == "agent":
            payload = {"content": message}
            headers = {"Content-Type": "application/json"}
            response = requests.post(chat_url, json=payload, headers=headers)

            if response.status_code != 200:
                logging.error("Failed to forward message to the agent")

        else:
            # Interact with Azure OpenAI assistant
            reply = get_response_from_assistant(
                platform, token, session_data["thread_id"], message, client
            )

            # Check if the reply is valid
            if not reply:
                return jsonify({"error": "Failed to get a reply from the assistant"}), 500

            # Send the reply back to the original platform
            if platform == "Teams":
                reply_Teams(reply, conversation_id)
            elif platform == "WhatsApp":
                reply_WhatsApp(reply, conversation_id)
                pass
            else:
                return jsonify({"error": "Unsupported platform"}), 400

            return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error handling webhook: {e}")
        return jsonify({"error": "Internal Server Error"}), 500



import os
from flask import current_app
import requests
from colorama import Fore, Style, init
import logging

init(autoreset=True)  # Ensures that colorama resets colors to default after each print


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""

    LEVEL_COLORS = {
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.INFO: Fore.GREEN,
        logging.DEBUG: Fore.BLUE,
    }

    def format(self, record):
        log_fmt = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE) + self._fmt
        formatter = logging.Formatter(log_fmt, style="{")
        return formatter.format(record)


def extract_info_from_request(data):
    # Determine if the request is from Teams
    if "serviceUrl" in data and "channelId" in data and data["channelId"] == "msteams":
        platform = "Teams"
        conversation_id = data["conversation"]["id"]
        aadObjectId = data["from"]["aadObjectId"]
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZWJ0b3JJZCI6IkVESVpaWlpaWloiLCJlbWFpbCI6ImJlbi5zYXVsQGRvd25lcmdyb3VwLmNvbSIsImV4dGVybmFsUmVmZXJlbmNlIjo2NTY2OCwiZmlyc3ROYW1lIjoiWXVndWFuZyIsImxhc3ROYW1lIjoiRGFuZyIsIm5hbWUiOiJZdWd1YW5nIERhbmciLCJyb2xlTmFtZSI6InRyYXZlbGxlciIsInN1YiI6InRlc3QifQ.4ujBBKDLnnFxxCpJsrwd4OOSnFDqgkajOdV4BAKFxy8"
        message = data["text"]

        # Retrieve and save session data from Redis
        session_data = current_app.config["GET_SESSION"](token)
        session_data["conversation_id"] = conversation_id
        session_data["aadObjectId"] = aadObjectId
        current_app.config["SAVE_SESSION"](token, session_data)

    elif "WaId" in data:
        platform = "WhatsApp"
        conversation_id = data["WaId"]
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZWJ0b3JJZCI6IkVESVpaWlpaWloiLCJlbWFpbCI6ImJlbi5zYXVsQGRvd25lcmdyb3VwLmNvbSIsImV4dGVybmFsUmVmZXJlbmNlIjo2NTY2OCwiZmlyc3ROYW1lIjoiWXVndWFuZyIsImxhc3ROYW1lIjoiRGFuZyIsIm5hbWUiOiJZdWd1YW5nIERhbmciLCJyb2xlTmFtZSI6InRyYXZlbGxlciIsInN1YiI6InRlc3QifQ.4ujBBKDLnnFxxCpJsrwd4OOSnFDqgkajOdV4BAKFxy8"
        message = data["Body"]

        # Retrieve and save session data from Redis
        session_data = current_app.config["GET_SESSION"](token)
        session_data["conversation_id"] = conversation_id
        session_data["aadObjectId"] = "05eadb95-7237-4ca2-8273-cb2b63964748"
        current_app.config["SAVE_SESSION"](token, session_data)

    return platform, token, message, conversation_id


def get_user_chat_status(email):
    email = "Yuguang.Dang@travelctm.com"
    api_url = f"{os.getenv('GLOBAL_SERVER_URL')}/user/findUserByEmail/{email}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        user_data = response.json()

        chat_status = user_data.get("chatStatus")
        chat_url = user_data.get("chatUrl")

        return {"chatStatus": chat_status, "chatUrl": chat_url}
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving data: {e}")
        return {"error": str(e)}

import requests
import os
from twilio.rest import Client

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_WHATSAPP_FROM")
twilio_client = Client(account_sid, auth_token)


def reply_Teams(message, conversation_id):
    token_url = "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token"
    token_request_data = {
        "grant_type": "client_credentials",
        "scope": "https://api.botframework.com/.default",
        "client_id": os.getenv("TEAMS_CLIENT_ID"),
        "client_secret": os.getenv("TEAMS_CLIENT_SECRET"),
    }

    try:
        # Fetch the token
        token_response = requests.post(token_url, data=token_request_data)
        token_response.raise_for_status()
        token = token_response.json()["access_token"]

        # Send the message to Teams
        message_url = f"https://smba.trafficmanager.net/amer/v3/conversations/{conversation_id}/activities"
        message_data = {
            "type": "message",
            "text": message,
            "channelData": {
                "notification": {
                    "alert": True,
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        message_response = requests.post(
            message_url, json=message_data, headers=headers
        )
        message_response.raise_for_status()
        print("Message sent to Teams:", message_response.json())
    except requests.exceptions.RequestException as e:
        print("Error:", e)


def reply_WhatsApp(message, to_number):
    try:
        message = twilio_client.messages.create(
            from_=from_number,
            body=message,
            to=f"whatsapp:{to_number}",
        )
    except requests.exceptions.RequestException as e:
        print("Error:", e)

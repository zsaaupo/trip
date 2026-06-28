import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

def send_email(to, subject, body):

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": API_KEY,
        "content-type": "application/json"
    }

    payload = {
        "sender": {
            "name": "Make a Trip",
            "email": "makeatrip007@gmail.com"
        },
        "to": [
            {
                "email": to
            }
        ],
        "subject": subject,
        "htmlContent": f"<html><body>{body}</body></html>"
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.status_code)
    print(response.text)

    response.raise_for_status()
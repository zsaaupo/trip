import requests
from django.conf import settings

API_KEY = settings.BREVO_API_KEY

def send_email(to, subject, body):
    print("API Key loaded:", API_KEY is not None)
    print("API Key prefix:", API_KEY[:10] if API_KEY else "None")

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": "Make a Trip",
            "email": "makeatrip007@gmail.com",
        },
        "to": [
            {
                "email": to,
            }
        ],
        "subject": subject,
        "htmlContent": f"<html><body>{body}</body></html>",
    }

    print("Headers:", headers)

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    print("Status:", response.status_code)
    print("Response:", response.text)

    response.raise_for_status()
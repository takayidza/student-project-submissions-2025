import requests
from django.conf import settings
from asgiref.sync import sync_to_async

class TelegramBot:
    BASE_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/"

    @staticmethod
    @sync_to_async
    def send_message(chat_id, text):
        url = TelegramBot.BASE_URL + "sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=payload)
        result = response.json()

        # Check if the request was successful
        if not result.get("ok"):
            # Log or handle error if chat_id does not exist or other failure
            error_description = result.get("description", "Unknown error")
            print(f"Failed to send message: {error_description}")
            return {
                "success": False,
                "error": error_description
            }

        return {
            "success": True,
            "message_id": result["result"]["message_id"]
        }

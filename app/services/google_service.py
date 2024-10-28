from google.oauth2 import id_token
from google.auth.transport import requests
from core.config import get_app_settings

class GoogleService:
    def __init__(self):
        self.settings = get_app_settings()

    async def verify_token(self, token: str) -> dict:
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.settings.google_client_id
            )
            return idinfo
        except ValueError:
            raise ValueError("Invalid token")

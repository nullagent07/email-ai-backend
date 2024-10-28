from openai import AsyncOpenAI
from core.config import get_app_settings

class ThreadService:
    def __init__(self):
        self.settings = get_app_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    async def generate_response(self, context: str) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an email assistant."},
                {"role": "user", "content": context}
            ]
        )
        return response.choices[0].message.content

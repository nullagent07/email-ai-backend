from openai import AsyncOpenAI
from app.core.config import get_app_settings
from typing import List, Optional
from datetime import datetime
from app.models.assistant import AssistantProfile

settings = get_app_settings()

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._assistant_id = settings.openai_base_assistant_id  # ID предварительно созданного ассистента
        
    async def create_thread_with_initial_message(self, name: str, description: str) -> str:
        """Создает новый тред с начальным сообщением от ассистента"""
        initial_message = f"Здравствуйте! Я {name}, ваш персональный ассистент. {description}"
        
        # Создаем тред с начальным сообщением
        thread = await self.client.beta.threads.create(
            messages=[{
                "role": "assistant",
                "content": initial_message
            }]
        )
        
        return thread.id, initial_message
        
    async def add_message_to_thread(self, thread_id: str, content: str, role: str = "user"):
        """Добавляет сообщение в тред"""
        message = await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content
        )
        return message
        
    async def run_assistant(self, thread_id: str, assistant_id: str):
        """Запускает ассистента для обработки сообщений в треде"""
        run = await self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        return run
        
    async def get_response(self, thread_id: str, run_id: str):
        """Получает ответ ассистента"""
        messages = await self.client.beta.threads.messages.list(thread_id=thread_id)
        return messages.data[0].content[0].text.value 
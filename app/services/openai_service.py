from openai import AsyncOpenAI
from app.core.config import get_app_settings
from typing import List, Optional, Tuple, Dict
from datetime import datetime
import asyncio
from app.models.assistant import AssistantProfile

settings = get_app_settings()

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._assistant_id = settings.openai_base_assistant_id
        
    async def create_assistant(self, name: str, instructions: str, tools: Optional[List[Dict]] = None) -> str:
        """Создает нового ассистента в OpenAI"""
        assistant = await self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            tools=tools or [],
            model="gpt-4-1106-preview"
        )
        return assistant.id
        
    async def update_assistant(self, assistant_id: str, instructions: str) -> bool:
        """Обновляет инструкции существующего ассистента"""
        try:
            await self.client.beta.assistants.update(
                assistant_id=assistant_id,
                instructions=instructions
            )
            return True
        except Exception:
            return False
            
    async def delete_assistant(self, assistant_id: str) -> bool:
        """Удаляет ассистента из OpenAI"""
        try:
            await self.client.beta.assistants.delete(assistant_id)
            return True
        except Exception:
            return False
            
    async def get_assistant(self, assistant_id: str) -> Optional[Dict]:
        """Получает информацию об ассистенте"""
        try:
            assistant = await self.client.beta.assistants.retrieve(assistant_id)
            return {
                "id": assistant.id,
                "name": assistant.name,
                "instructions": assistant.instructions,
                "tools": assistant.tools
            }
        except Exception:
            return None
        
    async def create_thread_with_initial_message(self, user_name: str, thread_description: str) -> Tuple[str, str]:
        """Создает новый тред с начальным сообщением от ассистента"""
        # Создаем новый тред
        thread = await self.client.beta.threads.create()
        
        # Добавляем начальное сообщение с инструкциями
        initial_message = f"Вот инструкции которые ты должен учитывать при общении с {user_name}: {thread_description}"
        await self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=initial_message
        )
        
        return thread.id, initial_message
        
    async def create_thread_with_welcome_message(self, thread_description: str) -> Tuple[str, Optional[str]]:
        """Создает новый тред и инициирует генерацию приветственного сообщения от ассистента"""
        # Создаем новый тред
        thread = await self.client.beta.threads.create()
        
        # Запускаем ассистента для генерации приветственного сообщения
        run = await self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self._assistant_id,
            instructions=thread_description
        )
        
        # Ожидаем завершения генерации ответа
        while True:
            run_status = await self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                return thread.id, None
            await asyncio.sleep(1)
        
        # Получаем сгенерированное сообщение
        messages = await self.client.beta.threads.messages.list(
            thread_id=thread.id
        )
        if not messages.data:
            return thread.id, None
            
        return thread.id, messages.data[0].content[0].text.value
        
    async def add_message_to_thread(self, thread_id: str, content: str, role: str = "user") -> str:
        """Добавляет сообщение в тред"""
        message = await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content
        )
        return message.id
        
    async def run_assistant(self, thread_id: str, assistant_id: str) -> str:
        """Запускает ассистента для обработки сообщений в треде"""
        run = await self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        return run.id
        
    async def get_response(self, thread_id: str, run_id: str) -> Optional[str]:
        """Получает ответ ассистента после выполнения run"""
        run_status = await self.client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        
        if run_status.status != 'completed':
            return None
            
        messages = await self.client.beta.threads.messages.list(
            thread_id=thread_id
        )
        
        if not messages.data:
            return None
            
        return messages.data[0].content[0].text.value
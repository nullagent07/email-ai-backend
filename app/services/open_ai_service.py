from openai import AsyncOpenAI
from app.core.config import get_app_settings
from typing import List, Optional, Tuple, Dict
from datetime import datetime
import asyncio
from app.models.assistant_profile import AssistantProfile
import httpx
from app.schemas.email_thread_schema import EmailThreadCreate


settings = get_app_settings()

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._assistant_id = settings.openai_base_assistant_id

    @classmethod
    def get_instance(cls) -> 'OpenAIService':
        return cls()
        
    async def setup_assistant(self, recipient_name: str) -> str:
        """Создает и настраивает ассистента OpenAI для пользователя."""
        return await self.create_assistant(
            name=f"Email Assistant for {recipient_name}",
            instructions=self.generate_email_assistant_instructions(recipient_name)
        )
    
    async def create_assistant(self, name: str, instructions: str, tools: Optional[List[Dict]] = None) -> str:
        """Создает нового ассистента в OpenAI"""
        assistant = await self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            tools=tools or [],
            model="gpt-4-1106-preview"
        )
        return assistant.id
        
    def generate_email_assistant_instructions(self, recipient_name: str) -> str:
        """Формирует инструкции для ассистента."""
        return f"""
        Ты - умный email ассистент, который помогает вести переписку с {recipient_name}.
        ...
        """
        
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
            content=thread_description
        )
        
        return thread.id, initial_message

    async def create_thread(self) -> str:
        """
        Создает новый пустой тред в OpenAI
        
        Returns:
            str: ID созданного треда
        """
        try:
            thread = await self.client.beta.threads.create()
            return thread.id
        except Exception as e:
            raise ValueError(f"Failed to create thread: {str(e)}")

    async def create_thread_with_welcome_message(self, thread_description: str) -> Tuple[str, Optional[str]]:
        """Создает новый тред и инициирует генерацию приветственного сообщения от ассистента"""
        # Создаем новый тред
        thread = await self.client.beta.threads.create()
        
        # Запускаем ссистета для генерации приветственного сообщения
        run = await self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self._assistant_id,
            instructions=thread_description
        )
        
        # Ожидаем завершения генераци ответа
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
        
    async def add_message_to_thread(
        self, 
        thread_id: str, 
        content: str, 
        role: str = "user",
        timeout: float = 30.0
    ) -> Optional[str]:
        """
        Добавляе сообщение в тред OpenAI
        
        Args:
            thread_id: ID треда
            content: Текст сообщения
            role: Роль отправителя (user/assistant)
            timeout: Таймаут запроса в секундах
            
        Returns:
            Optional[str]: ID созданного сообщения или None в случае ошибки
        """
        try:
            message = await self.client.with_options(timeout=timeout).beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=content
            )
            return message.id
        except Exception as e:
            # Логируем ошибку
            print(f"Failed to add message to thread {thread_id}: {str(e)}")
            return None
        
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

    async def run_thread(
        self, 
        thread_id: str, 
        assistant_id: str,
        instructions: Optional[str] = None,
        timeout: float = 180.0
    ) -> Optional[str]:
        """
        Запускает тред с ассистентом и ждет ответа
        """
        try:
            client = self.client.with_options(
                timeout=httpx.Timeout(
                    timeout,
                    connect=10.0,
                    read=timeout,
                    write=10.0
                ),
                max_retries=3
            )

            # Проверяем существование треда и ассистента
            thread = await client.beta.threads.retrieve(thread_id)
            assistant = await client.beta.assistants.retrieve(assistant_id)
            print(f"Thread and assistant verified: {thread.id}, {assistant.id}")

            if instructions:
                await client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=instructions
                )

            run = await client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            print(f"Run created: {run.id}")

            start_time = datetime.now()
            queue_timeout = 30.0
            queue_start = None

            while (datetime.now() - start_time).total_seconds() < timeout:
                run_status = await client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                print(f"Run status: {run_status.status}")

                if run_status.status == 'completed':
                    messages = await client.beta.threads.messages.list(
                        thread_id=thread_id,
                        order='desc',
                        limit=1
                    )
                    if messages.data:
                        return messages.data[0].content[0].text.value
                    return None

                elif run_status.status == 'queued':
                    if queue_start is None:
                        queue_start = datetime.now()
                    elif (datetime.now() - queue_start).total_seconds() > queue_timeout:
                        print("Queue timeout exceeded")
                        try:
                            await client.beta.threads.runs.cancel(
                                thread_id=thread_id,
                                run_id=run.id
                            )
                        except Exception as cancel_error:
                            print(f"Error cancelling run: {str(cancel_error)}")
                        return None

                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    print(f"Run failed with status: {run_status.status}")
                    if hasattr(run_status, 'last_error'):
                        print(f"Error details: {run_status.last_error}")
                    return None

                await asyncio.sleep(2)

            # Если превышен основной таймаут
            if run_status.status not in ['completed', 'failed', 'cancelled', 'expired']:
                try:
                    await client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                except Exception as cancel_error:
                    print(f"Error cancelling run: {str(cancel_error)}")
            return None

        except Exception as e:
            print(f"Error in run_thread: {str(e)}")
            return None

    async def process_email(self, email_data, gmail_service):
        # Принимаем gmail_service как параметр
        pass
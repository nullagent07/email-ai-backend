from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from fastapi import HTTPException, status
import base64
from app.services.openai_service import OpenAIService
from app.repositories.assistant_repository import AssistantRepository
from app.models.assistant import AssistantProfile
from app.models.email_thread import EmailThread, ThreadStatus
from app.models.user import User
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository
from app.core.config import get_app_settings
from app.repositories.email_thread_repository import EmailThreadRepository
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.email_thread_schema import EmailThreadCreate
from app.models.email_message import EmailMessage, MessageType
from app.repositories.email_message_repository import EmailMessageRepository
from uuid import UUID
import email.utils

settings = get_app_settings()

class GmailService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
        self.oauth_repo = OAuthCredentialsRepository(db)
        self.thread_repo = EmailThreadRepository(db)
        self.assistant_repo = AssistantRepository(db)
        self.openai_service = OpenAIService()
        self.message_repo = EmailMessageRepository(db)
        self.processed_messages = set()
        
    async def setup_email_monitoring(self, user_id: UUID):
        """Настраивает отслеживание писем для активного треда"""
        
        # Получаем OAuth credentials
        oauth_creds = await self.oauth_repo.get_by_user_id_and_provider(
            user_id, 
            "google"
        )
        
        if not oauth_creds:
            raise ValueError("Gmail credentials not found")
            
        # Создаем сервис Gmail API
        creds = Credentials.from_authorized_user_info(
            info={
                "token": oauth_creds.access_token,
                "refresh_token": oauth_creds.refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
            }
        )
        
        service = build('gmail', 'v1', credentials=creds)
        
        # Настраиваем push-уведомления
        request = {
            'labelIds': ['INBOX'],
            'topicName': f'projects/{settings.google_project_id}/topics/{settings.google_topic_id}'
        }
        
        try:
            # Активируем отслеживание
            service.users().watch(userId='me', body=request).execute()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to setup email monitoring: {str(e)}"
            )
            
    async def process_incoming_email(self, email_data: dict, email_thread: EmailThread, user: User):
        """Обрабатывает входящее письмо"""
        
        # Проверяем статус треда
        if email_thread.status != ThreadStatus.ACTIVE:
            return
            
        try:
            # Получаем OAuth credentials
            oauth_creds = await self.oauth_repo.get_by_user_id_and_provider(
                user.id, 
                "google"
            )
            
            if not oauth_creds:
                raise ValueError("Gmail credentials not found")
                
            # Создаем Gmail API клиент
            gmail = build('gmail', 'v1', credentials=Credentials.from_authorized_user_info(
                info={
                    "token": oauth_creds.access_token,
                    "refresh_token": oauth_creds.refresh_token,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                }
            ))
            
            # Получаем полное сообщение
            message = gmail.users().messages().get(
                userId='me',
                id=email_data['message']['id'],
                format='full'
            ).execute()

            # Извлекаем содержимое
            email_content = self._extract_email_content(message)
            
            # Сохраняем входящее сообщение в БД
            await self.message_repo.create_message(EmailMessage(
                thread_id=email_thread.id,
                message_type=MessageType.INCOMING,
                subject=email_content['subject'],
                content=email_content['body'],
                sender_email=email_content['from'],
                recipient_email=oauth_creds.email
            ))
            
            # Отправляем в OpenAI и получаем ответ
            ai_response = await self.openai_service.run_thread(
                thread_id=email_thread.id,
                assistant_id=email_thread.assistant_id,
                instructions=email_content['body'],
                timeout=30.0
            )
            
            if ai_response:
                # Отправляем ответ через Gmail
                await self.send_email_response(
                    service=gmail,
                    thread_id=email_thread.id,
                    to=email_content['from'],
                    subject=f"Re: {email_content['subject']}",
                    content=ai_response
                )
                
                # Сохраняем исходящее сообщение в БД
                await self.message_repo.create_message(EmailMessage(
                    thread_id=email_thread.id,
                    message_type=MessageType.OUTGOING,
                    subject=f"Re: {email_content['subject']}",
                    content=ai_response,
                    sender_email=oauth_creds.email,
                    recipient_email=email_content['from']
                ))
                
        except Exception as e:
            print(f"Error processing incoming email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process incoming email: {str(e)}"
            )
            
    def extract_email_content(self, message: dict) -> dict:
        """Извлекает содержимое из Gmail сообщения"""
        headers = message['payload']['headers']
        
        content = {
            'subject': next(h['value'] for h in headers if h['name'].lower() == 'subject'),
            'from': next(h['value'] for h in headers if h['name'].lower() == 'from'),
            'body': ''
        }
        
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    content['body'] += base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode()
        else:
            content['body'] = base64.urlsafe_b64decode(
                message['payload']['body']['data']
            ).decode()
            
        return content 
    
    async def create_gmail_thread(self, thread_data: EmailThreadCreate) -> EmailThread:
        # 1. Получаем OAuth credentials для Gmail
        oauth_creds = await self.oauth_repo.get_by_user_id_and_provider(
            thread_data.user_id, 
            "google"
        )

        if not oauth_creds:
            raise ValueError("Gmail credentials not found")

        # 2. Создаем ассистента в OpenAI с подробными инструкциями
        assistant_id = await self.openai_service.create_assistant(
            name=f"Email Assistant for {thread_data.recipient_name}",
            instructions=f"""Ты - умный email ассистент, который помогает вести переписку с {thread_data.recipient_name}.
            
            Формат письма (используй HTML-теги):
            1. Базовая структура:
               <div style="margin-bottom: 20px">Приветствие</div>
               
               <div style="margin-bottom: 15px; text-indent: 20px">Первый абзац основной части</div>
               
               <div style="margin-bottom: 15px; text-indent: 20px">Второй абзац основной части</div>
               
               <div style="margin-bottom: 20px; text-indent: 20px">Заключительный абзац</div>
               
               <div style="margin-top: 30px">С уважением,<br>
               [Подпись]</div>
            
            2. Правила форматирования:
               • Каждый абзац оборачивай в <div> с отступами
               • Используй <br> для переноса строк
               • Для списков используй <ul> и <li>
               • Важные части можно выделить <strong>
            
            3. Прмер структуры:
            
            <div style="margin-bottom: 20px">
            Уважаемый {thread_data.recipient_name}!
            </div>
            
            <div style="margin-bottom: 15px; text-indent: 20px">
            Надеюсь, это письмо найдет Вас в добром здравии. [Оcновная мысль первого абзаца...]
            </div>
            
            <div style="margin-bottom: 15px; text-indent: 20px">
            [Второй абзац с отступом...]
            </div>
            
            <div style="margin-bottom: 20px; text-indent: 20px">
            [Заключительный абзац с отступом...]
            </div>
            
            <div style="margin-top: 30px">
            С уважением,<br>
            [Подпись]
            </div>
            
            Дополнительный контект:
            {thread_data.assistant}
            """
        )

        # 3. Создаем тред в OpenAI
        openai_thread_id = await self.openai_service.create_thread()

        # 4. Добавляем начальное сообщение в тред
        await self.openai_service.add_message_to_thread(
            thread_id=openai_thread_id,
            content=f"""Это начало email переписки с {thread_data.recipient_name}.
            
            Напиши первое приветственное письмо, учитывая следующий контекст:
            {thread_data.assistant}
            
            Письмо должно:
            1. Начинаться с приветствия
            2. Представить себя как описано в контексте
            3. Объяснить цель переписки
            4. Закончиться вежливой подписью
            """
        )

        # 5. Проверяем существование ассистента
        assistant = await self.openai_service.get_assistant(assistant_id)
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assistant not found"
            )

        # 6. Запускаем ассистента и получаем ответ с обработкой ошибок
        try:
            initial_message = await self.openai_service.run_thread(
                thread_id=openai_thread_id,
                assistant_id=assistant_id,
                instructions="""
                Сгенерируй приветственное письмо, учитывая:
                1. Имя получателя
                2. Контекст переписки
                3. Деловой стиль
                """,
                timeout=30.0  # таймаут
            )
            
            if initial_message is None:
                # Очищаем ресурсы при ошибке
                await self.openai_service.delete_assistant(assistant_id)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate initial message"
                )
                
        except Exception as e:
            # Очищаем ресурсы при ошибке
            await self.openai_service.delete_assistant(assistant_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error running thread: {str(e)}"
            )

        # 7. Отправляем email через Gmail API
        message = {
            'raw': base64.urlsafe_b64encode(
                f"""From: {oauth_creds.email}\r\n\
To: {thread_data.recipient_email}\r\n\
Subject: New conversation with {thread_data.recipient_name}\r\n\
MIME-Version: 1.0\r\n\
Content-Type: text/html; charset=utf-8\r\n\
\r\n\
{initial_message}""".encode()
            ).decode()
        }

        try:
            # Создаем сервис Gmail API используя существующий токен
            creds = Credentials.from_authorized_user_info(
                info={
                    "token": oauth_creds.access_token,
                    "refresh_token": oauth_creds.refresh_token,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                },
            )
            
            service = build('gmail', 'v1', credentials=creds)
            service.users().messages().send(userId="me", body=message).execute()
            
            # Настраиваем мониторинг писем для созданного треда
            await self.setup_email_monitoring(thread_data.user_id)
            
        except Exception as e:
            # В случае ошибки удаляем созданного ассистента
            await self.openai_service.delete_assistant(assistant_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {str(e)}"
            )
        
        # 7. Создаем профиль ассистента в базе
        assistant_profile = AssistantProfile(
            id=assistant_id,
            user_id=thread_data.user_id,
            name=thread_data.recipient_name,
            description=thread_data.assistant
        )
        await self.assistant_repo.create_assistant_profile(assistant_profile)
        
        # 8. Создаем email тред в базе
        new_thread = EmailThread(
            id=openai_thread_id,
            user_id=thread_data.user_id,
            thread_name=thread_data.recipient_name,
            description=thread_data.assistant,
            status=ThreadStatus.ACTIVE,
            assistant_id=assistant_id,
            recipient_email=thread_data.recipient_email,
            recipient_name=thread_data.recipient_name
        )
        thread = await self.thread_repo.create_thread(new_thread)
        
        return thread

    async def process_webhook_gmail_messages(self, history_list: dict, service) -> dict:
        if not history_list.get('history', []):
            return {"status": "success", "message": "No new messages"}
        
        processed_messages = []
        
        for history in history_list['history']:
            for message_added in history.get('messagesAdded', []):
                message = message_added['message']
                message_id = message['id']
                
                try:
                    # Получаем полное сообщение для меток
                    full_message = service.users().messages().get(
                        userId='me', 
                        id=message_id
                    ).execute()
                    label_ids = full_message.get('labelIds', [])

                    # Обрабатываем сообщение
                    message_content = await self.process_message(service, message_id, label_ids)
                    if message_content:
                        processed_messages.append(message_content)
                    else:
                        return {"status": "success", "message": "Message processed"}

                except Exception as e:
                    if 'notFound' in str(e):
                        print(f"Message {message_id} not found, skipping: {str(e)}")
                        return {"status": "success", "message": f"Message {message_id} not found"}
                    else:
                        raise e

        if processed_messages:
            latest_message = max(processed_messages, key=lambda x: x['timestamp'])
            self._print_message_info(latest_message)
            return {"status": "success", "message": latest_message}
            
        return {"status": "success", "message": "Messages processed"}

    def _extract_email_from_header(self, header_value: str) -> str:
        """Извлекает email адрес из заголовка письма
        
        Примеры входных данных:
        - "Имя <email@domain.com>" -> "email@domain.com"
        - "email@domain.com" -> "email@domain.com"
        """
        if '<' in header_value and '>' in header_value:
            return header_value[header_value.find('<')+1:header_value.find('>')]
        return header_value.strip()

    async def _extract_message_content(self, full_message: dict, message_id: str) -> dict:
        """Извлекает содержимое сообщения и проверяет существование треда"""
        
        headers = {header['name']: header['value'] 
                  for header in full_message['payload']['headers']}
        
        # Получаем чистые email адреса отправителя и получателя
        sender_email = self._extract_email_from_header(headers.get('From', ''))
        recipient_email = self._extract_email_from_header(headers.get('To', ''))
        
        # Проверяем существование активного треда с чистыми email адресами
        existing_thread = await self.thread_repo.find_active_thread(
            sender_email=sender_email,
            recipient_email=recipient_email
        )

        # Если тред не найден, прекращаем обработку
        if existing_thread is None:
            print(f"Тред не найден")
            return None
        
        # Получаем время сообщения в формате timestamp
        date_str = headers.get('Date')
        date_obj = email.utils.parsedate_to_datetime(date_str)
        timestamp = date_obj.timestamp()
        
        message_content = {
            'id': message_id,
            'timestamp': timestamp,
            'subject': headers.get('Subject'),
            'from': sender_email,
            'to': recipient_email,
            'date': headers.get('Date'),
            'body': '',
            'thread_id': existing_thread.id  # Добавляем ID найденного треда
        }
        
        # Получаем тело сообщения
        if 'parts' in full_message['payload']:
            for part in full_message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
                    message_content['body'] = body.split('\n')[0]
                    break
        else:
            if 'data' in full_message['payload']['body']:
                body = base64.urlsafe_b64decode(
                    full_message['payload']['body']['data']
                ).decode('utf-8')
                message_content['body'] = body.split('\n')[0]
        
        return message_content

    def _print_message_info(self, message: dict):
        """Выводит информацию о сообщении"""
        print(f"thread_id: {message['thread_id']}")
        print(f"Обрабатываем входящее сообщение ID: {message['id']}")
        print(f"Тема: {message['subject']}")
        print(f"От: {message['from']}")
        print(f"Кому: {message['to']}")
        print(f"Дата: {message['date']}")
        print(f"Содержание сообщения: {message['body']}")

    async def process_message(self, service, message_id: str, label_ids: list) -> dict:
        """
        Обрабатывает отдельное сообщение Gmail
        
        Args:
            service: Gmail API сервис
            message_id: ID сообщения
            label_ids: Список меток сообщения
            
        Returns:
            dict: Обработанное содержимое сообщения или None если сообщение пропущено
        """
        # Пропускаем уже обработанные сообщения
        if message_id in self.processed_messages:
            print(f"Пропускаем дублирующееся сообщение: {message_id}")
            return None
            
        # Пропускаем черновики и отправленные сообщения    
        if 'DRAFT' in label_ids or 'SENT' in label_ids:
            print(f"Пропускаем сообщение с метками {label_ids}")
            return None
                
        # Обрабатываем только входящие сообщения
        if 'INBOX' in label_ids:
            try:
                # Получаем полное сообщение
                full_message = service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()

                message_content = await self._extract_message_content(full_message, message_id)
                
                if message_content:
                    # Добавляем ID в множество обработанных
                    self.processed_messages.add(message_id)
                    return message_content
                    
            except Exception as e:
                print(f"Ошибка при обработке сообщения {message_id}: {str(e)}")
                return None
                
        return None
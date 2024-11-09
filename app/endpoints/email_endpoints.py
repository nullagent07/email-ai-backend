# app/endpoints/email_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.email_service import EmailService
from app.services.gmail_service import GmailService
from app.schemas.email_message_schema import EmailMessageCreate, EmailMessageResponse
from app.schemas.email_thread_schema import EmailThreadCreate, EmailThreadResponse, ThreadStatus
from app.core.dependency import get_db, get_current_user
from app.models.user import User
import json
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository
from app.core.config import settings
from app.services.oauth_service import OAuthService
import email.utils

router = APIRouter(prefix="/email", tags=["email"])

# Эндпоинт для создания нового email-потока
@router.post("/gmail/threads/", response_model=EmailThreadResponse)
async def create_thread(
    thread_data: EmailThreadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    gmail_service = GmailService(db)
    try:
        # Устанавливаем текущего пользователя как владельца потока
        thread_data.user_id = current_user.id
        thread = await gmail_service.create_gmail_thread(thread_data)
        return thread
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Эндпоинт для получения всех потоков текущего пользователя
@router.get("/threads/", response_model=List[EmailThreadResponse])
async def get_user_threads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    email_service = EmailService(db)
    try:
        threads = await email_service.get_user_threads(current_user.id)
        return threads
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Эндпоинт для закрытия потока
@router.put("/threads/{thread_id}/close", response_model=EmailThreadResponse)
async def close_thread(
    thread_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    email_service = EmailService(db)
    try:
        # Проверяем, принадлежит и поток текущему пользователю
        thread = await email_service.get_thread_by_id(thread_id)
        if not thread or thread.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Thread not found")
        updated_thread = await email_service.close_email_thread(thread_id)
        return updated_thread
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Эндпоинт для получения потоков по статусу
@router.get("/threads/status/{status}", response_model=List[EmailThreadResponse])
async def get_threads_by_status(
    status: ThreadStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    email_service = EmailService(db)
    try:
        threads = await email_service.get_threads_by_status(current_user.id, status)
        return threads
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Эндпоинт для отправки email-сообщения
@router.post("/messages/send", response_model=EmailMessageResponse)
async def send_email_message(
    message_data: EmailMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    email_service = EmailService(db)
    try:
        # Проверяем, принадлежит ли поток текущему пользователю
        thread = await email_service.get_thread_by_id(message_data.thread_id)
        if not thread or thread.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Thread not found")
        message = await email_service.send_email_message(message_data)
        return message
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Эндпоинт для получения всех сообщений в потоке
@router.get("/threads/{thread_id}/messages", response_model=List[EmailMessageResponse])
async def get_messages_in_thread(
    thread_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    email_service = EmailService(db)
    try:
        # Проверяем, принадлежит ли поток текущему пользователю
        thread = await email_service.get_thread_by_id(thread_id)
        if not thread or thread.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Thread not found")
        messages = await email_service.get_messages_in_thread(thread_id)
        return messages
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Эндпоинт для получения отдельног сообщения по его ID
@router.get("/messages/{message_id}", response_model=EmailMessageResponse)
async def get_message_by_id(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    email_service = EmailService(db)
    try:
        message = await email_service.get_message_by_id(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        # Проверяем, принадлежит ли сообщение потоку текущего пользователя
        thread = await email_service.get_thread_by_id(message.thread_id)
        if not thread or thread.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this message")
        return message
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/gmail/webhook")
async def gmail_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Получаем данные запроса от Pub/Sub
        pubsub_message = await request.json()
        
        # Проверяем наличие поля 'message' в запросе
        if 'message' not in pubsub_message:
            # Возвращаем успешный ответ для подтверждения получения
            return {"status": "acknowledged"}
        
        # Декодируем данные сообщения
        message_data = pubsub_message['message']['data']
        decoded_data = base64.b64decode(message_data).decode('utf-8')
        
        # Преобразуем данные в JSON
        email_data = json.loads(decoded_data)
        email_address = email_data.get('emailAddress')
        history_id = email_data['historyId']

        # print(f"Email address: {email_address}")
        # print(f"History ID: {history_id}")
        
        oauth_service = OAuthService(db)
        
        # Получаем учетные данные OAuth
        oauth_creds = await oauth_service.get_oauth_credentials_by_email_and_provider(email_address, 'google')
        creds = Credentials.from_authorized_user_info(
            info={
                "token": oauth_creds.access_token,
                "refresh_token": oauth_creds.refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
            }
        )
        service = build('gmail', 'v1', credentials=creds)
        
        # Получаем историю изменений начиная с полученного historyId
        try:
            # Используем historyId немного меньше текущего
            start_history_id = str(int(history_id) - 100)  # Отступаем на 100 назад
            
            # print(f"Запрашиваем историю начиная с ID: {start_history_id}")
            
            history_list = service.users().history().list(
                userId='me',
                startHistoryId=start_history_id,
                # historyTypes=['messageAdded']  # Интересуют только новые сообщения
                maxResults=10
            ).execute()
            
            # print(f"Полученный ответ history_list: {history_list}")
            
            if 'history' not in history_list:
                print("В ответе нет ключа 'history' - нет новых изменений")
                return {"status": "success", "message": "No new changes"}
            
            changes = history_list['history']
            # print(f"Найдено {len(changes)} изменений")
            
            # Создадим список для хранения сообщений
            processed_messages = []
            
            for history in changes:
                if 'messagesAdded' in history:
                    for message_added in history['messagesAdded']:
                        message = message_added['message']
                        message_id = message['id']
                        
                        # Получаем метки сообщения
                        labels = message.get('labelIds', [])
                        
                        # Пропускаем черновики и отправленные сообщения
                        if 'DRAFT' in labels or 'SENT' in labels:
                            print(f"Пропускаем сообщение с метками {labels}")
                            continue
                            
                        # Обрабатываем только входящие сообщения
                        if 'INBOX' in labels:
                            try:
                                # Получаем полное сообщение
                                full_message = service.users().messages().get(
                                    userId='me',
                                    id=message_id,
                                    format='full'
                                ).execute()
                                
                                # Получаем заголовки
                                headers = {header['name']: header['value'] 
                                         for header in full_message['payload']['headers']}
                                
                                # Получаем время сообщения в формате timestamp
                                date_str = headers.get('Date')
                                date_obj = email.utils.parsedate_to_datetime(date_str)
                                timestamp = date_obj.timestamp()
                                
                                message_content = {
                                    'id': message_id,
                                    'timestamp': timestamp,
                                    'subject': headers.get('Subject'),
                                    'from': headers.get('From'),
                                    'to': headers.get('To'),
                                    'date': headers.get('Date'),
                                    'body': ''
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
                                
                                processed_messages.append(message_content)
                                
                            except Exception as e:
                                print(f"Ошибка при обработке сообщения {message_id}: {str(e)}")
                                continue
            
            # Выводим только самое последнее сообщение
            if processed_messages:
                latest_message = max(processed_messages, key=lambda x: x['timestamp'])
                print(f"Обрабатываем входящее сообщение ID: {latest_message['id']}")
                print(f"Тема: {latest_message['subject']}")
                print(f"От: {latest_message['from']}")
                print(f"Кому: {latest_message['to']}")
                print(f"Дата: {latest_message['date']}")
                print(f"Содержание сообщения: {latest_message['body']}")
        
        except Exception as e:
            print(f"Ошибка при получении истории: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"Ошибка при обработке уведомления от Pub/Sub: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось обработать уведомление: {str(e)}"
        )

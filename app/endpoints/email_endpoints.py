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
            return {"status": "acknowledged"}
        
        # Декодируем данные сообщения
        message_data = pubsub_message['message']['data']
        decoded_data = base64.b64decode(message_data).decode('utf-8')
        
        # Преобразуем данные в JSON
        email_data = json.loads(decoded_data)
        email_address = email_data.get('emailAddress')
        history_id = email_data['historyId']
        
        oauth_service = OAuthService(db)
        gmail_service = GmailService(db)
        
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
        
        try:
            # Используем historyId немного меньше текущего
            start_history_id = str(int(history_id) - 100)
            
            history_list = service.users().history().list(
                userId='me',
                startHistoryId=start_history_id,
                maxResults=10
            ).execute()
            
            return await gmail_service.process_webhook_messages(history_list, service)
            
        except Exception as e:
            print(f"Ошибка при получении истории: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        print(f"Ошибка при обработке уведомления от Pub/Sub: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось обработать уведомление: {str(e)}"
        )
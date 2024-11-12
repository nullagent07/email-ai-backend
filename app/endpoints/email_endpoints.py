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
from google.auth.transport import requests
from google.oauth2 import id_token
from app.utils.oauth_verification import verify_google_webhook_token

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

# Изменяем начало функции gmail_webhook
@router.post("/gmail/webhook")
async def gmail_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        for header, value in request.headers.items():
            print(f"{header}: {value}")
        
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Отсутствует или неверный заголовок Authorization"
            )
            
        # Проверяем токен
        is_valid = await verify_google_webhook_token(auth_header)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен авторизации"
            )

        # Получаем данные запроса от Pub/Sub
        pubsub_message = await request.json()
        print("\n=== Получено уведомление от Pub/Sub ===")
        print("Сырые данные:", json.dumps(pubsub_message, indent=2))
        
        # Декодируем данные сообщения
        message_data = pubsub_message['message']['data']
        decoded_data = base64.b64decode(message_data).decode('utf-8')
        email_data = json.loads(decoded_data)
        
        email_address = email_data.get('emailAddress')
        history_id = email_data['historyId']
            
        gmail_service = GmailService(db)
        gmail = await gmail_service.create_gmail_service(email_address)
        
        try:
            # Получаем только последнее сообщение
            messages_response = gmail.users().messages().list(
                userId='me',
                q='in:inbox -in:sent -in:draft newer_than:1h',  # Только входящие за последний час
                maxResults=1  # Получаем только одно последнее сообщение
            ).execute()
            
            if 'messages' in messages_response and messages_response['messages']:
                # Получаем последнее сообщение
                last_message = messages_response['messages'][0]
                
                # Получаем полное сообщение
                full_message = gmail.users().messages().get(
                    userId='me',
                    id=last_message['id'],
                    format='full'
                ).execute()
                
                # Извлекаем заголовки
                headers = {h['name']: h['value'] for h in full_message['payload'].get('headers', [])}
                
                print("\n=== Последнее входящее сообщение ===")
                print(f"ID: {last_message['id']}")
                print(f"От: {headers.get('From', 'Неизвестно')}")
                print(f"Кому: {headers.get('To', 'Неизвестно')}")
                print(f"Тема: {headers.get('Subject', 'Без темы')}")
                print(f"Дата: {headers.get('Date', 'Неизвестно')}")
                print("Текст:")
                
                # Извлекаем текст сообщения
                if 'parts' in full_message['payload']:
                    for part in full_message['payload']['parts']:
                        if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                            text = base64.urlsafe_b64decode(part['body']['data']).decode()
                            # Берем только первую строку текста (последнее сообщение)
                            first_line = text.split('\n')[0].strip()
                            print(first_line)
                            break
                elif 'body' in full_message['payload'] and 'data' in full_message['payload']['body']:
                    text = base64.urlsafe_b64decode(full_message['payload']['body']['data']).decode()
                    # Берем только первую строку текста (последнее сообщение)
                    first_line = text.split('\n')[0].strip()
                    print(first_line)
                    
                print("-" * 50)
                
                # Создаем историю из последнего сообщения
                history_list = {
                    'history': [{
                        'id': history_id,
                        'messages': [last_message]
                    }]
                }
            else:
                print("Новых сообщений не найдено")
                history_list = {'history': []}
            
        except Exception as e:
            print(f"Ошибка при получении сообщений: {str(e)}")
            return {"status": "error", "message": str(e)}

        # # Обрабатываем сообщения через GmailService
        result = await gmail_service.process_webhook_gmail_messages(history_list, gmail)
        return {"status": "success", "message": "Сообщения обработаны успешно"}
        
    except Exception as e:
        print(f"Ошибка при обработке уведомления: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обработать уведомление: {str(e)}"
        )
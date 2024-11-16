# app/endpoints/email_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status, Request

from sqlalchemy.ext.asyncio import AsyncSession

# services
from app.services.email_thread_service import EmailThreadService
from app.services.gmail_service import GmailService
from app.services.user_service import UserService
from app.services.openai_service import OpenAIService
from app.services.oauth_service import OAuthCredentialsService
from app.services.assistant_profile_service import AssistantProfileService

# Schemas
from app.schemas.email_thread_schema import EmailThreadCreate

# core
from app.core.dependency import get_db

# other
import json
import base64
from typing import List

from app.core.config import settings

router = APIRouter(prefix="/email", tags=["email"])

# Эндпоинт для создания нового email-потока
# @router.post("/gmail/threads/", response_model=EmailThreadResponse)
@router.post("/gmail/threads/", status_code=status.HTTP_201_CREATED)
async def create_thread(
    request: Request,
    thread_data: EmailThreadCreate,
    user_service: UserService = Depends(UserService.get_instance),    
    openai_service: OpenAIService = Depends(OpenAIService.get_instance),
    gmail_service: GmailService = Depends(GmailService.get_instance),
    email_thread_service: EmailThreadService = Depends(EmailThreadService.get_instance),
    oauth_service: OAuthCredentialsService = Depends(OAuthCredentialsService.get_instance),
    assistant_service: AssistantProfileService = Depends(AssistantProfileService.get_instance),
):
    try:
        # Получаем текущего пользователя
        current_user = await user_service.get_current_user(request)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Устанавливаем user_id из текущего пользователя
        thread_data.user_id = current_user.id

        # Получаем oauth_creds
        oauth_creds = await oauth_service.get_oauth_credentials_by_user_id_and_provider(thread_data.user_id, "google")

        # Проверяем, что oauth_creds есть
        if not oauth_creds:
            raise ValueError("Gmail credentials not found")

        # Создание ассистента
        assistant_id = await openai_service.setup_assistant(thread_data)

        # Создание тред в OpenAI
        openai_thread_id = await openai_service.create_thread()
        
        # Добавляем начальное сообщение в тред
        await openai_service.add_message_to_thread(
            thread_id=openai_thread_id,
            content=f"Это начало email переписки с {thread_data.recipient_name}..."
        )

        # Запускаем тред
        initial_message = await openai_service.run_thread(
            thread_id=openai_thread_id,
            assistant_id=assistant_id,
            instructions="Сгенерируй приветственное письмо..."
        )

        # Формируем тело email
        message_body = email_thread_service.compose_email_body(oauth_creds.email, thread_data.recipient_email, initial_message)

        # Создаем gmail сервис
        gmail = await gmail_service.create_gmail_service(oauth_creds)

        # Отправляем email
        await gmail_service.send_email(gmail, message_body)
        
        # Сохранение данных thread
        await email_thread_service.create_thread(thread_data)

        # Сохраняем assistant
        await assistant_service.create_assistant_profile(assistant_id, thread_data)

        return {"status": "success", "message": "Thread created successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))    

# Изменяем начало функции gmail_webhook
@router.post("/gmail/webhook")
async def gmail_webhook(
    request: Request,
    gmail_service: GmailService = Depends(GmailService.get_instance),
    oauth_service: OAuthCredentialsService = Depends(OAuthCredentialsService.get_instance),
    openai_service: OpenAIService = Depends(OpenAIService.get_instance),
):  
    try:
        # Получаем заголовок Authorization
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Отсутствует или неверный заголовок Authorization"
            )        
    
        # Проверяем токен
        is_valid = await gmail_service.verify_google_webhook_token(auth_header)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен авторизации"
            )
    
        # Получаем email и historyId
        user_email = await gmail_service.extract_user_email_from_pubsub_request(request)
        
        # Получаем oauth_creds
        oauth_creds = await oauth_service.get_oauth_credentials_by_email_and_provider(user_email, "google")

        # Проверяем, что oauth_creds есть
        if not oauth_creds:
            print(f"Не найдены учетные данные для {user_email}")
            return {
                "status": "success",
                "message": "Gmail credentials not found"
            }
        

        # Получаем payload, headers и parts
        payload, headers, parts = await gmail_service.get_payload_and_headers_and_parts(oauth_creds)

        # Определяем, является ли сообщение входящим или исходящим
        inbox = await gmail_service.validate_inbox_or_outbox(headers, user_email)

        # Если сообщение не является входящим, то возвращаем успех
        if inbox is None:
            return {"status": "success", "message": "Outgoing message"}

        # Получаем адреса отправителя и получателя
        from_email, to_email = inbox

        print(f"from_email: {from_email}, to_email: {to_email}")

        

        # Получаем данные из payload
        body_data = await gmail_service.get_body_data_from_payload(payload, parts)

        print(f"body_data: {body_data}")

        # # Добавляем сообщение в тред
        # await openai_service.add_message_to_thread(
        #     thread_id=openai_thread_id,
        #     content=last_message
        # )

        return {"status": "success", "message": "History received"}

    except Exception as e:
        print(f"Ошибка при обработке уведомления: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обработать уведомление: {str(e)}"
        )
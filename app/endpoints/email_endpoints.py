# app/endpoints/email_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status, Request

from sqlalchemy.ext.asyncio import AsyncSession

# services
from app.services.open_ai_thread_service import OpenAiThreadService
from app.services.gmail_service import GmailService
from app.services.user_service import UserService
from app.services.open_ai_service import OpenAIService
from app.services.oauth_service import OAuthCredentialsService
from app.services.assistant_profile_service import AssistantProfileService
from app.services.gmail_thread_service import GmailThreadService

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
# @router.post("/gmail/threads/", response_model=OpenAiThreadResponse)
@router.post("/gmail/threads/", status_code=status.HTTP_201_CREATED)
async def create_thread(
    request: Request,
    thread_data: EmailThreadCreate,
    user_service: UserService = Depends(UserService.get_instance),    
    open_ai_service: OpenAIService = Depends(OpenAIService.get_instance),
    gmail_service: GmailService = Depends(GmailService.get_instance),
    open_ai_thread_service: OpenAiThreadService = Depends(OpenAiThreadService.get_instance),
    oauth_service: OAuthCredentialsService = Depends(OAuthCredentialsService.get_instance),
    assistant_service: AssistantProfileService = Depends(AssistantProfileService.get_instance),
    gmail_thread_service: GmailThreadService = Depends(GmailThreadService.get_instance),
):
    try:
        # Получаем текущего пользователя
        current_user = await user_service.get_current_user(request)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Получаем oauth_creds
        oauth_creds = await oauth_service.get_oauth_credentials_by_user_id_and_provider(current_user.id, "google")

        # Проверяем, что oauth_creds есть
        if not oauth_creds:
            raise ValueError("Gmail credentials not found")

        # Создание ассистента
        assistant_id = await open_ai_service.setup_assistant(thread_data.recipient_name)

        # Создание тред в OpenAI
        open_ai_thread_id = await open_ai_service.create_thread()
        
        # Добавляем начальное сообщение в тред
        await open_ai_service.add_message_to_thread(
            thread_id=open_ai_thread_id,
            content=f"Это начало email переписки с {thread_data.recipient_name}..."
        )

        # Запускаем тред
        initial_message = await open_ai_service.run_thread(
            thread_id=open_ai_thread_id,
            assistant_id=assistant_id,
            instructions="Сгенерируй приветственное письмо..."
        )

        # Формируем тело email
        message_body = open_ai_thread_service.compose_email_body(
            oauth_creds.email, 
            thread_data.recipient_email, 
            initial_message
        )

        # Создаем gmail сервис
        gmail = await gmail_service.create_gmail_service(oauth_creds)

        # Отправляем email
        gmail_response = await gmail_service.send_email(gmail, message_body)

        # print(f"response: {response['threadId']}")

        # Сохраняем assistant
        await assistant_service.create_assistant_profile(
            assistant_id=assistant_id, 
            user_id=current_user.id, 
            assistant_description=thread_data.assistant
        )

        # Сохранение данных thread
        await open_ai_thread_service.create_thread(
            id=open_ai_thread_id, 
            user_id=current_user.id, 
            description=thread_data.assistant, 
            assistant_id=assistant_id, 
            recipient_email=thread_data.recipient_email, 
            recipient_name=thread_data.recipient_name,
            sender_email=oauth_creds.email
        )

        # Создаем gmail_thread
        await gmail_thread_service.create_gmail_thread(
            gmail_thread_id=gmail_response['threadId'],
            user_id=current_user.id,
            open_ai_thread_id=open_ai_thread_id,
            recipient_email=thread_data.recipient_email
        )

        return {"status": "success", "message": "Thread created successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))    

# Изменяем начало функции gmail_webhook
@router.post("/gmail/webhook")
async def gmail_webhook(
    request: Request,
    gmail_service: GmailService = Depends(GmailService.get_instance),
    oauth_service: OAuthCredentialsService = Depends(OAuthCredentialsService.get_instance),
    open_ai_service: OpenAIService = Depends(OpenAIService.get_instance),
    open_ai_thread_service: OpenAiThreadService = Depends(OpenAiThreadService.get_instance),
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
    
        # Получаем email
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
        payload, headers, parts, gmail_thread_id = await gmail_service.get_payload_and_headers_and_parts(oauth_creds)

        print(f"gmail_thread_id: {gmail_thread_id}")

        # return {"status": "success", "message": "Gmail thread id received"}
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

        # print(f"body_data: {body_data}")

        print(f"oauth_creds.user_id: {oauth_creds.user_id}")
        print(f"from_email: {from_email}")

        # Определение треда с пользователем
        open_ai_thread_id = await open_ai_thread_service.get_thread_id_by_user_id_and_recipient_email(oauth_creds.user_id, recipient_email=from_email)

        # # опеределяет асситент тред по gmail_thread_id и user_id и recipient_email
        # thread_id = await open_ai_thread_service.get_thread_id_by_user_id_and_recipient_email(oauth_creds.user_id, recipient_email=from_email)

        if open_ai_thread_id is None:
            return {"status": "success", "message": "Thread not found"}
        
        # добавить сообщение в openai_thread
        await open_ai_service.add_message_to_thread(
            thread_id=open_ai_thread_id,
            content=body_data
        )

        # получить ассистент
        assistant_id = await open_ai_thread_service.get_assistant_id_by_thread_id(open_ai_thread_id)

        # запустить тред
        thread_response = await open_ai_service.run_thread(thread_id=open_ai_thread_id, assistant_id=assistant_id)

        if thread_response is None:
            return {"status": "success", "message": "Thread response not found"}

        # создать gmail сервис
        gmail = await gmail_service.create_gmail_service(oauth_creds)

        # сформировать email
        email_body = open_ai_thread_service.compose_email_body(sender_email=user_email, recipient_email=from_email, content=thread_response, thread_id=gmail_thread_id)

        # отправить email
        await gmail_service.send_email(gmail, email_body)

        return {"status": "success", "message": "History received"}

    except Exception as e:
        print(f"Ошибка при обработке уведомления: {str(e)}")
        return {"status": "success", "message": "Error"}
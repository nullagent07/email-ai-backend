# app/endpoints/email_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status, Request

from sqlalchemy.ext.asyncio import AsyncSession

# services
from app.services.email_service import EmailService
from app.services.gmail_service import GmailService
from app.services.user_service import UserService
from app.services.openai_service import OpenAIService
from app.services.oauth_service import OAuthService

# Schemas
from app.schemas.email_message_schema import EmailMessageCreate, EmailMessageResponse
from app.schemas.email_thread_schema import EmailThreadCreate, EmailThreadResponse, ThreadStatus

# core
from app.core.dependency import get_db

# utils
from app.utils.oauth_verification import verify_google_webhook_token

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
    email_service: EmailService = Depends(EmailService.get_instance),
    oauth_service: OAuthService = Depends(OAuthService.get_instance),
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
        message_body = email_service.compose_email_body(oauth_creds.email, thread_data.recipient_email, initial_message)

        # Создаем gmail сервис
        gmail = await gmail_service.create_gmail_service(oauth_creds)

        # Отправляем email
        await gmail_service.send_email(gmail, message_body)
        
        # Сохранение данных в базе данных
        return await openai_service.save_assistant_and_thread(assistant_id, openai_thread_id, thread_data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))    

# Изменяем начало функции gmail_webhook
@router.post("/gmail/webhook")
async def gmail_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    print(request)
    return {"status": "success", "message": "Webhook received"}
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
            # Получаем историю изменений
            history_list = gmail.users().history().list(
                userId='me',
                startHistoryId=history_id,
                historyTypes=['messageAdded']  # Только добавление новых сообщений
            ).execute()
            
            print("\nПолученная история:", json.dumps(history_list, indent=2))
            
            if 'history' not in history_list:
                print("История пуста")
                return {"status": "success", "message": "No messages to process"}

            # Проверяем каждую запись в истории
            for record in history_list['history']:
                if 'messagesAdded' in record:
                    for message_added in record['messagesAdded']:
                        # Проверяем метки прямо в уведомлении
                        labels = message_added['message'].get('labelIds', [])
                        
                        # Изменяем условие для обработки только исходящих сообщений
                        if 'SENT' not in labels:
                            print(f"Пропускаем уведомление (не исходящее сообщение), метки: {labels}")
                            return {"status": "success", "message": "Не исходящее сообщение"}
                        
                        # Если дошли сюда - это исходящее сообщение, получаем его содержимое
                        message_id = message_added['message']['id']
                        message = gmail.users().messages().get(
                            userId='me',
                            id=message_id,
                            format='full'
                        ).execute()
                        
                        # Выводим информацию об исходящем сообщении
                        headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
                        print("\n=== Новое исходящее сообщение ===")
                        print(f"ID: {message_id}")
                        print(f"Кому: {headers.get('To', 'Неизвестно')}")
                        print(f"Тема: {headers.get('Subject', 'Без темы')}")
                        print(f"Метки: {labels}")
                        
                        # Здесь можно добавить дополнительную обработку исходящего сообщения
                        
            return {"status": "success", "message": "История обработана"}
            
        except Exception as e:
            print(f"Ошибка при получении истории: {str(e)}")
            return {"status": "error", "message": str(e)}

    except Exception as e:
        print(f"Ошибка при обработке уведомления: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обработать уведомление: {str(e)}"
        )

# # Эндпоинт для получения всех потоков текущего пользователя
# @router.get("/threads/", response_model=List[EmailThreadResponse])
# async def get_user_threads(
#     db: AsyncSession = Depends(get_db),
#     user_service: UserService = Depends(UserService.get_instance),
# ):
#     email_service = EmailService(db)
#     try:
#         threads = await email_service.get_user_threads(user_service.get_current_user().id)
#         return threads
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# # Эндпоинт для закрытия потока
# @router.put("/threads/{thread_id}/close", response_model=EmailThreadResponse)
# async def close_thread(
#     thread_id: int,
#     db: AsyncSession = Depends(get_db),
#     user_service: UserService = Depends(UserService.get_instance),
# ):
#     email_service = EmailService(db)
#     try:
#         # Проверяем, принадлежит и поток текущему пользователю
#         thread = await email_service.get_thread_by_id(thread_id)
#         if not thread or thread.user_id != user_service.get_current_user().id:
#             raise HTTPException(status_code=404, detail="Thread not found")
#         updated_thread = await email_service.close_email_thread(thread_id)
#         return updated_thread
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# # Эндпоинт для получения потоков по статусу
# @router.get("/threads/status/{status}", response_model=List[EmailThreadResponse])
# async def get_threads_by_status(
#     status: ThreadStatus,
#     db: AsyncSession = Depends(get_db),
#     user_service: UserService = Depends(UserService.get_instance)
# ):
#     email_service = EmailService(db)
#     try:
#         threads = await email_service.get_threads_by_status(user_service.get_current_user().id, status)
#         return threads
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# # Эндпоинт для отправки email-сообщения
# @router.post("/messages/send", response_model=EmailMessageResponse)
# async def send_email_message(
#     message_data: EmailMessageCreate,
#     db: AsyncSession = Depends(get_db),
#     user_service: UserService = Depends(UserService.get_instance)
# ):
#     email_service = EmailService(db)
#     try:
#         # Проверяем, принадлежит ли поток текущему пользователю
#         thread = await email_service.get_thread_by_id(message_data.thread_id)
#         if not thread or thread.user_id != user_service.get_current_user().id:
#             raise HTTPException(status_code=404, detail="Thread not found")
#         message = await email_service.send_email_message(message_data)
#         return message
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# # Эндпоинт для получения всех сообщений в потоке
# @router.get("/threads/{thread_id}/messages", response_model=List[EmailMessageResponse])
# async def get_messages_in_thread(
#     thread_id: int,
#     db: AsyncSession = Depends(get_db),
#     user_service: UserService = Depends(UserService.get_instance)
# ):
#     email_service = EmailService(db)
#     try:
#         # Проверяем, принадлежит ли поток текущему пользователю
#         thread = await email_service.get_thread_by_id(thread_id)
#         if not thread or thread.user_id != user_service.get_current_user().id:
#             raise HTTPException(status_code=404, detail="Thread not found")
#         messages = await email_service.get_messages_in_thread(thread_id)
#         return messages
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# # Эндпоинт для получения отдельног сообщения по его ID
# @router.get("/messages/{message_id}", response_model=EmailMessageResponse)
# async def get_message_by_id(
#     message_id: int,
#     db: AsyncSession = Depends(get_db),
#     user_service: UserService = Depends(UserService.get_instance)
# ):
#     email_service = EmailService(db)
#     try:
#         message = await email_service.get_message_by_id(message_id)
#         if not message:
#             raise HTTPException(status_code=404, detail="Message not found")
#         # Проверяем, принадлежит ли сообщение потоку текущего пользователя
#         thread = await email_service.get_thread_by_id(message.thread_id)
#         if not thread or thread.user_id != user_service.get_current_user().id:
#             raise HTTPException(status_code=403, detail="Not authorized to access this message")
#         return message
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
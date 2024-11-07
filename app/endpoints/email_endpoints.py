# app/endpoints/email_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.email_service import EmailService
from app.schemas.email_message_schema import EmailMessageCreate, EmailMessageResponse
from app.schemas.email_thread_schema import EmailThreadCreate, EmailThreadResponse, ThreadStatus
from app.core.dependency import get_db, get_current_user
from app.models.user import User

router = APIRouter(prefix="/email", tags=["email"])

# Эндпоинт для создания нового email-потока
@router.post("/gmail/threads/", response_model=EmailThreadResponse)
async def create_thread(
    thread_data: EmailThreadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    email_service = EmailService(db)
    try:
        # Устанавливаем текущего пользователя как владельца потока
        thread_data.user_id = current_user.id
        thread = await email_service.create_email_thread(thread_data)
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
        # Проверяем, принадлежит ли поток текущему пользователю
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

# Эндпоинт для получения отдельного сообщения по его ID
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

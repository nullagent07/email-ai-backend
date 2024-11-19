# app/services/oauth_service.py

# sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import Lock
import asyncio
import time
from sqlalchemy import select, and_
from fastapi import HTTPException, Depends, status

# repositories
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository

# models
from app.models.oauth_credentials import OAuthCredentials

# core
from app.core.dependency import get_db

# other
from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID
from typing import Dict, Any

class OAuthCredentialsService:
    _instance = None
    _lock = asyncio.Lock()
    _credentials_cache = {}  # Кэш для хранения учетных данных
    _cache_lock = asyncio.Lock()

    def __init__(self, db: AsyncSession):
        self.oauth_credentials_repo = OAuthCredentialsRepository(db)
        self.db = db
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_cache())

    @classmethod
    async def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'OAuthCredentialsService':
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = cls(db)
        return cls._instance
    
    async def _cleanup_expired_cache(self):
        """Периодически очищает устаревшие записи из кэша"""
        while True:
            try:
                async with self._cache_lock:
                    current_time = time.time()
                    expired_keys = [
                        key for key, value in self._credentials_cache.items()
                        if current_time - value['timestamp'] > 3600  # 1 час
                    ]
                    for key in expired_keys:
                        del self._credentials_cache[key]
            except Exception as e:
                print(f"Error in cache cleanup: {str(e)}")
            await asyncio.sleep(300)  # Проверяем каждые 5 минут

    async def update_oauth_credentials(
        self, 
        user_id: int, 
        provider: str,
        access_token: str,
        refresh_token: str,
        expires_in: datetime,
        email: str,
        provider_data: Dict[str, Any]
    ) -> OAuthCredentials:
        """Обновляет или создает учетные данные OAuth"""
        try:
            # Проверяем существующие учетные данные в кэше
            cache_key = f"{user_id}_{provider}"
            async with self._cache_lock:
                cached_creds = self._credentials_cache.get(cache_key)
                if cached_creds and not self._is_token_expired(cached_creds['credentials']):
                    return cached_creds['credentials']

            # Создаем или обновляем учетные данные в БД
            oauth_credentials = await self.oauth_credentials_repo.get_by_user_id_and_provider(user_id, provider)

            if oauth_credentials:
                # Обновляем существующие учетные данные
                oauth_credentials.access_token = access_token
                oauth_credentials.refresh_token = refresh_token or oauth_credentials.refresh_token
                oauth_credentials.expires_in = expires_in
                oauth_credentials.email = email
                oauth_credentials.provider_data = provider_data
                oauth_credentials.updated_at = datetime.utcnow()
                await self.oauth_credentials_repo.update(oauth_credentials)
            else:
                # Создаем новые учетные данные
                oauth_credentials = OAuthCredentials(
                    user_id=user_id,
                    provider=provider,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=expires_in,
                    email=email,
                    provider_data=provider_data
                )
                await self.oauth_credentials_repo.create(oauth_credentials)

            # Обновляем кэш
            async with self._cache_lock:
                self._credentials_cache[cache_key] = {
                    'credentials': oauth_credentials,
                    'timestamp': time.time()
                }

            return oauth_credentials

        except Exception as e:
            print(f"Error updating OAuth credentials: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update OAuth credentials"
            )

    def _is_token_expired(self, credentials: OAuthCredentials) -> bool:
        """Проверяет, истек ли срок действия токена"""
        if not credentials.expires_in:
            return True
        return datetime.utcnow() >= credentials.expires_in

    async def get_oauth_credentials_by_user_id_and_provider(self, user_id: UUID, provider: str) -> Optional[OAuthCredentials]:
        """Получает учетные данные OAuth из кэша или БД"""
        try:
            # Проверяем кэш
            cache_key = f"{user_id}_{provider}"
            async with self._cache_lock:
                cached_creds = self._credentials_cache.get(cache_key)
                if cached_creds and not self._is_token_expired(cached_creds['credentials']):
                    return cached_creds['credentials']

            # Получаем из БД
            oauth_credentials = await self.oauth_credentials_repo.get_by_user_id_and_provider(user_id, provider)

            if oauth_credentials:
                # Обновляем кэш
                async with self._cache_lock:
                    self._credentials_cache[cache_key] = {
                        'credentials': oauth_credentials,
                        'timestamp': time.time()
                    }

            return oauth_credentials

        except Exception as e:
            print(f"Error getting OAuth credentials: {str(e)}")
            return None

    async def get_oauth_credentials_by_email_and_provider(self, email: str, provider: str) -> Optional[OAuthCredentials]:
        """
        Получает OAuth credentials по email пользователя
        
        Args:
            email: Email пользователя
            
        Returns:
            Optional[OAuthCredentials]: Объект с учетными данными или None
        """
        return await self.oauth_credentials_repo.get_by_email_and_provider(email, provider)

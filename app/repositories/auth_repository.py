from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.oauth_credentials import OAuthCredentials


class AuthRepository:
    def __init__(self, db_session: AsyncSession):
        self.session = db_session
    
    async def get_oauth_credentials(self, email: str, provider: str) -> OAuthCredentials:
        query = select(OAuthCredentials).where(
            OAuthCredentials.email == email,
            OAuthCredentials.provider == provider
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_oauth_credentials(
        self, 
        credentials: OAuthCredentials, 
        access_token: str, 
        refresh_token: str | None,
        expires_at: datetime
    ) -> OAuthCredentials:
        credentials.access_token = access_token
        credentials.refresh_token = refresh_token
        credentials.expires_at = expires_at
        await self.session.commit()
        await self.session.refresh(credentials)
        return credentials
    
    async def create_user_with_oauth(
        self, 
        user_data: User, 
        credentials_data: OAuthCredentials
    ) -> User:
        # Создаем пользователя
        user = User(**user_data.model_dump())
        self.session.add(user)
        await self.session.flush()
        
        # Создаем OAuth credentials
        oauth_creds = OAuthCredentials(
            user_id=user.id,
            **credentials_data.model_dump()
        )
        self.session.add(oauth_creds)
        await self.session.commit()
        
        return user 
    
    async def update_user_password(self, user_id: int, password_hash: str) -> User:
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.password_hash = password_hash
            await self.session.commit()
            await self.session.refresh(user)
        
        return user
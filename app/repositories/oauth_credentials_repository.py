# app/repositories/oauth_credentials_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.oauth_credentials import OAuthCredentials

class OAuthCredentialsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id_and_provider(self, user_id: int, provider: str) -> OAuthCredentials:
        result = await self.db.execute(
            select(OAuthCredentials).filter(
                OAuthCredentials.user_id == user_id,
                OAuthCredentials.provider == provider
            )
        )
        return result.scalars().first()

    async def get_by_email_and_provider(self, email: str, provider: str) -> OAuthCredentials:
        result = await self.db.execute(
            select(OAuthCredentials).filter(
                OAuthCredentials.email == email,
                OAuthCredentials.provider == provider
            )
        )
        return result.scalars().first()

    async def create(self, oauth_credentials: OAuthCredentials) -> OAuthCredentials:
        self.db.add(oauth_credentials)
        await self.db.commit()
        await self.db.refresh(oauth_credentials)
        return oauth_credentials

    async def update(self, oauth_credentials: OAuthCredentials) -> OAuthCredentials:
        await self.db.merge(oauth_credentials)
        await self.db.commit()
        return oauth_credentials

    async def delete(self, oauth_credentials: OAuthCredentials):
        await self.db.delete(oauth_credentials)
        await self.db.commit()

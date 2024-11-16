from app.models.assistant_profile import AssistantProfile
from app.repositories.assistant_profile_repository import AssistantProfileRepository
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_app_settings
from fastapi import Depends
from app.core.dependency import get_db
from uuid import UUID
settings = get_app_settings()

class AssistantProfileService:
    def __init__(self, db: AsyncSession):
        self.assistant_repo = AssistantProfileRepository(db)
    
    @classmethod
    def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'AssistantProfileService':
        return cls(db)

    async def create_assistant_profile(self, 
                                       assistant_id: str, 
                                       user_id: UUID, 
                                       assistant_description: str) -> AssistantProfile:
        """Сохраняет профиль ассистента и email-тред в базе данных."""
        new_assistant_profile = AssistantProfile(
            id=assistant_id,
            user_id=user_id,
            description=assistant_description
        )

        return await self.assistant_repo.create_assistant_profile(new_assistant_profile)
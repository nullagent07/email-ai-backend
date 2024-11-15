from app.models.assistant_profile import AssistantProfile
from app.schemas.email_thread_schema import EmailThreadCreate
from app.repositories.email_thread_repository import EmailThreadRepository
from app.repositories.assistant_profile_repository import AssistantProfileRepository
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_app_settings

settings = get_app_settings()

class AssistantProfileService:
    def __init__(self, db: AsyncSession):
        self.assistant_repo = AssistantProfileRepository(db)
        self.thread_repo = EmailThreadRepository(db)

    async def create_assistant_profile(self, assistant_id: str, thread_data: EmailThreadCreate) -> AssistantProfile:
        """Сохраняет профиль ассистента и email-тред в базе данных."""
        assistant_profile = AssistantProfile(
            id=assistant_id,
            user_id=thread_data.user_id,
            name=thread_data.recipient_name,
            description=thread_data.assistant
        )

        return await self.assistant_repo.create_assistant_profile(assistant_profile)
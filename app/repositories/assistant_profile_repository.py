from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.assistant_profile import AssistantProfile
from app.models.open_ai_thread import OpenAiThread
from typing import Optional, List
from uuid import UUID

class AssistantProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create_assistant_profile(self, assistant: AssistantProfile) -> AssistantProfile:
        self.db.add(assistant)
        await self.db.commit()
        await self.db.refresh(assistant)
        return assistant
        
    async def get_assistant_by_id(self, assistant_id: str) -> Optional[AssistantProfile]:
        result = await self.db.execute(
            select(AssistantProfile).filter(AssistantProfile.id == assistant_id)
        )
        return result.scalars().first()
        
    async def get_assistants_by_user_id(self, user_id: UUID) -> List[AssistantProfile]:
        result = await self.db.execute(
            select(AssistantProfile).filter(AssistantProfile.user_id == user_id)
        )
        return result.scalars().all()
        
    async def get_assistant_by_thread(self, thread_id: str) -> Optional[AssistantProfile]:
        result = await self.db.execute(
            select(AssistantProfile)
            .join(EmailThread)
            .filter(EmailThread.id == thread_id)
        )
        return result.scalars().first()
        
    async def update_assistant_profile(self, assistant: AssistantProfile) -> AssistantProfile:
        await self.db.merge(assistant)
        await self.db.commit()
        return assistant
        
    async def delete_assistant_profile(self, assistant_id: str) -> bool:
        result = await self.db.execute(
            select(AssistantProfile).filter(AssistantProfile.id == assistant_id)
        )
        assistant = result.scalars().first()
        if assistant:
            await self.db.delete(assistant)
            await self.db.commit()
            return True
        return False
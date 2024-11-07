from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.assistant import AssistantProfile
from typing import Optional
from uuid import UUID

class AssistantRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create_assistant_profile(self, assistant: AssistantProfile) -> AssistantProfile:
        self.db.add(assistant)
        await self.db.commit()
        await self.db.refresh(assistant)
        return assistant
        
    async def get_assistant_by_thread_id(self, thread_id: UUID) -> Optional[AssistantProfile]:
        result = await self.db.execute(
            select(AssistantProfile).filter(AssistantProfile.thread_id == thread_id)
        )
        return result.scalars().first()
        
    async def update_assistant_profile(self, assistant: AssistantProfile) -> AssistantProfile:
        await self.db.merge(assistant)
        await self.db.commit()
        return assistant
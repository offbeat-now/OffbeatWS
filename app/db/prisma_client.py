from typing import Optional
from prisma import Prisma
from core.config import get_settings
from utils.logger import get_logger

logger = get_logger("prisma")

class PrismaManager:
    """Prisma client manager"""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[Prisma] = None
    
    async def get_client(self) -> Prisma:
        """Get Prisma client instance"""
        if not self._client:
            self._client = Prisma()
            await self._client.connect()
            logger.info("Connected to Prisma client")
        
        return self._client
    
    async def disconnect(self):
        """Disconnect Prisma client"""
        if self._client:
            await self._client.disconnect()
            self._client = None
            logger.info("Disconnected from Prisma client")

# Global Prisma manager
prisma_manager = PrismaManager()

async def get_prisma_client() -> Prisma:
    """FastAPI dependency for Prisma client"""
    return await prisma_manager.get_client()
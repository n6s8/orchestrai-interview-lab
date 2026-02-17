from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models.schemas import MemoryEntry

class MemoryInterface(ABC):
    @abstractmethod
    async def add(self, content: str, metadata: Dict[str, Any] = {}) -> str:
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        pass
    
    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        pass
    
    @abstractmethod
    async def get_session_history(self, session_id: str, limit: int = 50) -> List[MemoryEntry]:
        pass

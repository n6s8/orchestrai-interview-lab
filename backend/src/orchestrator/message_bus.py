from typing import Dict, List, Callable, Any
from asyncio import Queue
from ..models.schemas import AgentMessage
from ..models.enums import AgentType, MessageType
import asyncio

class MessageBus:
    def __init__(self):
        self.subscribers: Dict[AgentType, List[Callable]] = {}
        self.message_queue: Queue = Queue()
        self.message_history: List[AgentMessage] = []
        self.broadcast_callbacks: List[Callable] = []
    
    def subscribe(self, agent_type: AgentType, callback: Callable):
        if agent_type not in self.subscribers:
            self.subscribers[agent_type] = []
        self.subscribers[agent_type].append(callback)
    
    def subscribe_broadcast(self, callback: Callable):
        self.broadcast_callbacks.append(callback)
    
    async def publish(self, message: AgentMessage):
        self.message_history.append(message)
        await self.message_queue.put(message)
        
        for callback in self.broadcast_callbacks:
            asyncio.create_task(callback(message))
        
        if message.receiver:
            if message.receiver in self.subscribers:
                for callback in self.subscribers[message.receiver]:
                    asyncio.create_task(callback(message))
        else:
            for agent_callbacks in self.subscribers.values():
                for callback in agent_callbacks:
                    asyncio.create_task(callback(message))
    
    async def get_message(self, timeout: float = None) -> AgentMessage:
        if timeout:
            return await asyncio.wait_for(self.message_queue.get(), timeout=timeout)
        return await self.message_queue.get()
    
    def get_history(
        self,
        sender: AgentType = None,
        receiver: AgentType = None,
        message_type: MessageType = None,
        limit: int = 50
    ) -> List[AgentMessage]:
        filtered = self.message_history
        
        if sender:
            filtered = [m for m in filtered if m.sender == sender]
        if receiver:
            filtered = [m for m in filtered if m.receiver == receiver]
        if message_type:
            filtered = [m for m in filtered if m.message_type == message_type]
        
        return filtered[-limit:] if limit else filtered
    
    def clear_history(self):
        self.message_history.clear()
    
    async def broadcast(self, message: AgentMessage):
        message.receiver = None
        await self.publish(message)

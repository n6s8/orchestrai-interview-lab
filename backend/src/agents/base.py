from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from ..models.schemas import InterviewContext, AgentResponse, AgentMessage
from ..models.enums import AgentType, MessageType
import httpx
import json
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

class BaseAgent(ABC):
    def __init__(
        self,
        agent_type: AgentType,
        role_prompt: str,
        model: str = "llama3-8b-8192",
        use_groq: bool = True
    ):
        self.agent_type = agent_type
        self.role_prompt = role_prompt
        self.model = model
        self.use_groq = use_groq
        self.tools: List[Any] = []
        self.memory_interface: Optional[Any] = None
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        
    @abstractmethod
    async def act(self, context: InterviewContext) -> AgentResponse:
        pass
    
    async def call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.use_groq:
            return await self._call_groq(prompt, system_prompt)
        else:
            return await self._call_ollama(prompt, system_prompt)
    
    async def _call_groq(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        api_key = self.groq_api_key
        
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in .env file")
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                print(f"Groq API Error: {response.status_code}")
                print(f"Response: {response.text}")
                response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "phi3:mini")
        
        url = f"{ollama_url}/api/generate"
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "model": ollama_model,
            "prompt": full_prompt,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()["response"]
    
    async def call_llm_stream(self, prompt: str, system_prompt: Optional[str] = None):
        if self.use_groq:
            async for chunk in self._call_groq_stream(prompt, system_prompt):
                yield chunk
        else:
            async for chunk in self._call_ollama_stream(prompt, system_prompt):
                yield chunk
    
    async def _call_groq_stream(self, prompt: str, system_prompt: Optional[str] = None):
        api_key = self.groq_api_key
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "stream": True
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if data["choices"][0]["delta"].get("content"):
                                yield data["choices"][0]["delta"]["content"]
                        except:
                            continue
    
    async def _call_ollama_stream(self, prompt: str, system_prompt: Optional[str] = None):
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "phi3:mini")
        
        url = f"{ollama_url}/api/generate"
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "model": ollama_model,
            "prompt": full_prompt,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        data = json.loads(line)
                        if not data.get("done", False):
                            yield data.get("response", "")
    
    def create_message(
        self,
        receiver: Optional[AgentType],
        message_type: MessageType,
        content: str,
        payload: Dict[str, Any] = {},
        confidence: float = 0.0
    ) -> AgentMessage:
        return AgentMessage(
            id=f"{self.agent_type}_{datetime.utcnow().timestamp()}",
            sender=self.agent_type,
            receiver=receiver,
            message_type=message_type,
            content=content,
            payload=payload,
            confidence=confidence
        )
    
    async def retrieve_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if self.memory_interface:
            return await self.memory_interface.search(query, limit)
        return []
    
    async def store_memory(self, content: str, metadata: Dict[str, Any] = {}):
        if self.memory_interface:
            await self.memory_interface.add(content, metadata)
    
    def register_tool(self, tool: Any):
        self.tools.append(tool)
    
    def set_memory_interface(self, memory_interface: Any):
        self.memory_interface = memory_interface
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from .interface import MemoryInterface
from ..models.schemas import MemoryEntry
import uuid
from datetime import datetime

class VectorStore(MemoryInterface):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "interview_memory",
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_size: int = 384
    ):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.encoder = SentenceTransformer(embedding_model)
        self.vector_size = vector_size
        self._ensure_collection()
    
    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        exists = any(col.name == self.collection_name for col in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
    
    async def add(self, content: str, metadata: Dict[str, Any] = {}) -> str:
        entry_id = str(uuid.uuid4())
        embedding = self.encoder.encode(content).tolist()
        
        point = PointStruct(
            id=entry_id,
            vector=embedding,
            payload={
                "content": content,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": metadata.get("session_id", "")
            }
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        return entry_id
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.encoder.encode(query).tolist()
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        
        return [
            {
                "id": hit.id,
                "content": hit.payload.get("content", ""),
                "metadata": hit.payload.get("metadata", {}),
                "score": hit.score,
                "timestamp": hit.payload.get("timestamp", "")
            }
            for hit in results
        ]
    
    async def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        result = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[entry_id]
        )
        
        if not result:
            return None
        
        point = result[0]
        return MemoryEntry(
            id=point.id,
            session_id=point.payload.get("session_id", ""),
            content=point.payload.get("content", ""),
            metadata=point.payload.get("metadata", {}),
            timestamp=datetime.fromisoformat(point.payload.get("timestamp", ""))
        )
    
    async def delete(self, entry_id: str) -> bool:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[entry_id]
        )
        return True
    
    async def count_candidate_sessions(self, candidate_name: str) -> int:
        """Count unique past interview sessions for a specific candidate using metadata filter."""
        try:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            results, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.candidate",
                            match=MatchValue(value=candidate_name)
                        )
                    ]
                ),
                limit=1000,
                with_payload=True
            )
            session_ids = set()
            for point in results:
                sid = point.payload.get("metadata", {}).get("session_id", "")
                if sid:
                    session_ids.add(sid)
            return len(session_ids)
        except Exception as e:
            print(f"⚠️ count_candidate_sessions error: {e}")
            return 0

    async def get_session_history(self, session_id: str, limit: int = 50) -> List[MemoryEntry]:
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter={
                "must": [
                    {"key": "session_id", "match": {"value": session_id}}
                ]
            },
            limit=limit
        )[0]
        
        return [
            MemoryEntry(
                id=point.id,
                session_id=point.payload.get("session_id", ""),
                content=point.payload.get("content", ""),
                metadata=point.payload.get("metadata", {}),
                timestamp=datetime.fromisoformat(point.payload.get("timestamp", ""))
            )
            for point in results
        ]
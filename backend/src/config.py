from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3:mini"
    GROQ_API_KEY: str = ""
    USE_GROQ: bool = True
    GROQ_MODEL: str = "llama3-8b-8192"
    
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "interview_memory"
    
    DATABASE_URL: str = "sqlite:///./interview_data.db"
    
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    
    MAX_RETRIEVAL_RESULTS: int = 5
    CONFIDENCE_THRESHOLD: float = 0.7
    
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

def get_settings() -> Settings:
    return Settings()
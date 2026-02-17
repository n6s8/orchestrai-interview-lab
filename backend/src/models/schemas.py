from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .enums import InterviewState, AgentType, MessageType, DifficultyLevel
from datetime import datetime

class AgentMessage(BaseModel):
    id: str
    sender: AgentType
    receiver: Optional[AgentType] = None
    message_type: MessageType
    content: str
    payload: Dict[str, Any] = {}
    confidence: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class InterviewContext(BaseModel):
    session_id: str
    candidate_name: str
    current_state: InterviewState = InterviewState.INIT
    candidate_resume: Optional[str] = None
    skill_profile: Optional[Dict[str, Any]] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    current_question: Optional[Dict[str, Any]] = None
    candidate_answers: List[str] = []
    messages: List[AgentMessage] = []
    current_score: Dict[str, Any] = {}
    interview_plan: Optional[Dict[str, Any]] = None
    questions_asked: int = 0
    total_questions: int = 3

class AgentResponse(BaseModel):
    agent_type: AgentType
    content: str
    confidence: float = 0.0
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = {}

class Question(BaseModel):
    id: str
    title: str
    difficulty: str
    category: str
    problem_statement: str
    examples: List[Dict[str, str]] = []
    constraints: List[str] = []
    hints: List[str] = []
    optimal_approach: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None

class CandidateAnswer(BaseModel):
    question_id: str
    code: str
    language: str = "python"
    explanation: Optional[str] = None

class EvaluationResult(BaseModel):
    question_id: str
    correctness_score: float
    approach_score: float
    code_quality_score: float
    overall_score: float
    feedback: str
    suggested_improvements: List[str] = []

class FinalReport(BaseModel):
    session_id: str
    candidate_name: str
    overall_score: float
    dsa_score: float
    code_quality_score: float
    recommendation: str
    detailed_feedback: str
    strengths: List[str] = []
    improvements: List[str] = []

class MemoryEntry(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None

class ToolCallResult(BaseModel):
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
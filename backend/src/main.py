from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import get_settings
from .memory.vector_store import VectorStore
from .orchestrator.message_bus import MessageBus
from .orchestrator.state_machine import StateMachine
from .agents.recruiter import RecruiterAgent
from .agents.dsa_interviewer import DSAInterviewerAgent
from .agents.code_evaluator import CodeEvaluatorAgent
from .models.schemas import InterviewContext, AgentMessage
from .models.enums import InterviewState, AgentType, MessageType
from typing import Dict, List
import uuid
import json

settings = get_settings()

message_bus = MessageBus()
state_machine = StateMachine()
vector_store = None
agents: Dict[AgentType, any] = {}
active_sessions: Dict[str, InterviewContext] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_store, agents

    vector_store = VectorStore(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection_name=settings.QDRANT_COLLECTION,
        embedding_model=settings.EMBEDDING_MODEL,
        vector_size=settings.EMBEDDING_DIM
    )

    use_groq = settings.USE_GROQ
    model = settings.GROQ_MODEL if use_groq else settings.OLLAMA_MODEL

    recruiter = RecruiterAgent(use_groq=use_groq, model=model)
    recruiter.set_memory_interface(vector_store)
    agents[AgentType.RECRUITER] = recruiter

    dsa_interviewer = DSAInterviewerAgent(use_groq=use_groq, model=model)
    dsa_interviewer.set_memory_interface(vector_store)
    agents[AgentType.DSA_INTERVIEWER] = dsa_interviewer

    code_evaluator = CodeEvaluatorAgent(use_groq=use_groq, model=model)
    agents[AgentType.CODE_EVALUATOR] = code_evaluator

    print(f"✅ OrchestrAI started | LLM: {'Groq' if use_groq else 'Ollama'} | Model: {model}")

    yield

app = FastAPI(title="OrchestrAI Interview Lab", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "OrchestrAI Interview Lab", "version": "0.2.0", "status": "running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "llm_provider": "Groq" if settings.USE_GROQ else "Ollama",
        "model": settings.GROQ_MODEL if settings.USE_GROQ else settings.OLLAMA_MODEL,
        "agents": [a.value for a in agents.keys()],
        "active_sessions": len(active_sessions)
    }

@app.post("/interview/start")
async def start_interview(candidate_name: str, resume: str):
    session_id = str(uuid.uuid4())

    context = InterviewContext(
        session_id=session_id,
        candidate_name=candidate_name,
        current_state=InterviewState.RESUME_ANALYSIS,
        candidate_resume=resume
    )

    active_sessions[session_id] = context

    recruiter = agents.get(AgentType.RECRUITER)
    if recruiter:
        response = await recruiter.act(context)
        message = recruiter.create_message(
            receiver=None,
            message_type=MessageType.EVALUATION,
            content=response.content,
            payload=response.metadata,
            confidence=response.confidence
        )
        context.messages.append(message)
        await message_bus.publish(message)

    return {
        "session_id": session_id,
        "status": "started",
        "current_state": context.current_state.value,
        "candidate": candidate_name,
        "skill_profile": context.skill_profile,
        "difficulty": context.difficulty_level.value if context.difficulty_level else "MEDIUM"
    }

@app.post("/interview/{session_id}/next")
async def next_phase(session_id: str):
    """Move to DSA phase and get first question"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    context = active_sessions[session_id]
    context.current_state = InterviewState.DSA_PHASE
    context.current_question = None  # Reset for new question

    dsa = agents.get(AgentType.DSA_INTERVIEWER)
    if dsa:
        response = await dsa.act(context)
        message = dsa.create_message(
            receiver=None,
            message_type=MessageType.QUESTION,
            content=response.content,
            payload=response.metadata,
            confidence=response.confidence
        )
        context.messages.append(message)
        await message_bus.publish(message)

    return {
        "session_id": session_id,
        "state": context.current_state.value,
        "question": context.current_question
    }

@app.post("/interview/{session_id}/answer")
async def submit_answer(session_id: str, answer: str):
    """Submit code answer, get evaluation from DSA + Code Evaluator agents"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    context = active_sessions[session_id]
    context.candidate_answers.append(answer)

    responses = []

    # DSA Interviewer evaluates approach
    dsa = agents.get(AgentType.DSA_INTERVIEWER)
    if dsa and context.current_question:
        dsa_response = await dsa.evaluate_answer(context)
        msg = dsa.create_message(
            receiver=None,
            message_type=MessageType.EVALUATION,
            content=dsa_response.content,
            payload=dsa_response.metadata,
            confidence=dsa_response.confidence
        )
        context.messages.append(msg)
        await message_bus.publish(msg)
        responses.append({"agent": "DSA_INTERVIEWER", "content": dsa_response.content})

    # Code Evaluator does deep code review
    code_eval = agents.get(AgentType.CODE_EVALUATOR)
    if code_eval:
        eval_response = await code_eval.act(context)
        msg = code_eval.create_message(
            receiver=None,
            message_type=MessageType.EVALUATION,
            content=eval_response.content,
            payload=eval_response.metadata,
            confidence=eval_response.confidence
        )
        context.messages.append(msg)
        await message_bus.publish(msg)
        responses.append({"agent": "CODE_EVALUATOR", "content": eval_response.content})

    return {
        "session_id": session_id,
        "evaluations": responses,
        "scores": context.current_score
    }

@app.post("/interview/{session_id}/hint")
async def get_hint(session_id: str):
    """Get a hint for the current question"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    context = active_sessions[session_id]
    question = context.current_question

    if not question:
        raise HTTPException(status_code=400, detail="No active question")

    hints = question.get("hints", [])
    hint_index = context.current_score.get("hints_used", 0)

    if hint_index < len(hints):
        hint = hints[hint_index]
        context.current_score["hints_used"] = hint_index + 1
    else:
        hint = "Try thinking about the time complexity. Can you do better than O(n²)?"

    return {"hint": hint, "hints_remaining": max(0, len(hints) - hint_index - 1)}

@app.get("/interview/{session_id}")
async def get_interview_status(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    context = active_sessions[session_id]
    return {
        "session_id": session_id,
        "candidate": context.candidate_name,
        "current_state": context.current_state.value,
        "difficulty": context.difficulty_level.value if context.difficulty_level else "MEDIUM",
        "messages_count": len(context.messages),
        "scores": context.current_score,
        "current_question": context.current_question
    }

@app.get("/interview/{session_id}/messages")
async def get_interview_messages(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    context = active_sessions[session_id]
    return {
        "session_id": session_id,
        "messages": [msg.dict() for msg in context.messages]
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    async def broadcast_handler(message: AgentMessage):
        try:
            await websocket.send_json({"type": "agent_message", "data": message.dict()})
        except:
            pass

    message_bus.subscribe_broadcast(broadcast_handler)

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "ack", "message": "received"})
    except WebSocketDisconnect:
        pass
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from .config import get_settings
from .memory.vector_store import VectorStore
from .orchestrator.message_bus import MessageBus
from .orchestrator.state_machine import StateMachine
from .agents.recruiter import RecruiterAgent
from .agents.dsa_interviewer import DSAInterviewerAgent
from .agents.code_evaluator import CodeEvaluatorAgent
from .agents.system_design import SystemDesignAgent
from .agents.behavioral import BehavioralAgent
from .agents.critic import CriticAgent
from .agents.final_decision import FinalDecisionAgent
from .agents.hallucination_detector import HallucinationDetectorAgent
from .models.schemas import InterviewContext, AgentMessage
from .models.enums import InterviewState, AgentType, MessageType
from typing import Dict, List
import uuid
import json
import io
from datetime import datetime
import os

settings = get_settings()
message_bus = MessageBus()
state_machine = StateMachine()
vector_store = None
agents: Dict[AgentType, any] = {}
active_sessions: Dict[str, InterviewContext] = {}
interview_history: List[Dict] = []

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

    agent_classes = [
        (AgentType.RECRUITER, RecruiterAgent),
        (AgentType.DSA_INTERVIEWER, DSAInterviewerAgent),
        (AgentType.CODE_EVALUATOR, CodeEvaluatorAgent),
        (AgentType.SYSTEM_DESIGN, SystemDesignAgent),
        (AgentType.BEHAVIORAL, BehavioralAgent),
        (AgentType.CRITIC, CriticAgent),
        (AgentType.FINAL_DECISION, FinalDecisionAgent),
        (AgentType.HALLUCINATION_DETECTOR, HallucinationDetectorAgent),
    ]

    for agent_type, AgentClass in agent_classes:
        agent = AgentClass(use_groq=use_groq, model=model)
        agent.set_memory_interface(vector_store)
        agents[agent_type] = agent

    print(f"✅ OrchestrAI Day 4 | {len(agents)} agents loaded | Model: {model}")
    yield

app = FastAPI(title="OrchestrAI Interview Lab", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def _publish_agent_message(agent, context, msg_type, content, metadata, confidence):
    msg = agent.create_message(
        receiver=None,
        message_type=msg_type,
        content=content,
        payload=metadata,
        confidence=confidence
    )
    context.messages.append(msg)
    await message_bus.publish(msg)

    await vector_store.add(
        content=f"{agent.agent_type.value}: {content}",
        metadata={
            "session_id": context.session_id,
            "agent": agent.agent_type.value,
            "candidate": context.candidate_name,
            "timestamp": datetime.utcnow().isoformat(),
            "type": msg_type.value
        }
    )
    return msg

@app.get("/")
async def root():
    return {"message": "OrchestrAI Interview Lab", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "model": settings.GROQ_MODEL if settings.USE_GROQ else settings.OLLAMA_MODEL,
        "agents": [a.value for a in agents.keys()],
        "active_sessions": len(active_sessions),
        "memory_enabled": vector_store is not None
    }

@app.post("/upload-resume")
async def upload_resume_pdf(file: UploadFile = File(...)):
    """Accept a PDF file and extract its text content."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    try:
        import PyPDF2
        contents = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text.strip())
        full_text = "\n\n".join(text_parts)
        if not full_text.strip():
            raise HTTPException(422, "Could not extract text from this PDF. It may be a scanned image-only PDF.")
        return {"text": full_text, "pages": len(pdf_reader.pages)}
    except ImportError:
        raise HTTPException(500, "PyPDF2 not installed. Run: pip install PyPDF2")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to parse PDF: {str(e)}")

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

    # FIX: Run recruiter FIRST while skill_profile is empty.
    # If we add past_sessions BEFORE this, skill_profile becomes truthy and
    # recruiter calls generate_interview_plan() instead of analyze_resume() — causing blank fields.
    recruiter = agents[AgentType.RECRUITER]
    response = await recruiter.act(context)
    await _publish_agent_message(
        recruiter, context, MessageType.EVALUATION,
        response.content, response.metadata, response.confidence
    )

    # FIX: Count past sessions AFTER resume analysis, using metadata filter (not semantic search).
    # Semantic search returns top-N matches from ANY candidate, giving wrong counts.
    past_count = await vector_store.count_candidate_sessions(candidate_name)
    # Subtract the current session's messages we just wrote above
    past_count = max(0, past_count - 1)

    if past_count > 0:
        context.skill_profile["past_sessions"] = past_count

    return {
        "session_id": session_id,
        "status": "started",
        "current_state": context.current_state.value,
        "candidate": candidate_name,
        "skill_profile": context.skill_profile,
        "difficulty": context.difficulty_level.value,
        "past_interviews_found": past_count
    }

@app.post("/interview/{session_id}/dsa/start")
async def start_dsa(session_id: str):
    context = _get_session(session_id)
    context.current_state = InterviewState.DSA_PHASE
    context.current_question = None

    dsa = agents[AgentType.DSA_INTERVIEWER]
    response = await dsa.act(context)
    await _publish_agent_message(
        dsa, context, MessageType.QUESTION,
        response.content, response.metadata, response.confidence
    )

    return {"session_id": session_id, "state": "DSA_PHASE", "question": context.current_question}

@app.post("/interview/{session_id}/dsa/answer")
async def submit_dsa_answer(session_id: str, answer: str):
    context = _get_session(session_id)
    context.candidate_answers.append(answer)

    results = []

    dsa = agents[AgentType.DSA_INTERVIEWER]
    dsa_resp = await dsa.evaluate_answer(context)
    await _publish_agent_message(
        dsa, context, MessageType.EVALUATION,
        dsa_resp.content, dsa_resp.metadata, dsa_resp.confidence
    )
    results.append({"agent": "DSA_INTERVIEWER", "content": dsa_resp.content, "metadata": dsa_resp.metadata})

    code_eval = agents[AgentType.CODE_EVALUATOR]
    eval_resp = await code_eval.act(context)
    await _publish_agent_message(
        code_eval, context, MessageType.EVALUATION,
        eval_resp.content, eval_resp.metadata, eval_resp.confidence
    )
    results.append({"agent": "CODE_EVALUATOR", "content": eval_resp.content, "metadata": eval_resp.metadata})

    return {"evaluations": results, "scores": context.current_score}

@app.post("/interview/{session_id}/dsa/hint")
async def get_dsa_hint(session_id: str):
    context = _get_session(session_id)
    question = context.current_question
    if not question:
        raise HTTPException(400, "No active question")
    hints = question.get("hints", [])
    used = context.current_score.get("hints_used", 0)
    hint = hints[used] if used < len(hints) else "Think about the optimal time complexity."
    context.current_score["hints_used"] = used + 1
    return {"hint": hint, "hints_remaining": max(0, len(hints) - used - 1)}

@app.post("/interview/{session_id}/system-design/start")
async def start_system_design(session_id: str):
    context = _get_session(session_id)
    context.current_state = InterviewState.SYSTEM_DESIGN_PHASE
    context.current_question = None

    sd = agents[AgentType.SYSTEM_DESIGN]
    response = await sd.act(context)
    await _publish_agent_message(
        sd, context, MessageType.QUESTION,
        response.content, response.metadata, response.confidence
    )

    return {"session_id": session_id, "state": "SYSTEM_DESIGN_PHASE", "question": context.current_question}

@app.post("/interview/{session_id}/system-design/answer")
async def submit_system_design(session_id: str, answer: str):
    context = _get_session(session_id)
    context.candidate_answers.append(answer)

    sd = agents[AgentType.SYSTEM_DESIGN]
    response = await sd.evaluate_answer(context)
    await _publish_agent_message(
        sd, context, MessageType.EVALUATION,
        response.content, response.metadata, response.confidence
    )

    return {"evaluation": response.content, "metadata": response.metadata, "scores": context.current_score}

@app.post("/interview/{session_id}/behavioral/start")
async def start_behavioral(session_id: str):
    context = _get_session(session_id)
    context.current_state = InterviewState.BEHAVIORAL_PHASE
    context.current_question = None

    beh = agents[AgentType.BEHAVIORAL]
    response = await beh.act(context)
    await _publish_agent_message(
        beh, context, MessageType.QUESTION,
        response.content, response.metadata, response.confidence
    )

    return {"session_id": session_id, "state": "BEHAVIORAL_PHASE", "question": context.current_question}

@app.post("/interview/{session_id}/behavioral/answer")
async def submit_behavioral(session_id: str, answer: str):
    context = _get_session(session_id)
    context.candidate_answers.append(answer)

    beh = agents[AgentType.BEHAVIORAL]
    response = await beh.evaluate_answer(context)
    await _publish_agent_message(
        beh, context, MessageType.EVALUATION,
        response.content, response.metadata, response.confidence
    )

    return {"evaluation": response.content, "metadata": response.metadata, "scores": context.current_score}

@app.post("/interview/{session_id}/validate")
async def validate_evaluations(session_id: str):
    context = _get_session(session_id)

    detector = agents[AgentType.HALLUCINATION_DETECTOR]
    response = await detector.act(context)
    await _publish_agent_message(
        detector, context, MessageType.EVALUATION,
        response.content, response.metadata, response.confidence
    )

    return {"validation": response.content, "metadata": response.metadata}

@app.post("/interview/{session_id}/debate")
async def run_debate(session_id: str):
    context = _get_session(session_id)
    context.current_state = InterviewState.CROSS_AGENT_DEBATE

    critic = agents[AgentType.CRITIC]
    response = await critic.act(context)
    await _publish_agent_message(
        critic, context, MessageType.EVALUATION,
        response.content, response.metadata, response.confidence
    )

    return {"debate_result": response.content, "metadata": response.metadata, "scores": context.current_score}

@app.post("/interview/{session_id}/final")
async def get_final_decision(session_id: str):
    context = _get_session(session_id)
    context.current_state = InterviewState.FINAL_DECISION

    final = agents[AgentType.FINAL_DECISION]
    response = await final.act(context)
    await _publish_agent_message(
        final, context, MessageType.EVALUATION,
        response.content, response.metadata, response.confidence
    )

    context.current_state = InterviewState.COMPLETED

    decision_data = response.metadata.get("decision", {})

    history_entry = {
        "session_id": session_id,
        "candidate": context.candidate_name,
        "date": datetime.utcnow().isoformat(),
        "recommendation": decision_data.get("recommendation", "pending"),
        "overall_score": decision_data.get("overall_score", 0),
        "difficulty": context.difficulty_level.value,
        "hire_level": decision_data.get("hire_level", ""),
        "score_breakdown": decision_data.get("score_breakdown", {})
    }
    interview_history.append(history_entry)

    return {
        "session_id": session_id,
        "candidate": context.candidate_name,
        "recommendation": decision_data.get("recommendation", "pending"),
        "overall_score": decision_data.get("overall_score", 0),
        "confidence": decision_data.get("confidence", 0),
        "score_breakdown": decision_data.get("score_breakdown", {}),
        "strengths": decision_data.get("strengths", []),
        "concerns": decision_data.get("concerns", []),
        "growth_areas": decision_data.get("growth_areas", []),
        "detailed_feedback": decision_data.get("detailed_feedback", ""),
        "next_steps": decision_data.get("next_steps", ""),
        "hire_level": decision_data.get("hire_level", ""),
        "all_scores": context.current_score
    }

@app.get("/interview/history")
async def get_interview_history():
    return {
        "total_interviews": len(interview_history),
        "interviews": sorted(interview_history, key=lambda x: x["date"], reverse=True)
    }

@app.get("/interview/{session_id}")
async def get_status(session_id: str):
    context = _get_session(session_id)
    return {
        "session_id": session_id,
        "candidate": context.candidate_name,
        "current_state": context.current_state.value,
        "difficulty": context.difficulty_level.value,
        "messages_count": len(context.messages),
        "scores": context.current_score,
        "current_question": context.current_question
    }

@app.get("/interview/{session_id}/messages")
async def get_messages(session_id: str):
    context = _get_session(session_id)
    return {"session_id": session_id, "messages": [m.dict() for m in context.messages]}

@app.get("/interview/{session_id}/memory")
async def search_memory(session_id: str, query: str):
    results = await vector_store.search(query=query, limit=5)
    return {
        "query": query,
        "results": [
            {
                "text": r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"],
                "score": r["score"],
                "metadata": r["metadata"]
            }
            for r in results
        ] if results else []
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    async def broadcast(message: AgentMessage):
        try:
            await websocket.send_json({"type": "agent_message", "data": message.dict()})
        except:
            pass

    message_bus.subscribe_broadcast(broadcast)

    try:
        while True:
            await websocket.receive_text()
            await websocket.send_json({"type": "ack"})
    except WebSocketDisconnect:
        pass

def _get_session(session_id: str) -> InterviewContext:
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")
    return active_sessions[session_id]
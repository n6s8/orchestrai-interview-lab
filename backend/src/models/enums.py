from enum import Enum

class InterviewState(Enum):
    INIT = "init"
    RESUME_ANALYSIS = "resume_analysis"
    DSA_PHASE = "dsa_phase"
    SYSTEM_DESIGN_PHASE = "system_design_phase"
    BEHAVIORAL_PHASE = "behavioral_phase"
    CROSS_AGENT_DEBATE = "cross_agent_debate"
    FINAL_DECISION = "final_decision"
    COMPLETED = "completed"

class AgentType(Enum):
    RECRUITER = "recruiter"
    DSA_INTERVIEWER = "dsa_interviewer"
    CODE_EVALUATOR = "code_evaluator"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    HALLUCINATION_DETECTOR = "hallucination_detector"
    CRITIC = "critic"
    FINAL_DECISION = "final_decision"

class MessageType(Enum):
    QUESTION = "question"
    ANSWER = "answer"
    EVALUATION = "evaluation"
    HINT = "hint"
    FEEDBACK = "feedback"

class DifficultyLevel(Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
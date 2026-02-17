export enum InterviewState {
  INIT = "INIT",
  RESUME_ANALYSIS = "RESUME_ANALYSIS",
  SKILL_PROFILING = "SKILL_PROFILING",
  DSA_PHASE = "DSA_PHASE",
  SYSTEM_DESIGN_PHASE = "SYSTEM_DESIGN_PHASE",
  BEHAVIORAL_PHASE = "BEHAVIORAL_PHASE",
  CODE_EVALUATION = "CODE_EVALUATION",
  CROSS_AGENT_DEBATE = "CROSS_AGENT_DEBATE",
  FINAL_DECISION = "FINAL_DECISION",
  REPORT_GENERATION = "REPORT_GENERATION",
  COMPLETED = "COMPLETED"
}

export enum AgentType {
  RECRUITER = "RECRUITER",
  DSA_INTERVIEWER = "DSA_INTERVIEWER",
  SYSTEM_DESIGN = "SYSTEM_DESIGN",
  BEHAVIORAL = "BEHAVIORAL",
  CODE_EVALUATOR = "CODE_EVALUATOR",
  HALLUCINATION_DETECTOR = "HALLUCINATION_DETECTOR",
  CRITIC = "CRITIC",
  FINAL_DECISION = "FINAL_DECISION"
}

export enum MessageType {
  QUESTION = "QUESTION",
  ANSWER = "ANSWER",
  EVALUATION = "EVALUATION",
  EVALUATION_REQUEST = "EVALUATION_REQUEST",
  DEBATE_CONTRIBUTION = "DEBATE_CONTRIBUTION",
  SCORE_UPDATE = "SCORE_UPDATE",
  STATE_TRANSITION = "STATE_TRANSITION",
  TOOL_CALL = "TOOL_CALL",
  MEMORY_RETRIEVAL = "MEMORY_RETRIEVAL"
}

export interface AgentMessage {
  id: string;
  sender: AgentType;
  receiver: AgentType | null;
  message_type: MessageType;
  content: string;
  payload: Record<string, any>;
  confidence: number;
  timestamp: string;
}

export interface InterviewSession {
  session_id: string;
  candidate: string;
  current_state: InterviewState;
  difficulty: string;
  messages_count: number;
  scores: Record<string, number>;
}

from typing import Dict, List, Callable, Optional
from ..models.enums import InterviewState, AgentType
from ..models.schemas import InterviewContext

class StateMachine:
    def __init__(self):
        self.transitions: Dict[InterviewState, List[InterviewState]] = {
            InterviewState.INIT: [InterviewState.RESUME_ANALYSIS],
            InterviewState.RESUME_ANALYSIS: [InterviewState.SKILL_PROFILING],
            InterviewState.SKILL_PROFILING: [InterviewState.DSA_PHASE],
            InterviewState.DSA_PHASE: [InterviewState.SYSTEM_DESIGN_PHASE, InterviewState.CODE_EVALUATION],
            InterviewState.SYSTEM_DESIGN_PHASE: [InterviewState.BEHAVIORAL_PHASE],
            InterviewState.BEHAVIORAL_PHASE: [InterviewState.CROSS_AGENT_DEBATE],
            InterviewState.CODE_EVALUATION: [InterviewState.SYSTEM_DESIGN_PHASE],
            InterviewState.CROSS_AGENT_DEBATE: [InterviewState.FINAL_DECISION],
            InterviewState.FINAL_DECISION: [InterviewState.REPORT_GENERATION],
            InterviewState.REPORT_GENERATION: [InterviewState.COMPLETED],
            InterviewState.COMPLETED: []
        }
        
        self.state_agents: Dict[InterviewState, List[AgentType]] = {
            InterviewState.RESUME_ANALYSIS: [AgentType.RECRUITER],
            InterviewState.SKILL_PROFILING: [AgentType.RECRUITER],
            InterviewState.DSA_PHASE: [AgentType.DSA_INTERVIEWER, AgentType.HALLUCINATION_DETECTOR],
            InterviewState.SYSTEM_DESIGN_PHASE: [AgentType.SYSTEM_DESIGN, AgentType.HALLUCINATION_DETECTOR],
            InterviewState.BEHAVIORAL_PHASE: [AgentType.BEHAVIORAL],
            InterviewState.CODE_EVALUATION: [AgentType.CODE_EVALUATOR, AgentType.HALLUCINATION_DETECTOR],
            InterviewState.CROSS_AGENT_DEBATE: [AgentType.CRITIC],
            InterviewState.FINAL_DECISION: [AgentType.FINAL_DECISION],
            InterviewState.REPORT_GENERATION: [AgentType.FINAL_DECISION]
        }
        
        self.state_handlers: Dict[InterviewState, Optional[Callable]] = {}
    
    def can_transition(self, from_state: InterviewState, to_state: InterviewState) -> bool:
        return to_state in self.transitions.get(from_state, [])
    
    def get_next_states(self, current_state: InterviewState) -> List[InterviewState]:
        return self.transitions.get(current_state, [])
    
    def get_active_agents(self, state: InterviewState) -> List[AgentType]:
        return self.state_agents.get(state, [])
    
    def register_handler(self, state: InterviewState, handler: Callable):
        self.state_handlers[state] = handler
    
    async def execute_transition(
        self,
        context: InterviewContext,
        next_state: InterviewState
    ) -> InterviewContext:
        if not self.can_transition(context.current_state, next_state):
            raise ValueError(
                f"Invalid transition: {context.current_state} -> {next_state}"
            )
        
        context.current_state = next_state
        
        handler = self.state_handlers.get(next_state)
        if handler:
            context = await handler(context)
        
        return context
    
    def determine_next_state(self, context: InterviewContext) -> InterviewState:
        current = context.current_state
        possible_next = self.get_next_states(current)
        
        if not possible_next:
            return current
        
        if current == InterviewState.DSA_PHASE:
            last_message = context.messages[-1] if context.messages else None
            if last_message and "code" in last_message.payload:
                return InterviewState.CODE_EVALUATION
            return InterviewState.SYSTEM_DESIGN_PHASE
        
        return possible_next[0]

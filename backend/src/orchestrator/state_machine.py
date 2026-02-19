from typing import Dict, List
from ..models.enums import InterviewState


class StateMachine:
    """Manages valid state transitions in the interview flow"""

    def __init__(self):
        self.transitions: Dict[InterviewState, List[InterviewState]] = {
            InterviewState.INIT: [InterviewState.RESUME_ANALYSIS],
            InterviewState.RESUME_ANALYSIS: [InterviewState.DSA_PHASE],
            InterviewState.DSA_PHASE: [InterviewState.SYSTEM_DESIGN_PHASE, InterviewState.BEHAVIORAL_PHASE],
            InterviewState.SYSTEM_DESIGN_PHASE: [InterviewState.BEHAVIORAL_PHASE, InterviewState.CROSS_AGENT_DEBATE],
            InterviewState.BEHAVIORAL_PHASE: [InterviewState.CROSS_AGENT_DEBATE],
            InterviewState.CROSS_AGENT_DEBATE: [InterviewState.FINAL_DECISION],
            InterviewState.FINAL_DECISION: [InterviewState.COMPLETED],
            InterviewState.COMPLETED: []
        }

    def can_transition(self, from_state: InterviewState, to_state: InterviewState) -> bool:
        """Check if a state transition is valid"""
        if from_state not in self.transitions:
            return False
        return to_state in self.transitions[from_state]

    def get_next_states(self, current_state: InterviewState) -> List[InterviewState]:
        """Get all possible next states from current state"""
        return self.transitions.get(current_state, [])

    def validate_flow(self, state_sequence: List[InterviewState]) -> bool:
        """Validate that a sequence of states follows valid transitions"""
        if not state_sequence:
            return True

        for i in range(len(state_sequence) - 1):
            if not self.can_transition(state_sequence[i], state_sequence[i + 1]):
                return False
        return True
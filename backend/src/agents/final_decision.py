from .base import BaseAgent
from ..models.schemas import InterviewContext, AgentResponse
from ..models.enums import AgentType
import json


class FinalDecisionAgent(BaseAgent):
    """Makes final hiring recommendation based on all agent inputs"""

    def __init__(self, use_groq: bool = True, model: str = "llama-3.3-70b-versatile"):
        role_prompt = """You are the Hiring Manager making the final decision.
You synthesize all agent evaluations, debate points, and scores into a final recommendation.
Be balanced, data-driven, and justify your decision clearly.
Consider the whole candidate - technical skills AND soft skills."""

        super().__init__(
            agent_type=AgentType.FINAL_DECISION,
            role_prompt=role_prompt,
            model=model,
            use_groq=use_groq
        )

    async def act(self, context: InterviewContext) -> AgentResponse:
        scores = context.current_score
        skill_profile = context.skill_profile or {}
        difficulty = context.difficulty_level.value if context.difficulty_level else "MEDIUM"

        all_messages_summary = []
        for msg in context.messages:
            if msg.message_type.value == "evaluation":
                all_messages_summary.append(f"{msg.sender.value}: {msg.content[:300]}")

        prompt = f"""Make the final hiring decision based on all data.

Candidate: {context.candidate_name}
Difficulty Level: {difficulty}
Skill Profile: {json.dumps(skill_profile, indent=2)}

All Scores: {json.dumps(scores, indent=2)}

Interview Summary (Evaluations):
{chr(10).join(all_messages_summary[-8:]) if all_messages_summary else "Interview just started"}

Make a comprehensive final decision. Respond ONLY with valid JSON:
{{
    "recommendation": "hire",
    "confidence": 0.78,
    "overall_score": 7.5,
    "score_breakdown": {{
        "technical_skills": 8.0,
        "problem_solving": 7.5,
        "code_quality": 7.0,
        "communication": 8.0,
        "growth_potential": 9.0
    }},
    "hire_level": "SWE II",
    "strengths": ["Strong Python fundamentals", "Good problem decomposition", "Communicates clearly"],
    "concerns": ["Limited system design experience", "Needs more distributed systems knowledge"],
    "growth_areas": ["Study distributed systems", "Practice more hard LeetCode problems"],
    "detailed_feedback": "The candidate demonstrated solid algorithmic thinking and clean code...",
    "next_steps": "Recommend for team matching. Strong fit for backend-focused teams.",
    "interviewer_notes": "Candidate showed genuine curiosity and asked good clarifying questions."
}}"""

        response = await self.call_llm(prompt, self.role_prompt)

        try:
            cleaned = response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            decision = json.loads(cleaned)
            context.current_score["final_recommendation"] = decision.get("recommendation", "no_decision")
            context.current_score["overall"] = decision.get("overall_score", 0)

            rec = decision.get("recommendation", "").upper()
            emoji = "✅" if rec == "HIRE" else "❌" if rec == "NO_HIRE" else "🤔"

            content = f"{emoji} **Final Decision: {rec}** (Confidence: {int(decision.get('confidence', 0) * 100)}%)\n\n"
            content += f"**Overall Score: {decision.get('overall_score', 0)}/10**\n\n"
            content += decision.get("detailed_feedback", "")

            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=decision.get("confidence", 0.7),
                metadata={"decision": decision}
            )
        except json.JSONDecodeError:
            return AgentResponse(
                agent_type=self.agent_type,
                content="Based on the interview performance, I'll provide my final assessment.",
                confidence=0.5,
                metadata={"raw": response}
            )
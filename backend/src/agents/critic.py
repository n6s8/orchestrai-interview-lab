from .base import BaseAgent
from ..models.schemas import InterviewContext, AgentResponse
from ..models.enums import AgentType
import json


class CriticAgent(BaseAgent):
    """Challenges other agents' evaluations - plays devil's advocate"""

    def __init__(self, use_groq: bool = True, model: str = "llama-3.3-70b-versatile"):
        role_prompt = """You are a critical senior engineer who challenges evaluation scores.
Your job is to:
1. Challenge overly generous scores
2. Point out what was missed in evaluations
3. Advocate for higher standards
4. Ensure the hiring bar is maintained
5. But also recognize when other agents are being too harsh

Be rigorous but fair. Push back with evidence from the candidate's answers."""

        super().__init__(
            agent_type=AgentType.CRITIC,
            role_prompt=role_prompt,
            model=model,
            use_groq=use_groq
        )

    async def act(self, context: InterviewContext) -> AgentResponse:
        scores = context.current_score
        messages = context.messages[-6:] if len(context.messages) > 6 else context.messages

        recent_evals = [
            f"{msg.sender.value}: {msg.content[:200]}"
            for msg in messages
            if msg.message_type.value == "evaluation"
        ]

        prompt = f"""You are a critic reviewing these evaluation scores and feedback.

Current Scores: {json.dumps(scores, indent=2)}

Recent Evaluations:
{chr(10).join(recent_evals) if recent_evals else "No evaluations yet"}

As a critic, challenge the scores if needed. Respond ONLY with valid JSON:
{{
    "agrees_with_scores": false,
    "challenged_scores": {{
        "dsa": {{"original": 8, "suggested": 6, "reason": "Candidate didn't handle edge cases"}},
        "code_quality": {{"original": 7, "suggested": 7, "reason": "Score seems fair"}}
    }},
    "key_concerns": ["Edge case handling was weak", "No complexity analysis given"],
    "positive_observations": ["Clean code structure", "Good variable naming"],
    "recommendation_influence": "lean_no_hire",
    "debate_argument": "While the DSA score seems generous, the candidate failed to mention edge cases and didn't proactively discuss time complexity."
}}"""

        response = await self.call_llm(prompt, self.role_prompt)

        try:
            cleaned = response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            critique = json.loads(cleaned)
            context.current_score["critic_opinion"] = critique.get("recommendation_influence", "neutral")

            return AgentResponse(
                agent_type=self.agent_type,
                content=critique.get("debate_argument", "I have concerns about the evaluation scores."),
                confidence=0.8,
                metadata={"critique": critique}
            )
        except json.JSONDecodeError:
            return AgentResponse(
                agent_type=self.agent_type,
                content="I have reservations about some of the scores given. Let's ensure we maintain our hiring bar.",
                confidence=0.5,
                metadata={"raw": response}
            )
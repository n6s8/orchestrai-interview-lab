from .base import BaseAgent
from ..models.schemas import InterviewContext, AgentResponse
from ..models.enums import AgentType
import json


class HallucinationDetectorAgent(BaseAgent):
    """Detects if other agents are hallucinating or making unsupported claims"""

    def __init__(self, use_groq: bool = True, model: str = "llama-3.3-70b-versatile"):
        role_prompt = """You are a fact-checker that validates agent responses against ground truth.
Your job is to:
1. Check if agents' claims are supported by the candidate's actual answers
2. Detect when agents make up facts that weren't stated
3. Flag overly generous interpretations
4. Ensure evaluations are grounded in evidence

Be precise and cite specific evidence from the candidate's responses."""

        super().__init__(
            agent_type=AgentType.HALLUCINATION_DETECTOR,
            role_prompt=role_prompt,
            model=model,
            use_groq=use_groq
        )

    async def act(self, context: InterviewContext) -> AgentResponse:
        """Check recent evaluations for hallucinations"""
        recent_evals = [
            msg for msg in context.messages[-5:]
            if msg.message_type.value == "evaluation"
        ]

        if not recent_evals:
            return AgentResponse(
                agent_type=self.agent_type,
                content="No evaluations to validate yet.",
                confidence=1.0,
                metadata={"status": "no_data"}
            )

        candidate_answers = context.candidate_answers[-3:] if context.candidate_answers else []
        
        prompt = f"""Review these agent evaluations for factual accuracy.

Candidate's Recent Answers:
{chr(10).join([f"Answer {i+1}: {ans[:500]}..." for i, ans in enumerate(candidate_answers)])}

Recent Agent Evaluations:
{chr(10).join([f"{msg.sender.value}: {msg.content[:300]}" for msg in recent_evals])}

Check if the evaluations are grounded in what the candidate actually said.

Respond ONLY with valid JSON:
{{
    "hallucinations_detected": false,
    "flagged_claims": [],
    "unsupported_praise": [],
    "unsupported_criticism": [],
    "accuracy_score": 9,
    "validation_summary": "All agent claims are well-supported by the candidate's responses.",
    "recommended_corrections": []
}}"""

        response = await self.call_llm(prompt, self.role_prompt)

        try:
            cleaned = response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            validation = json.loads(cleaned)
            
            if validation.get("hallucinations_detected"):
                content = "⚠️ **Validation Issues Detected**\n\n"
                if validation.get("unsupported_praise"):
                    content += "Unsupported positive claims:\n" + "\n".join(f"• {c}" for c in validation["unsupported_praise"]) + "\n\n"
                if validation.get("unsupported_criticism"):
                    content += "Unsupported criticism:\n" + "\n".join(f"• {c}" for c in validation["unsupported_criticism"])
            else:
                content = "✅ All agent evaluations are factually grounded."

            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=validation.get("accuracy_score", 10) / 10,
                metadata={"validation": validation}
            )

        except json.JSONDecodeError:
            return AgentResponse(
                agent_type=self.agent_type,
                content="Validation check completed.",
                confidence=0.5,
                metadata={"raw": response}
            )
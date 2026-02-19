from .base import BaseAgent
from ..models.schemas import InterviewContext, AgentResponse
from ..models.enums import AgentType
import json


class SystemDesignAgent(BaseAgent):
    """Evaluates system design and architecture knowledge"""

    def __init__(self, use_groq: bool = True, model: str = "llama-3.3-70b-versatile"):
        role_prompt = """You are a senior staff engineer conducting a system design interview.
Your job is to:
1. Generate realistic system design questions appropriate to candidate level
2. Evaluate architecture proposals for scalability, reliability, and trade-offs
3. Check for understanding of databases, caching, load balancing, microservices
4. Assess ability to handle scale, failure modes, and bottlenecks

Be thorough but fair. Look for depth of understanding, not memorized patterns."""

        super().__init__(
            agent_type=AgentType.SYSTEM_DESIGN,
            role_prompt=role_prompt,
            model=model,
            use_groq=use_groq
        )

    async def act(self, context: InterviewContext) -> AgentResponse:
        """Generate a system design question"""
        difficulty = context.difficulty_level.value if context.difficulty_level else "MEDIUM"
        skill_profile = context.skill_profile or {}

        prompt = f"""Generate a system design interview question for a candidate at {difficulty} level.

Candidate's Skill Profile: {json.dumps(skill_profile, indent=2)}

Respond ONLY with valid JSON:
{{
    "title": "Design a URL Shortener Service",
    "problem_statement": "Design a scalable URL shortening service like bit.ly...",
    "requirements": [
        "Handle 100M URLs per day",
        "Generate short URLs (7 characters)",
        "Support custom aliases",
        "Track click analytics",
        "99.99% uptime"
    ],
    "evaluation_criteria": [
        "Database design",
        "Scalability approach",
        "Caching strategy",
        "Load balancing",
        "Failure handling"
    ]
}}"""

        response = await self.call_llm(prompt, self.role_prompt)

        try:
            cleaned = response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            question = json.loads(cleaned)
            context.current_question = question

            return AgentResponse(
                agent_type=self.agent_type,
                content=f"**{question.get('title', 'System Design Question')}**\n\n{question.get('problem_statement', '')}",
                confidence=0.9,
                metadata={"question": question}
            )
        except json.JSONDecodeError:
            # Fallback question
            fallback = {
                "title": "Design a URL Shortener",
                "problem_statement": "Design a URL shortening service that can handle millions of requests per day. Focus on scalability, reliability, and data storage.",
                "requirements": [
                    "Generate unique short URLs",
                    "Redirect to original URLs quickly",
                    "Handle 1M requests/day",
                    "Store URLs indefinitely"
                ]
            }
            context.current_question = fallback

            return AgentResponse(
                agent_type=self.agent_type,
                content=f"**{fallback['title']}**\n\n{fallback['problem_statement']}",
                confidence=0.7,
                metadata={"question": fallback}
            )

    async def evaluate_answer(self, context: InterviewContext) -> AgentResponse:
        """Evaluate the candidate's system design answer"""
        if not context.candidate_answers:
            return AgentResponse(
                agent_type=self.agent_type,
                content="No answer provided.",
                confidence=0.0,
                metadata={}
            )

        answer = context.candidate_answers[-1]
        question = context.current_question or {}

        prompt = f"""Evaluate this system design answer.

Question: {question.get('title', 'System Design Question')}

Candidate's Answer:
{answer}

Evaluate based on:
- Scalability (how well does it handle growth?)
- Reliability (fault tolerance, backup, recovery)
- Performance (latency, throughput)
- Trade-offs (did they discuss pros/cons?)
- Depth (did they go beyond surface level?)

Respond ONLY with valid JSON:
{{
    "score": 7,
    "strengths": ["Good database choice", "Considered caching"],
    "weaknesses": ["Missed load balancing", "No failure handling"],
    "scalability_score": 6,
    "reliability_score": 7,
    "depth_score": 8,
    "feedback": "Solid foundation but needs more attention to failure modes...",
    "follow_up_questions": ["How would you handle database failures?"]
}}"""

        response = await self.call_llm(prompt, self.role_prompt)

        try:
            cleaned = response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            evaluation = json.loads(cleaned)
            score = evaluation.get("score", 5)
            context.current_score["system_design"] = score

            strengths = evaluation.get("strengths", [])
            weaknesses = evaluation.get("weaknesses", [])

            content = f"**System Design Evaluation (Score: {score}/10)**\n\n"
            if strengths:
                content += "✅ Strengths:\n" + "\n".join(f"• {s}" for s in strengths) + "\n\n"
            if weaknesses:
                content += "⚠️ Areas to Improve:\n" + "\n".join(f"• {w}" for w in weaknesses) + "\n\n"
            content += evaluation.get("feedback", "")

            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=0.85,
                metadata={"evaluation": evaluation, "score": score}
            )
        except json.JSONDecodeError:
            return AgentResponse(
                agent_type=self.agent_type,
                content="Your system design shows understanding of key concepts. Consider discussing scalability and failure handling in more depth.",
                confidence=0.5,
                metadata={"raw": response}
            )
from .base import BaseAgent
from ..models.schemas import InterviewContext, AgentResponse
from ..models.enums import AgentType
import json


class BehavioralAgent(BaseAgent):
    """Conducts behavioral interviews using STAR method"""

    def __init__(self, use_groq: bool = True, model: str = "llama-3.3-70b-versatile"):
        role_prompt = """You are an experienced hiring manager conducting behavioral interviews.
Your job is to:
1. Ask situational questions that reveal problem-solving, communication, and leadership
2. Evaluate answers using the STAR method (Situation, Task, Action, Result)
3. Detect red flags (blaming others, vague answers, no self-reflection)
4. Assess growth mindset and ability to learn from failures

Focus on understanding how candidates think and handle real-world challenges."""

        super().__init__(
            agent_type=AgentType.BEHAVIORAL,
            role_prompt=role_prompt,
            model=model,
            use_groq=use_groq
        )

    async def act(self, context: InterviewContext) -> AgentResponse:
        """Generate a behavioral question based on skill gaps"""
        skill_profile = context.skill_profile or {}
        gaps = skill_profile.get("gaps", [])
        difficulty = context.difficulty_level.value if context.difficulty_level else "MEDIUM"

        prompt = f"""Generate a behavioral interview question for a {difficulty} level candidate.

Candidate's Skill Gaps: {gaps}

The question should probe one of these areas:
- Handling technical challenges
- Working under pressure / tight deadlines
- Collaboration and conflict resolution
- Learning from mistakes
- Leadership and mentorship

Respond ONLY with valid JSON:
{{
    "question": "Tell me about a time when you had to debug a critical production issue under time pressure.",
    "follow_ups": ["What would you do differently?", "How did the team react?"],
    "evaluation_focus": ["Problem-solving approach", "Communication under stress", "Learning outcome"]
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
                content=question.get("question", "Tell me about a challenging technical project you worked on."),
                confidence=0.9,
                metadata={"question": question}
            )
        except json.JSONDecodeError:
            fallback = {
                "question": "Describe a situation where you had to learn a new technology quickly to solve a problem. What was the situation, what did you do, and what was the outcome?",
                "follow_ups": ["What would you do differently?"],
                "evaluation_focus": ["Learning ability", "Problem-solving"]
            }
            context.current_question = fallback

            return AgentResponse(
                agent_type=self.agent_type,
                content=fallback["question"],
                confidence=0.7,
                metadata={"question": fallback}
            )

    async def evaluate_answer(self, context: InterviewContext) -> AgentResponse:
        """Evaluate behavioral answer using STAR method"""
        if not context.candidate_answers:
            return AgentResponse(
                agent_type=self.agent_type,
                content="No answer provided.",
                confidence=0.0,
                metadata={}
            )

        answer = context.candidate_answers[-1]
        question = context.current_question or {}

        prompt = f"""Evaluate this behavioral interview answer using the STAR method.

Question: {question.get('question', 'Behavioral question')}

Candidate's Answer:
{answer}

Evaluate each STAR component:
- Situation: Did they describe the context clearly?
- Task: Did they explain their responsibility?
- Action: Did they detail what THEY did (not the team)?
- Result: Did they quantify the outcome?

Also check for:
- Red flags (blaming others, vague, no reflection)
- Growth mindset (learning from failure)
- Leadership qualities
- Communication clarity

Respond ONLY with valid JSON:
{{
    "score": 8,
    "star_breakdown": {{
        "situation": 9,
        "task": 8,
        "action": 7,
        "result": 8
    }},
    "strengths": ["Clear problem description", "Took ownership"],
    "weaknesses": ["Could have mentioned metrics", "No reflection on learnings"],
    "red_flags": [],
    "growth_mindset_score": 7,
    "leadership_score": 6,
    "communication_score": 9,
    "feedback": "Strong STAR answer with clear ownership. Consider adding more specific metrics for impact."
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
            context.current_score["behavioral"] = score

            star = evaluation.get("star_breakdown", {})
            strengths = evaluation.get("strengths", [])
            weaknesses = evaluation.get("weaknesses", [])
            red_flags = evaluation.get("red_flags", [])

            content = f"**Behavioral Evaluation (Score: {score}/10)**\n\n"
            content += f"STAR Breakdown:\n"
            content += f"• Situation: {star.get('situation', 'N/A')}/10\n"
            content += f"• Task: {star.get('task', 'N/A')}/10\n"
            content += f"• Action: {star.get('action', 'N/A')}/10\n"
            content += f"• Result: {star.get('result', 'N/A')}/10\n\n"

            if strengths:
                content += "✅ Strengths:\n" + "\n".join(f"• {s}" for s in strengths) + "\n\n"
            if weaknesses:
                content += "⚠️ Areas to Improve:\n" + "\n".join(f"• {w}" for w in weaknesses) + "\n\n"
            if red_flags:
                content += "🚩 Red Flags:\n" + "\n".join(f"• {r}" for r in red_flags) + "\n\n"

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
                content="Your answer shows good situational awareness. Consider providing more specific metrics and reflecting on what you learned.",
                confidence=0.5,
                metadata={"raw": response}
            )
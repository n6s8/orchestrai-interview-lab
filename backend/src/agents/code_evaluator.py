from .base import BaseAgent
from ..models.schemas import InterviewContext, AgentResponse
from ..models.enums import AgentType
import json

class CodeEvaluatorAgent(BaseAgent):
    def __init__(self, use_groq: bool = True, model: str = "llama-3.3-70b-versatile"):
        role_prompt = """You are an expert code reviewer and evaluator at a top tech company.
Your job is to:
1. Analyze code for correctness, efficiency, and style
2. Detect edge cases the candidate missed
3. Evaluate time and space complexity accuracy
4. Check for potential bugs or issues
5. Provide constructive, specific feedback

Be thorough but fair. A good solution with minor issues should score well."""

        super().__init__(
            agent_type=AgentType.CODE_EVALUATOR,
            role_prompt=role_prompt,
            model=model,
            use_groq=use_groq
        )

    async def act(self, context: InterviewContext) -> AgentResponse:
        return await self.evaluate_code(context)

    async def evaluate_code(self, context: InterviewContext) -> AgentResponse:
        question = context.current_question or {}
        code = context.candidate_answers[-1] if context.candidate_answers else ""

        prompt = f"""Perform a detailed code review of this solution.

Problem: {question.get('title', 'Unknown')}
Problem Statement: {question.get('problem_statement', '')}
Optimal Time Complexity: {question.get('time_complexity', 'Unknown')}
Optimal Space Complexity: {question.get('space_complexity', 'Unknown')}

Candidate's Code:
```
{code}
```

Analyze thoroughly and respond ONLY with valid JSON:
{{
    "syntax_valid": true,
    "logic_correct": true,
    "handles_edge_cases": false,
    "time_complexity": "O(n)",
    "space_complexity": "O(n)",
    "is_optimal": true,
    "bugs": [],
    "missed_edge_cases": ["Empty array", "Single element"],
    "code_quality": {{
        "readability": 8,
        "naming": 7,
        "structure": 8
    }},
    "scores": {{
        "correctness": 9,
        "efficiency": 8,
        "style": 7,
        "overall": 8
    }},
    "detailed_feedback": "Your solution correctly uses a hash map...",
    "suggested_improvements": ["Add input validation", "Handle empty array case"],
    "test_cases_analysis": [
        {{"input": "[2,7,11,15], target=9", "expected": "[0,1]", "your_output": "[0,1]", "passes": true}}
    ]
}}"""

        response = await self.call_llm(prompt, self.role_prompt)

        try:
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            evaluation = json.loads(cleaned)
            overall_score = evaluation.get("scores", {}).get("overall", 5)
            context.current_score["code_quality"] = overall_score

            feedback_parts = [evaluation.get("detailed_feedback", "")]
            
            if evaluation.get("bugs"):
                feedback_parts.append(f"\n**Bugs found:** {', '.join(evaluation['bugs'])}")
            
            if evaluation.get("missed_edge_cases"):
                feedback_parts.append(f"\n**Missed edge cases:** {', '.join(evaluation['missed_edge_cases'])}")

            if evaluation.get("suggested_improvements"):
                feedback_parts.append(f"\n**Suggestions:** {'; '.join(evaluation['suggested_improvements'])}")

            return AgentResponse(
                agent_type=self.agent_type,
                content="\n".join(feedback_parts),
                confidence=0.88,
                metadata={"code_evaluation": evaluation, "score": overall_score}
            )
        except json.JSONDecodeError:
            return AgentResponse(
                agent_type=self.agent_type,
                content="Code reviewed. I've analyzed your solution for correctness, efficiency, and style.",
                confidence=0.5,
                metadata={"raw_response": response}
            )
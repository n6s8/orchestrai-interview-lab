from .base import BaseAgent
from ..models.schemas import InterviewContext, AgentResponse
from ..models.enums import AgentType, DifficultyLevel
import json
import os

class DSAInterviewerAgent(BaseAgent):
    def __init__(self, use_groq: bool = True, model: str = "llama-3.3-70b-versatile"):
        role_prompt = """You are an expert DSA (Data Structures & Algorithms) interviewer from a top tech company.
Your job is to:
1. Ask appropriate coding questions based on candidate's skill level
2. Provide hints when candidates are stuck
3. Evaluate the approach before the solution
4. Ask follow-up questions about time/space complexity

Be encouraging but rigorous. Focus on problem-solving thinking, not just correct answers."""

        super().__init__(
            agent_type=AgentType.DSA_INTERVIEWER,
            role_prompt=role_prompt,
            model=model,
            use_groq=use_groq
        )

    async def act(self, context: InterviewContext) -> AgentResponse:
        if not context.current_question:
            return await self.generate_question(context)
        else:
            return await self.evaluate_answer(context)

    async def generate_question(self, context: InterviewContext) -> AgentResponse:
        difficulty = context.difficulty_level.value if context.difficulty_level else "MEDIUM"
        skill_profile = context.skill_profile or {}
        dsa_level = skill_profile.get("dsa_level", "beginner")
        strengths = skill_profile.get("strengths", [])
        gaps = skill_profile.get("gaps", [])

        prompt = f"""Generate a coding interview question for a candidate with:
- DSA Level: {dsa_level}
- Difficulty: {difficulty}
- Strengths: {strengths}
- Gaps to probe: {gaps}

Create ONE appropriate LeetCode-style problem.

Respond ONLY with valid JSON:
{{
    "title": "Two Sum",
    "difficulty": "Easy",
    "category": "Arrays",
    "problem_statement": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target...",
    "examples": [
        {{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "nums[0] + nums[1] = 2 + 7 = 9"}}
    ],
    "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9"],
    "hints": ["Try using a hash map", "Think about what you need to find for each element"],
    "optimal_approach": "Hash map for O(n) time complexity",
    "time_complexity": "O(n)",
    "space_complexity": "O(n)"
}}"""

        response = await self.call_llm(prompt, self.role_prompt)

        try:
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            question_data = json.loads(cleaned)
            context.current_question = question_data

            return AgentResponse(
                agent_type=self.agent_type,
                content=f"Here's your {question_data.get('difficulty', difficulty)} question: **{question_data.get('title')}**\n\n{question_data.get('problem_statement')}",
                confidence=0.9,
                metadata={"question": question_data, "phase": "question_presented"}
            )
        except json.JSONDecodeError:
            fallback_question = self._get_fallback_question(difficulty)
            context.current_question = fallback_question
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"**{fallback_question['title']}**\n\n{fallback_question['problem_statement']}",
                confidence=0.7,
                metadata={"question": fallback_question, "phase": "question_presented"}
            )

    async def evaluate_answer(self, context: InterviewContext) -> AgentResponse:
        question = context.current_question
        candidate_answer = context.candidate_answers[-1] if context.candidate_answers else ""

        prompt = f"""Evaluate this candidate's answer to a DSA question.

Question: {question.get('title')}
Problem: {question.get('problem_statement')}
Optimal Approach: {question.get('optimal_approach')}
Expected Time: {question.get('time_complexity')}
Expected Space: {question.get('space_complexity')}

Candidate's Answer:
{candidate_answer}

Evaluate and respond ONLY with valid JSON:
{{
    "correctness_score": 8,
    "approach_score": 7,
    "code_quality_score": 8,
    "overall_score": 7.5,
    "is_correct": true,
    "time_complexity_given": "O(n)",
    "space_complexity_given": "O(n)",
    "complexity_correct": true,
    "strengths": ["Good use of hash map", "Clean code"],
    "improvements": ["Could handle edge cases better"],
    "feedback": "Good solution! You correctly used a hash map to achieve O(n) time complexity...",
    "follow_up_question": "What if the array was sorted? Could you do better than O(n) space?"
}}"""

        response = await self.call_llm(prompt, self.role_prompt)

        try:
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            evaluation = json.loads(cleaned)
            score = evaluation.get("overall_score", 5)
            context.current_score["dsa"] = score

            feedback = evaluation.get("feedback", "Answer evaluated.")
            follow_up = evaluation.get("follow_up_question", "")
            
            content = f"{feedback}"
            if follow_up:
                content += f"\n\n**Follow-up:** {follow_up}"

            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=0.85,
                metadata={"evaluation": evaluation, "phase": "answer_evaluated"}
            )
        except json.JSONDecodeError:
            return AgentResponse(
                agent_type=self.agent_type,
                content="I've reviewed your answer. Let's discuss your approach and complexity analysis.",
                confidence=0.5,
                metadata={"raw_response": response, "phase": "answer_evaluated"}
            )

    def _get_fallback_question(self, difficulty: str) -> dict:
        questions = {
            "EASY": {
                "title": "Two Sum",
                "difficulty": "Easy",
                "category": "Arrays",
                "problem_statement": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.",
                "examples": [{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "nums[0] + nums[1] = 9"}],
                "constraints": ["2 <= nums.length <= 10^4", "Each input has exactly one solution"],
                "hints": ["Try using a hash map", "For each number, check if target-number exists"],
                "optimal_approach": "Hash map for O(n) time",
                "time_complexity": "O(n)",
                "space_complexity": "O(n)"
            },
            "MEDIUM": {
                "title": "Longest Substring Without Repeating Characters",
                "difficulty": "Medium",
                "category": "Sliding Window",
                "problem_statement": "Given a string s, find the length of the longest substring without repeating characters.",
                "examples": [{"input": 's = "abcabcbb"', "output": "3", "explanation": "The answer is 'abc', with the length of 3"}],
                "constraints": ["0 <= s.length <= 5 * 10^4"],
                "hints": ["Use sliding window", "Use a set to track characters in current window"],
                "optimal_approach": "Sliding window with hash set",
                "time_complexity": "O(n)",
                "space_complexity": "O(min(m,n))"
            },
            "HARD": {
                "title": "Median of Two Sorted Arrays",
                "difficulty": "Hard",
                "category": "Binary Search",
                "problem_statement": "Given two sorted arrays nums1 and nums2 of size m and n respectively, return the median of the two sorted arrays. The overall run time complexity should be O(log(m+n)).",
                "examples": [{"input": "nums1 = [1,3], nums2 = [2]", "output": "2.0", "explanation": "Merged = [1,2,3], median = 2"}],
                "constraints": ["0 <= m, n <= 1000", "1 <= m + n"],
                "hints": ["Binary search on the smaller array", "Think about partitioning both arrays"],
                "optimal_approach": "Binary search for O(log(min(m,n)))",
                "time_complexity": "O(log(min(m,n)))",
                "space_complexity": "O(1)"
            }
        }
        return questions.get(difficulty, questions["MEDIUM"])
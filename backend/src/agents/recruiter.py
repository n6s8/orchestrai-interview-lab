from .base import BaseAgent
from ..models.schemas import InterviewContext, AgentResponse
from ..models.enums import AgentType, DifficultyLevel
import json

class RecruiterAgent(BaseAgent):
    def __init__(self, use_groq: bool = True, model: str = "llama3-8b-8192"):
        role_prompt = """You are an expert technical recruiter with deep knowledge of software engineering roles.
Your job is to:
1. Analyze candidate resumes thoroughly
2. Extract key skills, experience levels, and technical strengths
3. Identify gaps and areas to probe during the interview
4. Determine appropriate difficulty levels for technical questions
5. Create a comprehensive skill profile

Be analytical, objective, and focus on technical competencies."""
        
        super().__init__(
            agent_type=AgentType.RECRUITER,
            role_prompt=role_prompt,
            model=model,
            use_groq=use_groq
        )
    
    async def act(self, context: InterviewContext) -> AgentResponse:
        if not context.candidate_resume:
            return AgentResponse(
                agent_type=self.agent_type,
                content="No resume provided",
                confidence=0.0
            )
        
        if not context.skill_profile:
            return await self.analyze_resume(context)
        else:
            return await self.generate_interview_plan(context)
    
    async def analyze_resume(self, context: InterviewContext) -> AgentResponse:
        prompt = f"""Analyze this resume and extract:
1. Programming languages and proficiency levels
2. Frameworks and technologies
3. Years of experience (estimate)
4. Notable projects and their complexity
5. Algorithm/DS experience level
6. System design experience level

Resume:
{context.candidate_resume}

Respond ONLY with valid JSON:
{{
    "languages": {{"python": "advanced", "javascript": "intermediate"}},
    "frameworks": ["react", "fastapi"],
    "experience_years": 2,
    "dsa_level": "intermediate",
    "system_design_level": "beginner",
    "projects_complexity": "medium",
    "strengths": ["rag", "full-stack"],
    "gaps": ["distributed systems", "scaling"]
}}"""
        
        response = await self.call_llm(prompt, self.role_prompt)
        
        try:
            response_cleaned = response.strip()
            if response_cleaned.startswith("```json"):
                response_cleaned = response_cleaned.split("```json")[1].split("```")[0].strip()
            elif response_cleaned.startswith("```"):
                response_cleaned = response_cleaned.split("```")[1].split("```")[0].strip()
            
            skill_profile = json.loads(response_cleaned)
            context.skill_profile = skill_profile
            
            difficulty = self._determine_difficulty(skill_profile)
            context.difficulty_level = difficulty
            
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"Resume analyzed. Candidate shows {skill_profile.get('dsa_level', 'unknown')} DSA skills. Recommended difficulty: {difficulty.value}",
                confidence=0.85,
                reasoning=f"Based on experience and project complexity",
                metadata={"skill_profile": skill_profile, "difficulty": difficulty.value}
            )
        except json.JSONDecodeError as e:
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"Resume analyzed but couldn't parse structured profile. Raw response available.",
                confidence=0.5,
                metadata={"raw_response": response, "error": str(e)}
            )
    
    async def generate_interview_plan(self, context: InterviewContext) -> AgentResponse:
        skill_profile = context.skill_profile
        
        prompt = f"""Given this skill profile, create an interview plan:
{json.dumps(skill_profile, indent=2)}

Suggest:
1. Which areas to focus on (DSA, System Design, Behavioral)
2. Specific topics to probe based on gaps
3. Time allocation for each phase

Respond in JSON:
{{
    "focus_areas": ["dsa", "system_design"],
    "dsa_topics": ["arrays", "graphs"],
    "system_design_topics": ["caching", "load_balancing"],
    "time_allocation": {{"dsa": 30, "system_design": 20, "behavioral": 10}}
}}"""
        
        response = await self.call_llm(prompt, self.role_prompt)
        
        try:
            response_cleaned = response.strip()
            if response_cleaned.startswith("```json"):
                response_cleaned = response_cleaned.split("```json")[1].split("```")[0].strip()
            elif response_cleaned.startswith("```"):
                response_cleaned = response_cleaned.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(response_cleaned)
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"Interview plan generated. Focus: {', '.join(plan.get('focus_areas', []))}",
                confidence=0.9,
                metadata={"interview_plan": plan}
            )
        except json.JSONDecodeError:
            return AgentResponse(
                agent_type=self.agent_type,
                content="Generated interview plan",
                confidence=0.7,
                metadata={"raw_response": response}
            )
    
    def _determine_difficulty(self, skill_profile: dict) -> DifficultyLevel:
        dsa_level = skill_profile.get("dsa_level", "beginner").lower()
        experience = skill_profile.get("experience_years", 0)
        
        if dsa_level == "advanced" or experience >= 5:
            return DifficultyLevel.HARD
        elif dsa_level == "intermediate" or experience >= 2:
            return DifficultyLevel.MEDIUM
        else:
            return DifficultyLevel.EASY
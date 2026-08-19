import os
import sys
import site
import json
import re
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from app.config import settings

logger = logging.getLogger(__name__)

# Ensure user site-packages is in sys.path
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.append(user_site)


class GeminiService:
    def __init__(self):
        load_dotenv(override=True)
        self.api_key = os.getenv("GEMINI_API_KEY", getattr(settings, "GEMINI_API_KEY", ""))
        self.client = None
        self.types_module = None

        if self.api_key:
            try:
                from google import genai
                from google.genai import types
                self.types_module = types
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.client = None

    def is_available(self) -> bool:
        if self.client is None and self.api_key:
            try:
                from google import genai
                from google.genai import types
                self.types_module = types
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                pass
        return self.client is not None

    def _generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self.is_available():
            return "Gemini AI API key is not configured or offline. Operating in fallback mode."

        try:
            config = self.types_module.GenerateContentConfig()
            if system_instruction:
                config.system_instruction = system_instruction
                
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            return response.text.strip() if response.text else "No response generated."
        except Exception as e:
            logger.error(f"Gemini API invocation error: {e}")
            return f"[Offline Mode] Unable to contact Gemini AI Tutor ({str(e)})."

    def chat_with_tutor(self, message: str, context: Optional[str] = None) -> Dict[str, Any]:
        system_instruction = (
            "You are an expert AI Tutor & Software Engineering Mentor guiding a Computer Science student through a strict 60-day job preparation program. "
            "Provide helpful, concise, structured, and highly encouraging advice. "
            "If the user asks technical questions (DSA, System Design, SQL, Python, ML, HR), give crisp, interview-ready answers."
        )
        prompt = f"Context:\n{context}\n\nStudent Message: {message}" if context else f"Student Message: {message}"
        response_text = self._generate(prompt, system_instruction=system_instruction)
        
        return {
            "reply": response_text,
            "status": "success"
        }

    def ask(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        return self.chat_with_tutor(question, context)

    def explain(self, topic: str, category: str = "General") -> str:
        prompt = f"Explain the topic '{topic}' in category '{category}' in 4 bullet points: 1. Core Intuition, 2. Key Architecture/Formula, 3. Common Interview Edge Cases, 4. Time/Space Complexity."
        return self._generate(prompt, system_instruction="You are a CSE Technical Interviewer.")

    def hint(self, question_text: str, hint_level: int = 1) -> str:
        """
        Progressive Hinting Engine:
        Level 1: Subtle clue without revealing algorithm/code.
        Level 2: Algorithm/pattern direction hint without full solution.
        Level 3: Complete solution with complexity analysis and follow-up question.
        """
        if hint_level == 1:
            instruction = "Provide a LEVEL 1 SUBTLE HINT. Guide the candidate's thinking with a small clue. Do NOT mention specific data structures or code."
        elif hint_level == 2:
            instruction = "Provide a LEVEL 2 PATTERN HINT. Suggest the optimal algorithm pattern or data structure (e.g., Sliding Window, Hash Map, Two Pointers), but do NOT write the full implementation."
        else:
            instruction = "Provide a LEVEL 3 COMPLETE SOLUTION. Include: 1. Approach & Intuition, 2. Step-by-Step Algorithm, 3. Time Complexity, 4. Space Complexity, 5. Edge Cases, 6. Follow-up Interview Question."

        return self._generate(f"Question: {question_text}", system_instruction=instruction)

    def evaluate_interview_answer(self, question_text: str, user_answer: str, category: str = "Technical") -> Dict[str, Any]:
        """
        Evaluates interview answer and returns structured JSON schema:
        score (0-10), correct_points (list), missing_points (list), incorrect_points (list), better_answer (str), interview_tip (str), follow_up_question (str).
        """
        system_instruction = (
            "You are a Senior Tech Lead conducting an interview. Evaluate the candidate's answer. "
            "Return ONLY valid JSON matching this exact structure: "
            "{\n"
            '  "score": 7.5,\n'
            '  "correct_points": ["point 1", "point 2"],\n'
            '  "missing_points": ["missing point 1"],\n'
            '  "incorrect_points": [],\n'
            '  "better_answer": "Model answer string",\n'
            '  "interview_tip": "Pro tip for interview delivery",\n'
            '  "follow_up_question": "Next logical question"\n'
            "}"
        )
        prompt = f"Category: {category}\nQuestion: {question_text}\n\nCandidate Answer: {user_answer}"
        raw_res = self._generate(prompt, system_instruction=system_instruction)

        try:
            clean_json = raw_res.replace("```json", "").replace("```", "").strip()
            # Extract JSON substring if surrounded by extra text
            json_match = re.search(r"\{.*\}", clean_json, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
            data = json.loads(clean_json)
            return {
                "score": float(data.get("score", 7.0)),
                "correct_points": data.get("correct_points", []),
                "missing_points": data.get("missing_points", []),
                "incorrect_points": data.get("incorrect_points", []),
                "better_answer": data.get("better_answer", "Explain concept clearly with trade-offs."),
                "interview_tip": data.get("interview_tip", "Structure response using STAR framework."),
                "follow_up_question": data.get("follow_up_question", "How does this scale under high load?")
            }
        except Exception:
            return {
                "score": 7.0 if len(user_answer) > 40 else 5.0,
                "correct_points": ["Addressed core topic"],
                "missing_points": ["Detailed trade-offs and edge case analysis"],
                "incorrect_points": [],
                "better_answer": raw_res,
                "interview_tip": "Be concise and state complexity upfront.",
                "follow_up_question": f"Can you explain the trade-offs of this approach in {category}?"
            }

    def evaluate_dsa(self, question_text: str, user_answer: str) -> Dict[str, Any]:
        return self.evaluate_interview_answer(question_text, user_answer, category="DSA Coding")

    def generate_interview_question(self, topic: str, difficulty: str = "Medium") -> Dict[str, Any]:
        prompt = f"Generate 1 high-frequency placement interview question on topic '{topic}' at '{difficulty}' difficulty level."
        q_text = self._generate(prompt, system_instruction="You are a CSE Interviewer.")
        return {
            "topic": topic,
            "difficulty": difficulty,
            "question": q_text
        }

    def generate_follow_up(self, previous_question: str, previous_answer: str) -> str:
        prompt = f"Previous Question: {previous_question}\nCandidate Answer: {previous_answer}\n\nAsk 1 logical, insightful follow-up question to probe deeper."
        return self._generate(prompt, system_instruction="You are a Senior Technical Interviewer.")

    def generate_project_questions(self, project_name: str, project_description: Optional[str] = None) -> Dict[str, Any]:
        desc = project_description or f"Portfolio project named '{project_name}'."
        prompt = f"Project: {project_name}\nDescription: {desc}\n\nGenerate: 60s pitch, 2min pitch, 3 architecture questions, 2 database/ML questions, and 2 trade-off/challenge questions."
        res = self._generate(prompt, system_instruction="Act as a Principal Engineer conducting a project deep-dive.")
        return {
            "project_name": project_name,
            "interview_guide": res
        }

    def generate_daily_review(self, daily_stats: Dict[str, Any]) -> str:
        prompt = f"Daily Study Stats:\n{json.dumps(daily_stats, indent=2)}\n\nGenerate a 3-bullet motivating end-of-day review and actionable priority focus for tomorrow."
        return self._generate(prompt, system_instruction="You are an encouraging AI career coach.")

    def adapt_study_plan(self, current_plan: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        system_instruction = (
            "You are an AI Academic Advisor. The user wants to adjust their daily 60-day plan. "
            "Modify fields according to request. Return ONLY valid JSON with keys: "
            "objectives (str), dsa_topic (str), python_topic (str), sql_topic (str), ml_topic (str), estimated_total_time (num)."
        )
        prompt = f"Current Daily Plan:\n{json.dumps(current_plan, indent=2)}\n\nUser Request: {user_prompt}"
        raw_res = self._generate(prompt, system_instruction=system_instruction)

        try:
            clean_res = raw_res.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_res)
        except Exception:
            return {
                "objectives": f"Adjusted Plan: {user_prompt[:80]}...",
                "estimated_total_time": 4.0 if "hour" in user_prompt.lower() else current_plan.get("estimated_hours", 6.5)
            }

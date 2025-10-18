import os
import json
import traceback
import time
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

client = None

def initialize_groq_client():
    """Initialize Groq client with proper error handling."""
    global client
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("[LLM] ERROR: GROQ_API_KEY not found in environment variables")
        return False
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        print("[LLM] Groq client initialized successfully")
        return True
    except Exception as e:
        print(f"[LLM] ERROR: Failed to initialize Groq client: {e}")
        return False


def create_strong_prompt(resume_text: str, jd_text: str, candidate_name: str, candidate_index: int) -> str:
    """Highly detailed prompt for ATS evaluation with HR-focused, actionable feedback."""
    jd_key = jd_text[:600]  # 600 chars
    resume_key = resume_text[:900]  # 900 chars

    return f"""
You are an expert HR professional and ATS evaluator. Your task is to critically analyze the following candidate resume against the provided job description (JD). Your evaluation should be highly specific, actionable, and tailored for HR decision-makers.

Job Description (trimmed):
{jd_key}

Candidate Resume (trimmed):
{resume_key}

Please return ONLY valid JSON with this schema:
{{
  "ats_score": number (0-100, no decimals),
  "reason": "A concise, evidence-based justification for the score, referencing specific skills, experiences, or gaps from the resume and JD.",
  "feedback": "2–3 sentences highlighting the candidate's most relevant strengths and weaknesses, using concrete examples from the resume and directly tying them to the JD requirements.",
  "improvements": [
    "List 3-5 highly specific, actionable suggestions for the candidate. These should include missing technical or soft skills from the JD, ways to improve resume phrasing or quantify achievements, and any formatting or clarity enhancements that would make the resume stand out to HR."
  ]
}}

Guidelines:
- Use direct references to both the JD and resume (e.g., 'The JD requires project management with Agile, but the resume only mentions Scrum experience').
- For 'reason', justify the score with clear, HR-relevant logic.
- For 'feedback', highlight both what the candidate does well and what is lacking, with examples.
- For 'improvements', be concrete and actionable (e.g., 'Add a section on leadership experience', 'Quantify sales achievements', 'Include proficiency in Python as listed in the JD').
- Avoid generic statements; be as specific as possible.
- Each candidate must get a distinct score.

Return ONLY the JSON object, no extra commentary.
"""
def analyze_resume_with_jd(resume_text: str, jd_text: str, candidate_name="Candidate", candidate_index=1) -> Dict[str, Any]:
    global client
    if not client:
        if not initialize_groq_client():
            return create_smart_fallback(resume_text, jd_text, candidate_name, candidate_index)

    prompt = create_strong_prompt(resume_text, jd_text, candidate_name, candidate_index)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an ATS evaluator. Reply in JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=500,
            timeout=40,
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"```json|```", "", content).strip()

        result = json.loads(content)

        if not validate_json_result(result):
            raise ValueError("Invalid JSON schema from LLM")

        return enhance_result(result, resume_text, jd_text, candidate_name, candidate_index)

    except Exception as e:
        print(f"[LLM] ERROR: {e}")
        return create_smart_fallback(resume_text, jd_text, candidate_name, candidate_index, str(e))


def validate_json_result(result: dict) -> bool:
    required_keys = ["ats_score", "feedback", "improvements"]
    return all(k in result for k in required_keys) and isinstance(result["improvements"], list)


def enhance_result(result: dict, resume_text: str, jd_text: str, candidate_name: str, candidate_index: int) -> dict:
    base_score = int(result.get("ats_score", 50))
    variation = (candidate_index * 5) % 12 - 6
    result["ats_score"] = max(20, min(95, base_score + variation))

    if not result.get("reason"):
        result["reason"] = "No reason provided by LLM. Please check the prompt or fallback logic."

    if not result.get("feedback"):
        result["feedback"] = "Resume shows potential but needs stronger alignment with JD."

    if not result.get("improvements") or len(result["improvements"]) < 3:
        result["improvements"] = [
            "Add more quantified achievements (e.g., % impact, $ saved, time reduced).",
            "Include missing technical skills explicitly mentioned in JD.",
            "Improve formatting and section clarity for readability."
        ]

    return result


def create_smart_fallback(resume_text: str, jd_text: str, candidate_name: str, candidate_index: int, reason="LLM failure") -> dict:
    jd_lower = jd_text.lower()
    resume_lower = resume_text.lower()

    required_skills = [w for w in ["python", "java", "react", "aws", "sql", "docker"] if w in jd_lower]
    found_skills = [s for s in required_skills if s in resume_lower]

    score = 40 + len(found_skills) * 10
    score = min(score, 85)

    return {
        "ats_score": score,
        "reason": f"Scored by fallback: found {len(found_skills)} of {len(required_skills)} required skills. {reason}",
        "feedback": f"Candidate shows {len(found_skills)} out of {len(required_skills)} required skills.",
        "improvements": [
            f"Add missing skills: {', '.join(set(required_skills) - set(found_skills)) or 'None'}",
            "Include measurable outcomes for projects.",
            "Restructure resume to emphasize JD-related experience."
        ]
    }


def analyze_multiple_resumes(resume_documents: List[Dict[str, Any]], jd_text: str) -> List[Dict[str, Any]]:
    """
    Analyze multiple resumes (documents) against a job description.
    Each document should have at least 'parsed_data' with 'raw_text', '_id', and 'filename'.
    """
    results = []
    for idx, doc in enumerate(resume_documents):
        resume_text = doc.get("parsed_data", {}).get("raw_text", "")
        candidate_name = doc.get("parsed_data", {}).get("personal_info", {}).get("name", f"Candidate {idx+1}")
        analysis = analyze_resume_with_jd(resume_text, jd_text, candidate_name, idx+1)
        results.append({
            "resume_id": str(doc.get("_id", "")),
            "filename": doc.get("filename", "unknown.pdf"),
            "analysis": analysis,
            "rank": idx + 1
        })
    return results

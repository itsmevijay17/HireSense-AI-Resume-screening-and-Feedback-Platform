import random

class HuggingFaceScoringService:
    def __init__(self):
        # later you will add API key & URL here
        pass

    def evaluate_resume(self, jd_text: str, resume_data: dict):
        """
        Dummy implementation.
        Replace with Hugging Face inference API call later.
        """
        # Simulated ATS score
        ats_score = random.randint(50, 100)

        return {
            "ats_score": ats_score,
            "feedback": f"Resume evaluated for JD length {len(jd_text)}.",
            "improvements": "Add more keywords related to the JD.",
            "reason": "Lack of relevant project experience.",
            "cover_letter": f"Dear HR, I am excited to apply for this role because..."
        }

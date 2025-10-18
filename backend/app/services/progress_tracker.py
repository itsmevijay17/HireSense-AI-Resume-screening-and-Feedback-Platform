class ProgressTracker:
    """
    Track candidate's skill development progress over time.
    Compare multiple analysis reports to show improvement.
    """
    def __init__(self):
        self.history = []

    def add_analysis(self, analysis_date, gap_analysis):
        self.history.append({
            "date": analysis_date,
            "match_percentage": gap_analysis.get("match_percentage", 0),
            "ats_score": gap_analysis.get("ats_score", 0),
            "matched_skills_count": len(gap_analysis.get("matched_skills", [])),
            "missing_skills_count": len(gap_analysis.get("missing_skills", []))
        })

    def calculate_improvement(self):
        if len(self.history) < 2:
            return None
        first = self.history[0]
        last = self.history[-1]
        return {
            "match_percentage_change": last["match_percentage"] - first["match_percentage"],
            "ats_score_change": last["ats_score"] - first["ats_score"],
            "skills_learned": first["missing_skills_count"] - last["missing_skills_count"],
            "days_elapsed": (last["date"] - first["date"]).days,
            "learning_velocity": (
                (first["missing_skills_count"] - last["missing_skills_count"]) /
                ((last["date"] - first["date"]).days / 7)
            ) if (last["date"] - first["date"]).days > 0 else 0
        }

    def generate_progress_report(self):
        if len(self.history) < 2:
            return "Not enough data for progress tracking. Run another analysis in 30 days."
        improvement = self.calculate_improvement()
        report = f"""
Progress Report:
- Match Percentage: {improvement['match_percentage_change']:+.1f}% improvement
- ATS Score: {improvement['ats_score_change']:+.1f} points improvement
- Skills Learned: {improvement['skills_learned']} new skills
- Time Period: {improvement['days_elapsed']} days
- Learning Velocity: {improvement['learning_velocity']:.1f} skills/week

{"Excellent progress! Keep up the momentum." if improvement['match_percentage_change'] > 10 else "Good start! Stay consistent with your learning plan."}
"""
        return report.strip()
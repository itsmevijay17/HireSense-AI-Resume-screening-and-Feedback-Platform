🚀 HireSense – AI Resume Screening & Feedback Platform












GitHub: itsmevijay17/HireSense-AI-Resume-screening-and-Feedback-Platform

🎯 Overview

HireSense is an AI-powered Applicant Tracking System (ATS) that leverages Groq LLM to revolutionize resume screening and personalized candidate feedback.
It bridges the gap between HR recruiters and job seekers by providing automated scoring, insights, and guided improvement paths through intelligent text understanding.

The system includes two main modules:

HR Module → Bulk resume upload, Groq-powered scoring, ranking, and CSV export

Job Seeker Module → Individual resume feedback, skill gap detection, and personalized learning roadmap

✨ Key Features
👩‍💼 For HR Professionals

📂 Bulk Resume Uploads (10+)

Upload multiple resumes simultaneously for instant analysis.

⚙️ Batch Scoring with Groq LLM

Performs parallel evaluation of all uploaded resumes.

Generates for each resume:

🧮 ATS Score (0–100)

💡 Reason for ATS Score (LLM-explained reasoning)

🧠 Feedback Summary (key strengths & weaknesses)

🔧 Improvement Suggestions (how to optimize the resume)

Enables data-driven shortlisting and transparent hiring.

📊 Automated Candidate Ranking & CSV Export

Sorts and exports candidate results by ATS performance.

🧠 Semantic JD–Resume Matching

Matches resumes to job descriptions using LLM semantic understanding.

⚖️ Bias-Reduced Screening

Focuses purely on skill relevance and content quality.

⚙️ Fast, Scalable, and Secure

Groq LLM ensures real-time processing even for large resume batches.

👨‍🎓 For Job Seekers

📈 AI-Powered Skill Gap & Fit Analysis

Calculates Skill Match %, ATS Score, and Fit Score.

Identifies Matched Skills, Skills to Develop, and Transferable Skills.

🧠 Executive Summary & Career Readiness Score

AI-generated overview highlighting current strengths and areas to improve.

💪 Strengths & Quick Wins

Suggests immediate, actionable improvements.

🔍 Detailed Skills Breakdown

Displays each skill’s category, priority, and estimated learning time.

🗺️ Personalized Action Plan

Step-by-step roadmap including:

Resume optimization advice

Course and platform recommendations

Portfolio project ideas

Networking guidance

📅 30/60/90-Day Learning Roadmap

Structured timeline to become interview-ready in 8–12 weeks.

💼 Market Insights & ROI

Predicts salary uplift potential from acquiring high-ROI skills.

📚 Curated Learning Resources

Suggests practical resources from Coursera, Udemy, edX, and YouTube.

✅ Action Checklist & Progress Tracking

Includes AI-based re-analysis after 30 days to measure growth.

🧠 Architecture / Tech Stack
Layer	Technology	Description
Frontend	Streamlit	Interactive dashboard for HR & Job Seekers
Backend	FastAPI	RESTful API for resume parsing and scoring
Database	MongoDB	Stores parsed resumes, scores, and metadata
AI Engine	Groq LLM	Handles reasoning, scoring, and feedback
PDF Parsing	PyMuPDF, pdfplumber	Extracts text and structure from resumes
Utilities	Pydantic, pandas	Validation and data processing
⚙️ Installation & Setup
🧩 Prerequisites

Python 3.10+

MongoDB Atlas account

Groq API key

🧰 Clone the Repository
git clone https://github.com/itsmevijay17/HireSense-AI-Resume-screening-and-Feedback-Platform.git
cd HireSense-AI-Resume-screening-and-Feedback-Platform

🔑 Environment Variables

Create a .env file in the root directory:

MONGO_URI=your_mongodb_uri
GROQ_API_KEY=your_groq_api_key


⚠️ Never commit .env — ensure it’s in .gitignore.

🧱 Backend Setup
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
uvicorn app.main:app --reload

🎨 Frontend Setup (Streamlit)
cd ../frontend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
streamlit run app.py

🚀 Usage Guide
HR Module

Bulk Resume Analysis

curl -X POST "http://localhost:8000/api/hr/analyze-bulk" \
     -F "files=@resumes/sample1.pdf" \
     -F "files=@resumes/sample2.pdf"


Output (per resume):

{
  "ats_score": 83,
  "reason": "Strong technical alignment but lacks project diversity.",
  "feedback": "Excellent use of keywords and structure.",
  "improvements": ["Add measurable outcomes", "Highlight teamwork projects"]
}

Job Seeker Module

Single Resume Feedback

curl -X POST "http://localhost:8000/api/jobseeker/analyze" \
     -F "file=@resumes/sample1.pdf"


Generates a comprehensive AI report containing:

Skill Match %, Fit Score, ATS Score

Executive Summary & Career Fit

Strengths, Gaps, and Transferable Skills

30/60/90 Day Learning Plan

Personalized Roadmap with Recommended Resources

🖼️ Screenshots
HR Dashboard	Job Seeker Report	CSV Export

	
	
🔒 Security & Privacy

.env file for sensitive credentials

LLM sanitization to prevent prompt injection

No permanent storage of resume data

Compliant with data privacy standards (GDPR)

🤝 Contributing

Fork the repo

Create a feature branch

Follow PEP8 and document changes

Submit a pull request with context

🧾 License

Licensed under the MIT License
.

📞 Support

For issues or feature requests:
📬 Open a GitHub Issue or reach out via repository discussions.

Built with ❤️ using FastAPI, Streamlit, MongoDB & Groq LLM.

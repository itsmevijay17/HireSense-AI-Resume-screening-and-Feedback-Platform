# HireSense - AI-Powered Resume Analysis System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red.svg)](https://streamlit.io/)
[![Groq](https://img.shields.io/badge/Groq-LLM--Powered-orange.svg)](https://groq.com/)

## 🎯 Overview

HireSense is an advanced AI-powered Applicant Tracking System (ATS) that revolutionizes the hiring process for both HR professionals and job seekers. Using state-of-the-art LLM technology and custom NLP algorithms, it provides automated resume screening, skill gap analysis, and personalized career guidance.

## ✨ Key Features

### For HR Professionals
- 📊 Bulk resume analysis (10+ resumes simultaneously)
- 🤖 AI-powered ATS scoring with detailed reasoning
- 📈 Automated candidate ranking and shortlisting
- 📑 CSV export functionality for results
- ⚖️ Bias-reduced screening process

### For Job Seekers
- 🎯 Detailed skill gap analysis
- 📝 Personalized action recommendations
- 📊 Comprehensive PDF reports
- 🛠️ Resume optimization suggestions
- 🎓 Custom learning path generation

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Backend:** FastAPI
- **AI/LLM:** Groq (Llama-3)
- **PDF Processing:** PyMuPDF
- **Data Handling:** Pandas
- **Database:** MongoDB

## 🚀 Getting Started

### Prerequisites
```bash
- Python 3.10+
- MongoDB
- Groq API access
```

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd resume-ats-project
```

2. Set up environment variables
```bash
# Create .env file with:
MONGO_URI=your_mongodb_connection_string
GROQ_API_KEY=your_groq_api_key
```

3. Install dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
pip install -r requirements.txt
```

4. Run the application
```bash
# Backend
uvicorn app.main:app --reload

# Frontend
streamlit run app.py
```

## 📊 Project Structure

```
resume-ats-project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── pages/
│   ├── app.py
│   └── requirements.txt
└── .env
```

## 💡 Usage

### HR Module
1. Navigate to HR dashboard
2. Upload multiple resumes and job description
3. Get instant AI-powered analysis
4. Export results to CSV

### Job Seeker Module
1. Upload resume and target job description
2. Receive detailed skill gap analysis
3. Get personalized action recommendations
4. Download comprehensive PDF report

## 🔒 Security

- Environment variables for sensitive credentials
- Secure API endpoints
- No storage of sensitive resume data
- Compliance with data protection standards

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions and support, please open an issue in the repository or contact the maintainers.

---

*Built with ❤️ using Python, FastAPI, and Groq LLM*


cd resume-ats-project
uvicorn backend.app.main:app --reload

streamlit run frontend/app.py

cd resume-ats-project
uvicorn backend.app.main:app --reload
streamlit run frontend/app.py
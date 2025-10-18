import streamlit as st
import requests
import io
import pandas as pd

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="HireSense | HR Dashboard", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 2rem; font-weight: 700; color: #4CAF50; }
    .section-header { font-size: 1.2rem; color: #CCCCCC; margin-top: 1.5rem; }
    .info-box {
        background: #1E1E1E; border-left: 4px solid #4CAF50; padding: 1rem; border-radius: 8px;
        color: #DDD; margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📂 HR Resume Matcher Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="info-box">Easily upload job descriptions and candidate resumes, and let HireSense score them using AI-powered matching and LLM feedback.</div>', unsafe_allow_html=True)

# --- Upload JD ---
st.markdown('<div class="section-header">1️⃣ Upload Job Description</div>', unsafe_allow_html=True)
jd_file = st.file_uploader("Upload JD (PDF or text)", type=["pdf", "txt"])

jd_text = None
if jd_file is not None:
    jd_text = jd_file.read().decode("utf-8", errors="ignore")

# --- Upload Resumes ---
st.markdown('<div class="section-header">2️⃣ Upload Candidate Resumes</div>', unsafe_allow_html=True)
resumes = st.file_uploader("Upload multiple resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if st.button("📤 Upload Resumes"):
    if resumes:
        files = [("resumes", (f.name, f, "application/pdf")) for f in resumes]
        response = requests.post(f"{BACKEND_URL}/parser/upload-resumes", files=files)
        if response.status_code == 200:
            data = response.json()
            st.success(f"✅ Uploaded {data['uploaded']} resumes under Bulk ID: {data['bulk_upload_id']}")
            st.session_state["bulk_upload_id"] = data["bulk_upload_id"]
        else:
            st.error(f"Upload failed! {response.text}")

# --- Score Resumes ---
st.markdown('<div class="section-header">3️⃣ Score Resumes Against JD</div>', unsafe_allow_html=True)
use_llm = st.checkbox("Use LLM for scoring", value=True)

if st.button("⚙️ Run Scoring"):
    if jd_text and "bulk_upload_id" in st.session_state:
        bulk_id = st.session_state["bulk_upload_id"]
        response = requests.post(f"{BACKEND_URL}/hr/score-resumes-by-session",
                                 data={"jd_text": jd_text, "bulk_upload_id": bulk_id, "use_llm": use_llm})
        if response.status_code == 200:
            data = response.json()
            st.success("✅ Scoring completed successfully!")

            st.subheader("📈 Results Overview")
            results = []
            for res in data.get("results", []):
                results.append({
                    "Candidate Name": res.get("candidate_name", "N/A"),
                    "Filename": res.get("filename", "N/A"),
                    "Score": res.get("ats_score", "N/A"),
                    "Reason": res.get("reason", "N/A"),
                    "Feedback": res.get("feedback", "N/A"),
                    "Improvements": "; ".join(res.get("improvements", [])),
                })

            if results:
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            st.info(f"📊 Statistics: {data.get('statistics', {})}")

        else:
            st.error(f"Scoring failed! {response.text}")
    else:
        st.warning("Please upload JD and resumes first.")

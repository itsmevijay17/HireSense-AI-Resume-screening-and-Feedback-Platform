import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="HireSense | Job Seeker Analyzer", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 2rem; font-weight: 700; color: #4CAF50; }
    .info-box { background: #1E1E1E; border-left: 4px solid #4CAF50; padding: 1rem; border-radius: 8px; color: #DDD; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🧩 Job Seeker Skill Gap Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="info-box">Upload your resume and compare it to your dream job’s requirements. Discover missing skills and get personalized recommendations.</div>', unsafe_allow_html=True)

resume = st.file_uploader("📄 Upload your resume (PDF or TXT)", type=["pdf", "txt"])
jd_text = st.text_area("📝 Paste the Job Description here")
candidate_name = st.text_input("👤 Your Name")

if st.button("🔍 Analyze Gap"):
    if resume and jd_text:
        files = {"resume": resume}
        data = {"job_description": jd_text}
        resp = requests.post(f"{BACKEND_URL}/jobseeker/analyze-gap", files=files, data=data)
        if resp.status_code == 200:
            result = resp.json()
            st.subheader("✅ Matched Skills")
            st.write([s["skill"] for s in result["skills_analysis"]["matched_skills"]])
            st.subheader("❌ Missing Skills")
            st.write([s["skill"] for s in result["skills_analysis"]["missing_skills"]])
            st.subheader("🚀 Priority Actions")
            for action in result["priority_actions"]:
                st.write(f"- {action['action']} (Impact: {action['impact']})")
        else:
            st.error("Analysis failed.")

if st.button("📄 Generate PDF Report"):
    if resume and jd_text and candidate_name:
        files = {"resume": resume}
        data = {"job_description": jd_text, "candidate_name": candidate_name}
        resp = requests.post(f"{BACKEND_URL}/jobseeker/export-report", files=files, data=data)
        if resp.status_code == 200:
            st.download_button(
                label="⬇️ Download PDF Report",
                data=resp.content,
                file_name=f"{candidate_name}_gap_report.pdf",
                mime="application/pdf"
            )
        else:
            st.error("PDF generation failed.")

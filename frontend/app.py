import streamlit as st

st.set_page_config(page_title="HireSense | AI-Powered ATS", layout="wide")

# --- Custom Styles ---
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4CAF50;
        text-align: center;
        margin-top: 1rem;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #CCCCCC;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        transition: 0.3s;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        border-color: #4CAF50;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: #888;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown('<div class="main-title">HireSense — AI-Powered Resume ATS 🚀</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Smart. Fast. Fair. Empowering HRs and Job Seekers with AI.</div>', unsafe_allow_html=True)

# --- Intro Text ---
st.write(
    """
    ### Why HireSense?
    Traditional hiring can be time-consuming and biased. **HireSense** revolutionizes this with AI — 
    automatically analyzing, scoring, and interpreting resumes to match them perfectly with your job descriptions.

    Whether you're an HR professional looking to shortlist candidates, or a job seeker aiming to
    understand and improve your resume — HireSense makes it effortless, accurate, and insightful.
    """
)

# --- Feature Cards ---
st.markdown("### ✨ Core Features")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
        <div class="feature-card">
        <h4>🤖 Automated Resume Scoring</h4>
        <p>Leverage advanced NLP models to rank and match resumes against job descriptions with precision.</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="feature-card">
        <h4>📊 Skill Gap Analysis</h4>
        <p>Help job seekers identify missing skills and actionable improvement steps for better employability.</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="feature-card">
        <h4>💬 AI-Powered Feedback</h4>
        <p>Receive personalized suggestions and improvement areas, ensuring every profile gets fair visibility.</p>
        </div>
    """, unsafe_allow_html=True)

# --- CTA Buttons ---
st.markdown("### 🚀 Get Started")
colA, colB = st.columns(2)
with colA:
    if st.button("👔 For HR Professionals"):
        st.switch_page("pages/hr_module.py")

with colB:
    if st.button("🧑‍💼 For Job Seekers"):
        st.switch_page("pages/job_seeker_module.py")

# --- Footer ---
st.markdown("""
    <div class="footer">
        <br>
        <p>Backend should be running at <code>http://127.0.0.1:8000</code></p>
        <p>© 2025 HireSense — Empowering Smarter Hiring Decisions</p>
    </div>
""", unsafe_allow_html=True)

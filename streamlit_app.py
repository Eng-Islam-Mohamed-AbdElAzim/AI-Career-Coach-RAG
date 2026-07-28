import streamlit as st
import requests

st.set_page_config(page_title="AI Career Coach", page_icon="🤖", layout="wide")

st.title("🤖 AI Career Coach")
st.caption(
    "Upload your resume — the analysis runs on your Kaggle GPU notebook "
    "and is streamed back here through an ngrok tunnel."
)

# ----------------------------------------------------------------------
# Backend URL configuration
# ----------------------------------------------------------------------
default_url = st.secrets.get("KAGGLE_API_URL", "") if hasattr(st, "secrets") else ""

with st.sidebar:
    st.header("⚙️ Settings")
    api_url = st.text_input(
        "Kaggle ngrok API URL",
        value=default_url,
        placeholder="https://xxxx-xx-xx-xxx-xx.ngrok-free.app",
        help=(
            "Paste the public URL printed by the last cell of your Kaggle "
            "notebook (kaggle_server_cells.py, CELL 45). It changes every "
            "time you restart the Kaggle server unless you use a paid "
            "ngrok static domain."
        ),
    )
    st.markdown("---")
    if api_url:
        if st.button("Test connection"):
            try:
                r = requests.get(f"{api_url.rstrip('/')}/health", timeout=10)
                if r.ok:
                    st.success("Connected to Kaggle backend ✅")
                else:
                    st.error(f"Backend responded with status {r.status_code}")
            except Exception as e:
                st.error(f"Could not reach backend: {e}")

st.markdown("---")

# ----------------------------------------------------------------------
# Resume upload
# ----------------------------------------------------------------------
uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

analyze_clicked = st.button("Analyze Resume", type="primary", disabled=not uploaded_file)

if analyze_clicked:
    if not api_url:
        st.warning("Please enter your Kaggle ngrok API URL in the sidebar first.")
        st.stop()

    with st.spinner("Analyzing resume on Kaggle GPU... this can take a minute or two"):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = requests.post(
                f"{api_url.rstrip('/')}/analyze", files=files, timeout=600
            )
        except Exception as e:
            st.error(f"Request failed: {e}")
            st.stop()

    if not response.ok:
        st.error(f"Backend error ({response.status_code}): {response.text}")
        st.stop()

    data = response.json()
    if "error" in data:
        st.error(f"Backend error: {data['error']}")
        with st.expander("Traceback"):
            st.code(data.get("trace", ""))
        st.stop()

    candidate_skills = data.get("candidate_skills", {})
    comparison = data.get("comparison", {})
    roadmap = data.get("roadmap", {})

    st.success("Analysis complete!")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Current Skills")
        for skill in comparison.get("current_skills", []):
            st.markdown(f"- ✅ {skill}")

    with col2:
        st.subheader("⚠️ Missing Skills")
        for skill in comparison.get("missing_skills", []):
            st.markdown(f"- ❌ {skill}")

    st.markdown("---")
    st.subheader("💼 Recommended Jobs")
    for job in comparison.get("recommended_jobs", []):
        title = job.get("title", "Untitled role") if isinstance(job, dict) else str(job)
        with st.expander(title):
            if isinstance(job, dict):
                for skill in job.get("skills", []):
                    st.markdown(f"- {skill}")

    st.markdown("---")
    st.subheader("📚 Learning Roadmap")
    for item in roadmap.get("roadmap", []):
        skill = item.get("skill", "") if isinstance(item, dict) else str(item)
        with st.expander(skill):
            if isinstance(item, dict):
                for resource in item.get("learning_resources", []):
                    st.markdown(f"- {resource}")

    st.markdown("---")
    st.subheader("🚀 Improvement Plan")
    for item in roadmap.get("improvement_plan", []):
        skill = item.get("skill", "") if isinstance(item, dict) else str(item)
        st.markdown(f"**🎯 {skill}**")
        if isinstance(item, dict):
            for step in item.get("improvement_steps", []):
                st.markdown(f"- {step}")

    with st.expander("Raw extracted skills (debug)"):
        st.json(candidate_skills)

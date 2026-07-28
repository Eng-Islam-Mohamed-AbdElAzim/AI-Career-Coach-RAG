# ============================================================================
# PASTE THESE AS NEW CELLS AT THE END OF YOUR EXISTING KAGGLE NOTEBOOK
# (after your current last cell — the one that pip installs streamlit/pyngrok)
#
# They reuse variables already defined earlier in your notebook:
#   embedding_model, index, chunks, tokenizer, llm,
#   ask_llm(), search_faiss(), read_resume()
#
# Do NOT run this as a standalone .py file — it's meant to be split into
# separate Kaggle notebook cells, marked "# --- CELL N ---" below.
# ============================================================================

# --- CELL 42: install server deps ---
!pip install -q fastapi uvicorn python-multipart pyngrok nest_asyncio

# --- CELL 43: set your ngrok authtoken ---
# 1. Sign up free at https://ngrok.com
# 2. Copy your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
# 3. In Kaggle: Add-ons > Secrets > add a secret named NGROK_AUTH_TOKEN
#    (safer than pasting the token directly in the notebook)

from kaggle_secrets import UserSecretsClient

user_secrets = UserSecretsClient()
NGROK_AUTH_TOKEN = user_secrets.get_secret("NGROK_AUTH_TOKEN")

from pyngrok import ngrok
ngrok.set_auth_token(NGROK_AUTH_TOKEN)


# --- CELL 44: define the API ---
import json
import re
import shutil
import tempfile
import traceback

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="AI Career Coach API")

# Allow the local Streamlit app to call this API from your machine
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def safe_json_parse(raw_text):
    """
    LLMs sometimes wrap JSON in markdown fences or add stray text.
    This pulls out the first {...} block and parses it safely.
    """
    text = raw_text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM output:\n{raw_text}")

    return json.loads(match.group(0))


def run_career_coach_pipeline(resume_text: str):
    # 1. Extract skills from resume
    skills_prompt = f"""
You are an AI career coach.

Below is a student's resume.

Resume:

{resume_text}

Extract ONLY the technical skills.

Return ONLY JSON.

{{
    "skills":[]
}}
"""
    skills_raw = ask_llm(skills_prompt)
    candidate_skills = safe_json_parse(skills_raw)

    # 2. Retrieve relevant jobs/resources from FAISS
    query = " ".join(candidate_skills["skills"])
    retrieved_documents = search_faiss(
        query, embedding_model, index, chunks, k=5
    )
    context = "\n\n".join(retrieved_documents)

    # 3. Compare candidate vs retrieved jobs
    comparison_prompt = f"""
You are an AI Career Coach.

Candidate Skills

{candidate_skills["skills"]}

Retrieved Knowledge

{context}

Compare the candidate with the retrieved jobs.

Return ONLY JSON.

{{
"current_skills":[],
"missing_skills":[],
"recommended_jobs":[]
}}
"""
    comparison_raw = ask_llm(comparison_prompt)
    comparison = safe_json_parse(comparison_raw)

    # 4. Generate roadmap + improvement plan
    roadmap_prompt = f"""
You are an AI Career Coach.

Candidate Skills

{comparison["current_skills"]}

Missing Skills

{comparison["missing_skills"]}

Retrieved Knowledge

{context}

Generate

1 Learning Roadmap

2 Improvement Plan

Return ONLY JSON

{{
"roadmap":[],
"improvement_plan":[]
}}
"""
    roadmap_raw = ask_llm(roadmap_prompt)
    roadmap = safe_json_parse(roadmap_raw)

    return {
        "candidate_skills": candidate_skills,
        "comparison": comparison,
        "roadmap": roadmap,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        resume_text = read_resume(tmp_path)
        result = run_career_coach_pipeline(resume_text)
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()},
        )


# --- CELL 45: start the server + expose it with ngrok ---
import nest_asyncio
import uvicorn
import threading

nest_asyncio.apply()

# Kill any previous tunnels from an earlier run in this session
ngrok.kill()

public_url = ngrok.connect(8000)
print("=" * 70)
print(f"PUBLIC API URL: {public_url}")
print("Copy this into your local Streamlit app's sidebar / secrets.toml")
print("=" * 70)


def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)


thread = threading.Thread(target=run_server, daemon=True)
thread.start()

# Keep this cell "running" — do not stop it, or the tunnel + server die.
# In Kaggle, leave the notebook session active (Save & Run All won't work
# for a live server — you need an interactive session with the internet
# toggle ON, and keep the tab open / session alive).

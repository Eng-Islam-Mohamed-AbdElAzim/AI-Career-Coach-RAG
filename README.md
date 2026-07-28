# AI Career Coach — Streamlit + Kaggle (via ngrok)

Turns your Kaggle RAG notebook into a live backend that a local Streamlit
app talks to, so you can upload a resume PDF from your own machine while
the heavy model (Mistral-7B) runs on Kaggle's free GPU.

```
Browser → Streamlit (VS Code, local) → ngrok tunnel → FastAPI (Kaggle notebook, GPU)
```

## Project structure

```
ai-career-coach/
├── streamlit_app.py              # local UI — upload resume, view report
├── requirements.txt               # local Python deps
├── .streamlit/secrets.toml.example
├── .gitignore
├── kaggle/
│   └── kaggle_server_cells.py     # paste into your Kaggle notebook as new cells
└── README.md
```

---

## Part 1 — Kaggle: turn your notebook into an API

1. Open your existing Kaggle notebook (the one that builds `chunks`,
   `index`, `embedding_model`, `tokenizer`, `llm`, `ask_llm`, `search_faiss`,
   `read_resume`).
2. Open `kaggle/kaggle_server_cells.py` from this project. It's split into
   5 labeled cells (`# --- CELL 42 ---` through `# --- CELL 45 ---`).
3. Copy each cell's code into a **new cell at the end of your Kaggle
   notebook**, in order.
4. Get a free ngrok account and authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
5. In Kaggle: **Add-ons → Secrets** → add a secret named `NGROK_AUTH_TOKEN`
   with that token (don't paste it directly into the notebook).
6. Make sure the notebook session has **Internet: On** (Settings panel on
   the right).
7. Run all cells, including the new ones, in an **interactive session**
   (not "Save & Run All" — that doesn't keep a server alive). The last
   cell prints something like:

   ```
   PUBLIC API URL: NgrokTunnel: "https://xxxx-xx-xx-xxx-xx.ngrok-free.app" -> "http://localhost:8000"
   ```

8. Copy the `https://....ngrok-free.app` URL — that's your backend.
   Keep the Kaggle notebook session running; if it stops or the kernel
   restarts, the URL changes and you'll need to grab the new one.

## Part 2 — VS Code: run Streamlit locally

1. Open this folder (`ai-career-coach/`) in VS Code.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. (Optional but convenient) Save your Kaggle URL so you don't retype it:

   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # then edit .streamlit/secrets.toml and paste your ngrok URL
   ```

4. Run the app:

   ```bash
   streamlit run streamlit_app.py
   ```

5. In the sidebar, paste (or confirm) the ngrok URL, click **Test
   connection**, then upload a resume PDF and click **Analyze Resume**.

---

## Part 3 — Connect this VS Code project to GitHub

**Easiest way (VS Code UI):**
1. Open the Source Control panel (`Ctrl+Shift+G` / `Cmd+Shift+G`).
2. Click **Initialize Repository**.
3. Stage and commit your files (write a commit message like
   `Initial commit: streamlit + kaggle career coach`).
4. Click **Publish to GitHub** in the Source Control panel (sign in to
   GitHub if prompted). Choose public or private.

**Or via terminal:**

```bash
git init
git add .
git commit -m "Initial commit: streamlit + kaggle career coach"

# Create the repo on GitHub first (github.com/new), then:
git remote add origin https://github.com/<your-username>/ai-career-coach.git
git branch -M main
git push -u origin main
```

`.streamlit/secrets.toml` is already in `.gitignore` so your ngrok URL
(which changes each session anyway) never gets committed.

---

## Notes / gotchas

- **The ngrok URL changes** every time you restart the Kaggle server
  (free ngrok tier has no fixed subdomain). Update it in the Streamlit
  sidebar or `secrets.toml` each session.
- **Keep the Kaggle notebook tab open** — closing it or letting the
  session idle-timeout kills the API server.
- The `/analyze` endpoint can take 30–120+ seconds depending on Kaggle's
  GPU allocation and Mistral-7B's generation speed — this is expected.
- If `requests.post` to `/analyze` times out, increase the `timeout=600`
  value in `streamlit_app.py`.
- For a permanent (non-changing) URL, ngrok offers paid static domains —
  otherwise Kaggle + free ngrok is inherently a "restart = new URL" setup.

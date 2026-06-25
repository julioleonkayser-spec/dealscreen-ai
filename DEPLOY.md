# DealScreen AI — Deployment Guide

---

## 1. Local run

```bash
cd ~/Desktop/pd-hackathon
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

The app will be at **http://localhost:8501**

For your API keys, open `.streamlit/secrets.toml` (git-ignored) and replace the placeholders:

```toml
ANTHROPIC_API_KEY = "sk-ant-your-real-key-here"
EXA_API_KEY = "your-exa-key-here"   # optional
```

Alternatively, copy `.env.example` to `.env` and fill in your key — the app checks `os.getenv` before `st.secrets`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 2. Push to GitHub

1. Go to **github.com → New repository** → name it (e.g. `dealscreen-ai`) → set to **Public** → **do not** initialize with README → click **Create repository**.

2. From your terminal, inside this folder:

```bash
git remote add origin https://github.com/<your-username>/dealscreen-ai.git
git branch -M main
git push -u origin main
```

Replace `<your-username>` with your actual GitHub username.

---

## 3. Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **"Create app"**.
3. Select your repository (`dealscreen-ai`) and branch (`main`).
4. Set the main file to **`app.py`**.
5. Expand **"Advanced settings → Secrets"** and paste:
   ```
   ANTHROPIC_API_KEY = "sk-ant-your-real-key-here"
   ```
6. Click **Deploy**.

Streamlit will build the environment from `requirements.txt` and give you a public URL like:
```
https://dealscreen-ai.streamlit.app
```

> **Note:** The first deploy takes ~2–3 minutes while dependencies install.
> Subsequent deploys (after a git push) are faster.

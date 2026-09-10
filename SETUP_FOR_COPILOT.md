# Setup Instructions — E-commerce-Chatbot (CustomerServiceAI)

This doc is written to be pasted directly into GitHub Copilot Chat (or
followed manually) to get this project running after pulling the
`3-agent-mvp` branch/PR. Paste the whole thing to Copilot and ask it to
"run these steps in order and fix any errors that come up."

## What this PR changes (context for Copilot)

The project was a partial prototype (broken import, Windows-only
hardcoded file paths, a couple of tool bugs). This PR completes the
3-agent architecture (Supervisor, Enquiry Resolution, Complaint
Resolution agents + deterministic tools + a CSV-backed database +
4 human-review Streamlit pages) and fixes those bugs, so the setup
below is a clean run from a fresh clone — no manual DB setup needed.

## Prerequisites

- Python 3.10 or newer (`python --version` / `python3 --version`)
- Git
- Internet access to these domains (see "Org laptop / restricted
  network" troubleshooting below if any are blocked):
  - `pypi.org` (installing packages)
  - `huggingface.co` (downloading the embedding model, ~90MB, one-time)
  - `generativelanguage.googleapis.com` and `aistudio.google.com`
    (Gemini API calls)

## Step-by-step setup

Run these from the repo root (the folder containing `app.py`).

**1. Create and activate a virtual environment**

Windows (PowerShell):
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Windows (cmd.exe):
```
python -m venv venv
venv\Scripts\activate.bat
```

macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```
This installs LangChain/LangGraph, FAISS, sentence-transformers, and a
few other libraries. `paddleocr`/`paddlepaddle` in this file are large
(multi-GB) and currently unused by the app (image/video evidence is
routed to a human reviewer instead of OCR) — if the install is slow or
fails on those two specifically, it's safe to remove those two lines
from `requirements.txt` and re-run `pip install -r requirements.txt`.

**3. Create the `.env` file**

Copy `.env.example` to `.env` in the repo root, and fill in a real
Gemini API key:
```
GOOGLE_API_KEY=<paste key here>
```

Get the key from **https://aistudio.google.com/api-keys** — click
"Create API key". **Important**: if the key you're given starts with
`AQ.` and calls fail with a `401 UNAUTHENTICATED` /
`ACCESS_TOKEN_TYPE_UNSUPPORTED` error, that means AI Studio issued an
"auth key" (OAuth-scoped) instead of a "Standard API key" — go back
and look for a way to explicitly generate a **Standard API key**
instead. (We hit this ourselves — it's a real gotcha, not a config
mistake.)

If the key works but calls fail with a `404` saying a model like
`gemini-2.5-flash` "is no longer available", the account's model
access has changed. Open `config/setting.py` and change:
```python
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
```
to whatever current model name Google's error message recommends (or
set a `GEMINI_MODEL=<name>` line in `.env` instead of editing code).

**4. Build the vector store** (search index over the policy documents
— this is not committed to git, it must be built locally):
```bash
python -m rag.build_vectorstore
```
Expected output ends with `Vector Store Saved Successfully`. This step
needs `huggingface.co` access to download the embedding model the
first time it runs.

**5. Run the app**
```bash
streamlit run app.py
```
This opens a browser tab at `http://localhost:8501`. If it doesn't
open automatically, go to that URL manually.

## How to verify it's working

- On the main chat page, type: `Can I return a laptop after 15 days?`
  — should get a policy-grounded answer (not an error).
- Type something like: `My laptop screen arrived cracked` — should
  start a complaint intake (asks for Order ID, then issue type, then a
  description).
- In the left sidebar, there's a page picker — `Case Manager`,
  `Evidence Reviewer`, `Customer Care`, `Department Tasks` are the
  human-review screens for the workflow this complaint goes through.

## Troubleshooting on a restricted/org laptop

- **PowerShell blocks running `Activate.ps1`** ("running scripts is
  disabled on this system"): use the `cmd.exe` activation command
  above instead (`venv\Scripts\activate.bat`), or run PowerShell as:
  `powershell -ExecutionPolicy Bypass -File venv\Scripts\Activate.ps1`
- **`pip install` fails/times out** — the org network likely requires
  a proxy. Ask IT for the proxy address, then either set it as an
  environment variable before installing:
  ```
  set HTTPS_PROXY=http://proxy.company.com:port
  set HTTP_PROXY=http://proxy.company.com:port
  ```
  or pass it directly: `pip install --proxy http://proxy.company.com:port -r requirements.txt`
- **No admin rights to install Python packages** — add `--user` to the
  pip install command, or use a Python installed without admin rights
  (e.g. from the Microsoft Store, or a portable Python).
- **`huggingface.co` or `generativelanguage.googleapis.com` is
  blocked by the corporate firewall** — the app cannot function
  without access to at least the Google Gemini endpoint (it's used for
  intent classification, answers, and safety checks) and, once, the
  HuggingFace endpoint (only for the one-time embedding model
  download). Ask IT to allowlist these domains, or run the setup
  once on an unrestricted network/hotspot to get past the one-time
  download, then switch back.
- **Antivirus flags the `venv` folder or blocks script execution** —
  this is a standard local Python virtual environment with no network
  listeners besides the Streamlit dev server on `localhost:8501`;
  whitelisting the project folder in the antivirus tool should resolve
  it.

## After setup

Once it's running locally and confirmed working, let Ayush know so the
PR can be opened against this repo.

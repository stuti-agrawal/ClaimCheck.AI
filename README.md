# ClaimCheck.AI — Agentic Fact Verification for Calls

**ClaimCheck.AI** is an multi-agent AI platform that turns meeting audio (Zoom/phone) into an evidence-backed report:
1) **ASR Agent** → transcript + timestamps  
2) **Claim Extraction (watsonx.ai LLM)** → JSON claims  
3) **Evidence Retrieval (watsonx.ai Embeddings + FAISS + optional Rerank)** → KB hits  
4) **Verification (watsonx.ai LLM)** → supported/refuted/insufficient + citations  
5) **Summarizer (watsonx.ai LLM)** → executive summary + action items

## ✨ Why it matters

High-stakes calls contain promises and metrics (SLA, compliance, finance). ClaimCheck.AI verifies statements against your **trusted KB** so decisions are grounded in facts—not memory.
git branch -M main

---

## 🔧 Project structure

```
claim-check/
├─ app/
│  ├─ agents/
│  │  ├─ claims.py            # Claim extractor (watsonx.ai Prompt Lab / LLM)
│  │  ├─ retriever.py         # IBM embeddings + FAISS + optional rerank
│  │  ├─ verifier.py          # LLM verdicts (supported/refuted/insufficient)
│  │  └─ summarizer.py        # LLM executive summary + action items
│  ├─ core/
│  │  ├─ config.py            # env wiring (IBM base url, project, keys)
│  │  └─ json_utils.py        # robust JSON extraction from LLM outputs
│  ├─ schemas/                # pydantic models (Claim, Evidence, Verdict, CallReport)
│  ├─ services/
│  │  └─ asr.py               # Speech to Text model
│  └─ main.py                 # FastAPI: /health, /process-audio, /process-transcript
├─ kb/
│  ├─ snippets.jsonl          # your knowledge base (facts; one JSON per line)
│  └─ index/                  # FAISS index (auto-built)
├─ data/audio/                # demo audio files
├─ .env                       # local secrets (NOT committed)
├─ .env.sample                # template for env vars (safe to commit)
├─ requirements.txt
└─ README.md
```

---

## 🧪 Quick start

### 1) Python env
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure IBM (edit `.env`)
Copy the sample and fill in values from your IBM Cloud / watsonx project.

```bash
cp .env.sample .env
```

**Required env keys:**
```
# IBM Core
WATSONX_BASE_URL=https://us-south.ml.cloud.ibm.com
WATSONX_PROJECT_ID=<your-watsonx-project-id>
WATSONX_API_KEY=<your-ibm-cloud-api-key>
IBM_API_VERSION=2023-05-29

# Models
IBM_EMBEDDINGS_MODEL_ID=ibm/granite-embedding-107m-multilingual   # 384-dim
IBM_RERANK_MODEL_ID=ibm/slate-30m-english-rtrvr-v2                 # optional
IBM_VERIFIER_MODEL_ID=ibm/granite-3-8b-instruct
IBM_SUMMARY_MODEL_ID=ibm/granite-3-8b-instruct

# Speech to Text (IBM)
IBM_STT_URL=<your-ibm-stt-instance-url>   # e.g. https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/XXXX
IBM_STT_APIKEY=<your-ibm-stt-api-key>

# Whisper fallback (optional)
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

### 3) Seed the KB
Put your facts in `kb/snippets.jsonl` (one JSON per line). Example:

```jsonl
{"doc_id":"uptime_q2_report","source":"Global Uptime Dashboard","snippet":"Q2 2025 uptime was 99.982% globally; LATAM outage lowered regional uptime to 99.965%.","metadata":{"quarter":"Q2","year":2025}}
```

If you change the KB, rebuild the index by deleting the `kb/index/` folder.

### 4) Run the API
```bash
# macOS OpenMP fix (optional) + run
KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1 uvicorn app.main:app --reload
```

### 5) Try it

**Transcript path (no audio):**
```bash
curl -X POST http://127.0.0.1:8000/process-transcript   -H "Content-Type: application/json"   -d '{"text":"We achieved 99.99% uptime in Q2. P95 latency under 200 ms globally. Default retention is 30 days."}'
```

**Audio path (IBM STT):**
```bash
curl -X POST http://127.0.0.1:8000/process-audio   -F "file=@data/audio/demo_call.wav"
```

**Health:**
```bash
curl http://127.0.0.1:8000/health/ibm
```

---

## 🧠 How it works (agentic)

## 🧠 Core Concepts and Models

ClaimCheck.AI combines modern **agentic AI** orchestration with core NLP, IR, and speech processing techniques. Each agent is powered by a specific model or algorithm:

| Agent         | Function                             | Model/Tool Used                              | Concepts |
|---------------|--------------------------------------|-----------------------------------------------|----------|
| ASR Agent     | Audio transcription + timestamps     | `IBM Speech-to-Text` or `Whisper`             | Automatic Speech Recognition (ASR), Diarization |
| Claim Extractor | Turns transcript → atomic claims    | `watsonx.ai` Prompt Lab + `granite-3-8b-instruct` | Information Extraction, Prompt Engineering |
| Retriever     | Find matching KB facts               | `granite-embedding-107m-multilingual`, FAISS, optional `slate-30m-rtrvr` | Embedding-based Retrieval, Vector Search, Reranking |
| Verifier      | Evaluate support/refute status       | `granite-3-8b-instruct`                       | Fact Verification, Retrieval-Augmented Generation (RAG) |
| Summarizer    | Generate exec summary + action items | `granite-3-8b-instruct`                       | Abstractive Summarization, Plan Extraction |


---

## 🛡️ Notes on data & security
- Do **not** commit `.env` or audio with sensitive content.  
- Use IBM Cloud secrets manager / vault in production.  
- All third-party calls are behind explicit env flags; the pipeline fails safe (insufficient) if evidence is missing.

---

## 🧰 Troubleshooting
- **Embeddings 400** → ensure `version` query param, body includes `"inputs"` and `"model_id"`.  
- **FAISS dim mismatch** → delete `kb/index/` after changing embedding model.  
- **OpenMP error (macOS)** → set `KMP_DUPLICATE_LIB_OK=TRUE` and `OMP_NUM_THREADS=1`.  
- **JSON parse errors** → we use a robust extractor; check server logs `[RAW OUTPUT]`.



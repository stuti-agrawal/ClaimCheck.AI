# app/main.py
import os
from fastapi import FastAPI
from fastapi import Body
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.core.orchestrator import process_call
from app.core.ibm_sanity import sanity_embeddings, sanity_generation

app = FastAPI(title="ClaimCheck")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ClaimCheck"}

@app.get("/health/ibm")
def health_ibm():
    emb = sanity_embeddings()
    claim = sanity_generation(os.getenv("IBM_CLAIM_MODEL_ID",""), "Say OK")
    verify = sanity_generation(os.getenv("IBM_VERIFIER_MODEL_ID",""), "Say OK")
    return {"embeddings": emb, "claim_gen": claim, "verify_gen": verify}


@app.post("/process-transcript")
def process_transcript(text: str = Body(..., embed=True)):
    """
    Accepts raw transcript text and returns a CallReport JSON.
    For now, the orchestrator returns a dummy report (no AI).
    """
    report = process_call(transcript=text)
    return report

@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    path = f"data/audio/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    return process_call(audio_path=path)
# app/core/ibm_sanity.py
import os, requests, json, numpy as np
from app.core.config import WATSONX_BASE_URL, WATSONX_PROJECT, WATSONX_API_KEY
from app.utils.auth import get_ibm_iam_token

VERSION = os.getenv("IBM_API_VERSION", "2023-05-29")
EMB = os.getenv("IBM_EMBEDDINGS_MODEL_ID", "")
CLAIM = os.getenv("IBM_CLAIM_MODEL_ID", "")
VERIFY = os.getenv("IBM_VERIFIER_MODEL_ID", "")


def sanity_embeddings():
    tok = get_ibm_iam_token()
    r = requests.post(
        f"{WATSONX_BASE_URL.rstrip('/')}/ml/v1/text/embeddings?version={VERSION}",
        headers={"Authorization":f"Bearer {tok}","Accept":"application/json","Content-Type":"application/json"},
        json={"inputs":["probe"],"model_id":EMB,"project_id":WATSONX_PROJECT},
        timeout=60,
    )
    r.raise_for_status()
    j = r.json()
    items = j.get("data") or j.get("results") or []
    dim = len(items[0]["embedding"]) if items else 0
    return {"ok": True, "dim": dim}


def sanity_generation(model_id: str, prompt: str):
    tok = get_ibm_iam_token()
    r = requests.post(
        f"{WATSONX_BASE_URL.rstrip('/')}/ml/v1/text/generation?version={VERSION}",
        headers={"Authorization":f"Bearer {tok}","Accept":"application/json","Content-Type":"application/json"},
        json={
            "input": prompt,
            "model_id": model_id,
            "project_id": WATSONX_PROJECT,
            "parameters": {"decoding_method":"greedy","max_new_tokens":64}
        },
        timeout=90,
    )
    r.raise_for_status()
    txt = (r.json().get("results") or [{}])[0].get("generated_text","")
    return {"ok": True, "preview": txt[:120]}

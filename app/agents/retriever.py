# app/agents/retriever.py
from typing import List, Tuple, Dict
import os, json, numpy as np, faiss, requests

from app.schemas.claim import Claim
from app.schemas.evidence import Evidence
from app.core.config import WATSONX_BASE_URL as _BASE, WATSONX_PROJECT as _PROJECT, WATSONX_API_KEY as _APIKEY

BASE_URL = (_BASE or "").rstrip("/")          # avoid //ml
PROJECT_ID = _PROJECT
API_KEY = _APIKEY
EMB_MODEL_ID = os.getenv("IBM_EMBEDDINGS_MODEL_ID", "").strip()   # <-- REQUIRED
RERANK_MODEL_ID = os.getenv("IBM_RERANK_MODEL_ID", "").strip()    # optional

IDX_DIR   = "kb/index"
IDX_PATH  = f"{IDX_DIR}/kb.index"
META_PATH = f"{IDX_DIR}/kb_meta.json"
SNIPPETS  = "kb/snippets.jsonl"

# ---------- IBM helpers ----------
_tok, _exp = None, 0
def _ibm_token():
    import time
    global _tok, _exp
    now = time.time()
    if _tok and now < _exp - 60:
        return _tok
    r = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": API_KEY
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json(); _tok = data["access_token"]; _exp = now + 3000
    return _tok

def _assert_ibm_ready():
    missing = []
    if not BASE_URL: missing.append("WATSONX_BASE_URL")
    if not PROJECT_ID: missing.append("WATSONX_PROJECT_ID")
    if not API_KEY: missing.append("WATSONX_API_KEY")
    if not EMB_MODEL_ID: missing.append("IBM_EMBEDDINGS_MODEL_ID")
    if missing:
        raise RuntimeError(f"IBM embeddings not configured. Missing: {', '.join(missing)}")

VERSION = os.getenv("IBM_API_VERSION", "2023-05-29")
BASE_URL = BASE_URL.rstrip("/")

def _ibm_embed(texts: list[str]) -> np.ndarray:
    url = f"{BASE_URL}/ml/v1/text/embeddings?version={VERSION}"
    hdr = {"Authorization": f"Bearer {_ibm_token()}",
           "Accept": "application/json",
           "Content-Type": "application/json"}
    payload = {
        "inputs": texts,                  # NOTE: plural
        "model_id": EMB_MODEL_ID,
        "project_id": PROJECT_ID
    }
    r = requests.post(url, headers=hdr, json=payload, timeout=60)
    r.raise_for_status()
    j = r.json()

    # Accept either "data": [{"embedding": [...]}, ...]  OR
    # "results": [{"embedding": [...]}, ...]
    items = None
    if isinstance(j, dict):
        if "data" in j:
            items = j["data"]
        elif "results" in j:
            items = j["results"]

    if not items or not isinstance(items, list):
        # Print full response once to help diagnose, then fall back
        print(f"[retriever] Unexpected embeddings schema: {j}")
        raise RuntimeError("Embeddings response missing 'data'/'results'")

    vecs = np.asarray([it.get("embedding") for it in items], dtype=np.float32)
    if vecs.ndim != 2:
        print(f"[retriever] Bad embedding shapes: {vecs.shape}")
        raise RuntimeError("Embeddings returned with wrong dimensionality")
    # normalize for cosine/IP
    vecs /= (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12)
    return vecs


def _ibm_rerank(query: str, docs: list[dict], top_n: int = 5) -> list[dict]:
    if not docs or not RERANK_MODEL_ID:
        return docs
    url = f"{BASE_URL}/ml/v1/text/rerank?version={VERSION}"
    hdr = {"Authorization": f"Bearer {_ibm_token()}",
           "Accept":"application/json","Content-Type":"application/json"}
    payload = {
        "input": {
            "query": query,
            "passages": [{"id": d["doc_id"], "text": d["snippet"]} for d in docs]
        },
        "model_id": RERANK_MODEL_ID,               # <-- required
        "project_id": PROJECT_ID,
        "top_n": min(top_n, len(docs))
    }
    r = requests.post(url, headers=hdr, json=payload, timeout=60)
    if r.status_code != 200:
        return docs
    order = r.json().get("results", [])
    id2doc = {d["doc_id"]: d for d in docs}
    out = []
    for it in order:
        d = id2doc.get(it["id"])
        if d:
            d = {**d, "score": it.get("relevance", d.get("score", d.get("score", 0.0)))}
            out.append(d)
    return out or docs


# ---------- Local embeddings fallback ----------
_embedder = None
def _local_embed(texts: list[str]) -> np.ndarray:
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    vecs = _embedder.encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype=np.float32)

def _use_ibm():
    # use IBM only if all pieces exist
    return bool(BASE_URL and PROJECT_ID and API_KEY and EMB_MODEL_ID)

def _load_snippets() -> list[dict]:
    docs = []
    with open(SNIPPETS) as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    if not docs:
        raise RuntimeError("No KB snippets found. Please populate kb/snippets.jsonl")
    return docs

def _build_or_load():
    os.makedirs(IDX_DIR, exist_ok=True)
    if os.path.exists(IDX_PATH) and os.path.exists(META_PATH):
        return faiss.read_index(IDX_PATH), json.load(open(META_PATH))

    docs = _load_snippets()
    texts = [d["snippet"] for d in docs]
    try:
        embs = _ibm_embed(texts) if _use_ibm() else _local_embed(texts)
    except Exception as e:
        # Fallback to local embeddings if IBM call fails, but surface why
        print(f"[retriever] IBM embeddings failed, falling back to local: {e}")
        embs = _local_embed(texts)

    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(embs.astype("float32"))
    faiss.write_index(index, IDX_PATH)
    json.dump(docs, open(META_PATH, "w"))
    return index, docs

def _search(query_text: str, k: int = 8) -> list[dict]:
    index, meta = _build_or_load()
    try:
        q = _ibm_embed([query_text]) if _use_ibm() else _local_embed([query_text])
    except Exception as e:
        print(f"[retriever] IBM query embed failed, using local: {e}")
        q = _local_embed([query_text])
    D, I = index.search(q.astype("float32"), k)
    hits = []
    for rank, idx in enumerate(I[0].tolist()):
        d = meta[idx]
        hits.append({
            "doc_id": d["doc_id"], "source": d.get("source","KB"),
            "snippet": d["snippet"], "score": float(D[0][rank]),
            "metadata": d.get("metadata", {})
        })
    try:
        hits = _ibm_rerank(query_text, hits, top_n=5) if _use_ibm() else hits
    except Exception as e:
        print(f"[retriever] IBM rerank failed, using original hits: {e}")
    return hits

def retrieve_evidence_for_claims(claims: List[Claim], k: int = 8) -> Tuple[List[Claim], Dict[str, List[Evidence]]]:
    claim_to_evidence: Dict[str, List[Evidence]] = {}
    for cl in claims:
        hits = _search(cl.text, k=k)
        ev_list = [
            Evidence(
                doc_id=h["doc_id"], source=h["source"], snippet=h["snippet"],
                score=h["score"], metadata=h["metadata"]
            )
            for h in hits[:5]
        ]
        claim_to_evidence[cl.id] = ev_list
    return claims, claim_to_evidence

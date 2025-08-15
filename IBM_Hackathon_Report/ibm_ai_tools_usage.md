# IBM watsonx Usage Report

## Overview
ClaimCheck AI leverages IBM watsonx as the backbone for claim verification.  
The system uses IBM watsonx.ai’s large language models and embedding capabilities to handle:
1. **Text Retrieval (RAG)**
2. **Claim Verification**
3. **Evidence Reranking**
4. *(Optionally)* IBM Speech-to-Text for transcription.

---

## Agents & IBM Integration

### 1. **Transcriber Agent**
- **Goal**: Convert audio from Zoom/phone calls to text.
- **IBM Usage**: Can integrate IBM Speech-to-Text (STT) to provide enterprise-grade transcription accuracy.
- **Inputs**: WAV/MP3/OGG audio file.
- **Outputs**: JSON array of `{ speaker, start, end, text }`.

---

### 2. **Claim Extractor Agent**
- **Goal**: Identify factual statements in the transcript.
- **IBM Usage**: Powered by IBM watsonx.ai LLM (Prompt Lab) to output JSON with `{ claim_text, speaker, start, end }`.

---

### 3. **Retriever Agent**
- **Goal**: Retrieve relevant knowledge base snippets to support or refute claims.
- **IBM Usage**:
  - **IBM Text Embeddings**: Generates semantic vector representations of KB snippets and claims.
  - **FAISS Vector Search**: Finds top-K relevant evidence from local index.
  - **IBM Rerank API**: Orders results by relevance.
- **Benefit**: Reduces false positives in evidence retrieval.

---

### 4. **Verifier Agent**
- **Goal**: Cross-check each claim against retrieved evidence.
- **IBM Usage**: LLM prompt to classify as "Supported", "Contradicted", or "Unverifiable".
- **Output**: Verdicts with reasoning.

---

### 5. **Summarizer Agent**
- **Goal**: Produce final human-readable report.
- **IBM Usage**: LLM summarization model to combine claims, evidence, and verdicts into structured output.

---

## Deployment & Scalability
While deployment is not in the scope of this hackathon, in a production setting:
- **IBM watsonx.ai models** can run in a secure IBM Cloud environment.
- **IBM Orchestrate** could be used to automate claim verification workflows (triggered after each meeting).
- **IBM Code Assistant** could accelerate code integration for enterprise clients.
- **Scalable Vector Store**: IBM Cloud Object Storage could hold large KB datasets for retrieval.

---

## Required Capabilities & Datasets
- **KB Sources**: SLA documents, compliance policies, contractual clauses, product documentation.
- **Integrations**: Zoom/Teams API for call recordings.
- **Agents**: 5 specialized agents as described.
- **IBM Services**:
  - Text Embeddings API
  - Text Rerank API
  - LLM Prompting via Prompt Lab
  - (Optional) Speech-to-Text

---

## Why IBM watsonx is Critical
- **Enterprise readiness** — Secure, compliant AI processing.
- **High accuracy retrieval** — Embeddings + Rerank reduce noise.
- **Custom KB adaptability** — Works across industries.
- **Unified ecosystem** — AI models, APIs, and orchestration tools in one platform.

By combining these capabilities, ClaimCheck AI transforms unstructured meeting dialogue into **evidence-backed, compliance-ready reports** in near real-time.

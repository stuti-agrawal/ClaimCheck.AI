# app/core/config.py
import os
from dotenv import load_dotenv
load_dotenv()

WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "")
WATSONX_BASE_URL = os.getenv("WATSONX_BASE_URL", "")
WATSONX_PROJECT  = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_API_KEY  = os.getenv("WATSONX_API_KEY", "")
IBM_API_VERSION = os.getenv("IBM_API_VERSION", "")
IBM_EMBEDDINGS_MODEL_ID = os.getenv("IBM_EMBEDDINGS_MODEL_ID", "")
IBM_RERANK_MODEL_ID = os.getenv("IBM_RERANK_MODEL_ID", "")
IBM_CLAIM_MODEL_ID = os.getenv("IBM_CLAIM_MODEL_ID", "")
IBM_VERIFIER_MODEL_ID = os.getenv("IBM_VERIFIER_MODEL_ID", "")
IBM_SUMMARY_MODEL_ID = os.getenv("IBM_SUMMARY_MODEL_ID", "")
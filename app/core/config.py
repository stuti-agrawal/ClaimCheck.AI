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

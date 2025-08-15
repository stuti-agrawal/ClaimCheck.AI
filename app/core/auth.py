import time
import requests
from app.core.config import WATSONX_API_KEY


_iam_cache = {"token": None, "expiry": 0.0}


def get_ibm_iam_token() -> str:
    now = time.time()
    token = _iam_cache.get("token")
    expiry = _iam_cache.get("expiry", 0.0)
    if token and now < (expiry - 60):
        return token

    response = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": WATSONX_API_KEY,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    _iam_cache["token"] = token
    _iam_cache["expiry"] = now + 3000  # ~50 minutes
    return token 
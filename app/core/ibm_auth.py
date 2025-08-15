# app/core/ibm_auth.py
import requests, time, os
from app.core.config import WATSONX_API_KEY

_iam = {"tok": None, "exp": 0}

def ibm_iam_token():
    now = time.time()
    if _iam["tok"] and now < _iam["exp"] - 60:
        return _iam["tok"]
    r = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type":"urn:ibm:params:oauth:grant-type:apikey","apikey":WATSONX_API_KEY},
        headers={"Content-Type":"application/x-www-form-urlencoded"}
    )
    r.raise_for_status()
    tok = r.json()["access_token"]
    _iam["tok"] = tok
    _iam["exp"] = now + 3000  # ~50 min
    return tok

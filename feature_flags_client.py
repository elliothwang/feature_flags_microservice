# feature_flags_client.py
import os
import requests

FEATURE_FLAG_BASE_URL = os.environ.get("FEATURE_FLAG_URL", "http://localhost:5005")
ALLOWED_MODES = {"test", "production"}


def get_current_mode() -> str:
    """
    returns the current mode reported by the feature flag microservice
    falls back to test if the service is unavailable
    """
    try:
        resp = requests.get(f"{FEATURE_FLAG_BASE_URL}/mode", timeout=1.0)
        if not resp.ok:
            return "test"
        data = resp.json()
        mode = str(data.get("mode", "")).lower()
        if mode in ALLOWED_MODES:
            return mode
    except Exception:
        pass
    return "test"

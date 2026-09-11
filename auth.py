# auth.py
import hmac
import hashlib
import time
import json
import base64
import streamlit as st

SECRET = st.secrets["AUTH_SECRET"]

DUREES = {
    "JOUR": 1,
    "MOIS": 30,
    "BAC": 90,
}


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def creer_token(formule: str) -> str:
    if formule not in DUREES:
        raise ValueError("Formule inconnue")
    expiration = int(time.time()) + DUREES[formule] * 86400
    payload = {"f": formule, "exp": expiration}
    payload_json = json.dumps(payload, separators=(",", ":")).encode()
    payload_b64 = _b64encode(payload_json)
    signature = hmac.new(
        SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def verifier_token(token: str):
    if not token or "." not in token:
        return None
    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError:
        return None

    expected_sig = hmac.new(
        SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        return None

    try:
        payload = json.loads(_b64decode(payload_b64))
    except Exception:
        return None

    if payload.get("exp", 0) < time.time():
        return None

    return payload
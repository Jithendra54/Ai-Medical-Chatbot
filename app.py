"""CareGuide — AI Medical Chatbot prototype.

A Flask app that keeps conversation state in the browser and uses a local Ollama model by default. Optional xAI mode is available only when explicitly selected.
"""

from __future__ import annotations

import os
import re
import threading
import time
from collections import defaultdict, deque
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

XAI_API_URL = "https://api.x.ai/v1/chat/completions"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()
_DEFAULT_OLLAMA_URL = "https://ollama.com/api/chat" if OLLAMA_API_KEY else "http://127.0.0.1:11434/api/chat"
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "").strip() or _DEFAULT_OLLAMA_URL
DEFAULT_MODEL = os.getenv("XAI_MODEL", "grok-4.6")
_DEFAULT_OLLAMA_MODEL = "gemma4:31b" if OLLAMA_API_KEY else "qwen2.5:3b"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "").strip() or _DEFAULT_OLLAMA_MODEL
MAX_MESSAGE_CHARS = 2_000
MAX_HISTORY_MESSAGES = 12
MAX_HISTORY_CHARS = 10_000
API_TIMEOUT_SECONDS = 45

SYSTEM_PROMPT = """You are CareGuide, a careful health-information assistant in a student project.
Your role is health education and navigation, not clinical diagnosis or treatment.

SAFETY RULES:
- Never claim to diagnose, rule out, or confirm a disease. Explain uncertainty plainly.
- If the user describes possible emergency symptoms (such as chest pain, difficulty breathing, stroke signs, unconsciousness, severe bleeding, seizure, severe allergic reaction, poisoning/overdose, or immediate risk of self-harm), advise urgent in-person help now. In India they can call 112; elsewhere use their local emergency number. Do not delay this advice with a long explanation.
- Give general, low-risk self-care information only when appropriate. Do not prescribe medicines, provide individualized dosing, recommend antibiotics, or tell people to stop prescribed medicines. Suggest a doctor or pharmacist for medication decisions.
- For symptoms, ask only relevant follow-up questions and explain when to seek care. Be especially cautious with infants, pregnancy, older adults, and serious chronic illness.
- Never invent sources, certainty, examination findings, or medical credentials.
- Be calm, plain-spoken, concise, and non-judgmental. Use brief headings or bullets when helpful. Explain medical terms in everyday language.
- Do not request names, exact addresses, government IDs, or other identifying information. Remind users not to share them.
- Make clear that this is informational and cannot replace a qualified healthcare professional.
"""

EMERGENCY_PATTERNS = [
    r"\b(chest pain|pressure in (my )?chest)\b",
    r"\b(can't|cannot|unable to|difficulty) (breathe|breathing)\b",
    r"\b(shortness of breath|severe breathing trouble)\b",
    r"\b(face droop|slurred speech|sudden weakness|stroke symptoms?)\b",
    r"\b(unconscious|not waking up|passed out)\b",
    r"\b(severe bleeding|bleeding won't stop)\b",
    r"\b(anaphylaxis|throat closing|severe allergic reaction)\b",
    r"\b(overdose|poisoned|swallowed poison)\b",
    r"\b(active seizure|seizing right now)\b",
]


def current_mode() -> str:
    provider = os.getenv("AI_PROVIDER", "ollama").strip().lower()
    if provider == "demo":
        return "demo"
    if provider == "xai":
        return "grok" if os.getenv("XAI_API_KEY", "").strip() else "demo"
    return "ollama"


def is_possible_emergency(message: str) -> bool:
    text = message.lower()
    return any(re.search(pattern, text) for pattern in EMERGENCY_PATTERNS)


def emergency_reply() -> str:
    return (
        "**Please seek urgent medical help now.** Do not wait for an AI response. "
        "If you are in India, call **112**; otherwise call your local emergency number. "
        "Ask someone nearby to help, and do not drive yourself if you may be seriously unwell. "
        "This automated warning is limited and is not a medical assessment."
    )


def demo_reply(message: str) -> str:
    text = message.lower()
    if any(word in text for word in ("cold", "runny nose", "sore throat", "cough")):
        return (
            "**Demo example — not AI-generated medical advice.** For mild cold-like symptoms, "
            "rest, drink fluids, and consider warm drinks or saline nasal spray. Seek medical "
            "advice if symptoms worsen, persist, or you are concerned. Trouble breathing, "
            "chest pain, confusion, or severe weakness needs urgent care."
        )
    if any(word in text for word in ("sleep", "insomnia", "sleeping")):
        return (
            "**Demo example — not AI-generated medical advice.** A regular sleep and wake time, "
            "a quiet dark bedroom, and limiting late caffeine may help sleep habits. Persistent "
            "sleep difficulties are worth discussing with a healthcare professional."
        )
    if any(word in text for word in ("doctor", "appointment", "visit")):
        return (
            "**Demo example — not AI-generated medical advice.** Before a medical visit, note "
            "when the symptom began, how it has changed, relevant medicines and allergies, "
            "and the questions you want to ask. Avoid including identifying details here."
        )
    return (
        "**Demo mode is active.** This is a pre-written example, not a live AI response and "
        "not a clinically validated answer. Add your xAI API key on the server to enable Grok. "
        "For a personal health concern, consult a qualified healthcare professional."
    )


def normalise_history(raw_messages: Any) -> list[dict[str, str]]:
    if not isinstance(raw_messages, list):
        raise ValueError("messages must be a list")
    cleaned: list[dict[str, str]] = []
    total_chars = 0
    for item in raw_messages[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict) or item.get("role") not in ("user", "assistant"):
            continue
        content = item.get("content")
        if not isinstance(content, str):
            continue
        content = content.strip()
        if not content:
            continue
        if len(content) > MAX_MESSAGE_CHARS:
            raise ValueError(f"Each message must be no longer than {MAX_MESSAGE_CHARS} characters")
        total_chars += len(content)
        cleaned.append({"role": item["role"], "content": content})
    if not cleaned or cleaned[-1]["role"] != "user":
        raise ValueError("The final message must be a user message")
    if total_chars > MAX_HISTORY_CHARS:
        raise ValueError("Conversation is too long; please start a new chat")
    return cleaned


def call_ollama(messages: list[dict[str, str]]) -> str:
    """Call a model running locally through Ollama."""
    payload = {
        "model": os.getenv("OLLAMA_MODEL", OLLAMA_MODEL),
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        "stream": False,
        "options": {"temperature": 0.2},
    }
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
    response = requests.post(OLLAMA_API_URL, headers=headers, json=payload, timeout=API_TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    reply = data["message"]["content"]
    if not isinstance(reply, str) or not reply.strip():
        raise ValueError("The Ollama model returned an empty response")
    return reply.strip()


def call_grok(messages: list[dict[str, str]]) -> str:
    api_key = os.getenv("XAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("XAI_API_KEY is not configured")
    payload = {
        "model": os.getenv("XAI_MODEL", DEFAULT_MODEL),
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        "temperature": 0.2,
    }
    response = requests.post(
        XAI_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    if not isinstance(reply, str) or not reply.strip():
        raise ValueError("The AI service returned an empty response")
    return reply.strip()


_request_times: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = threading.Lock()


def request_is_rate_limited() -> bool:
    limit = max(1, int(os.getenv("RATE_LIMIT_PER_MINUTE", "20")))
    now = time.time()
    address = request.headers.get("X-Real-IP") or request.remote_addr or "unknown"
    with _rate_lock:
        items = _request_times[address]
        while items and now - items[0] > 60:
            items.popleft()
        if len(items) >= limit:
            return True
        items.append(now)
    return False


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; font-src 'self' data:; object-src 'none'; base-uri 'self'; "
        "frame-ancestors 'none'; form-action 'self'"
    )
    return response


@app.get("/")
def index():
    return render_template("index.html", mode=current_mode())


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "mode": current_mode()})


@app.post("/api/chat")
def chat():
    if request_is_rate_limited():
        return jsonify({"error": "Too many requests. Please wait a moment and try again."}), 429
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Please send a valid JSON request."}), 400
    try:
        messages = normalise_history(body.get("messages"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    latest = messages[-1]["content"]
    if is_possible_emergency(latest):
        return jsonify({"reply": emergency_reply(), "mode": current_mode(), "emergency": True})

    mode = current_mode()
    if mode == "demo":
        return jsonify({"reply": demo_reply(latest), "mode": "demo", "emergency": False})
    try:
        reply = call_grok(messages) if mode == "grok" else call_ollama(messages)
        return jsonify({"reply": reply, "mode": mode, "emergency": False})
    except requests.Timeout:
        return jsonify({"error": "The AI model took too long to respond. Try again or use a smaller model."}), 504
    except requests.ConnectionError:
        if mode == "ollama" and not OLLAMA_API_KEY:
            return jsonify({"error": "Cannot reach local Ollama. Install it, start it, and run ollama run qwen2.5:3b, then retry."}), 503
        app.logger.warning("xAI API connection failed", exc_info=True)
        return jsonify({"error": "The AI service is unavailable right now. Please try again later."}), 502
    except requests.RequestException:
        app.logger.warning("AI provider request failed", exc_info=True)
        return jsonify({"error": "The AI service is unavailable right now. Please try again later."}), 502
    except (KeyError, IndexError, TypeError, ValueError):
        app.logger.warning("Unexpected response from AI provider", exc_info=True)
        return jsonify({"error": "The AI service returned an unexpected response. Please try again."}), 502


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "Request is too large. Please shorten your message."}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)

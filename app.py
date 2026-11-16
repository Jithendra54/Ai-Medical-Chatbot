import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
API_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")

st.set_page_config(page_title="CareGuide", page_icon="✚", layout="wide")
st.markdown("""
<style>
:root { --ink:#173343; --muted:#687985; --green:#137e6a; }
.stApp { background: radial-gradient(ellipse at 75% 2%, #e7f4f1 0, transparent 35%), #f6f8fc; color:var(--ink); }
.block-container { max-width: 1050px; padding-top: 2rem; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid #e8edf1; }
[data-testid="stChatMessage"] { background:#fff; border:1px solid #e7ecee; border-radius:14px; }
.stButton button { border-radius:11px; }
</style>
""", unsafe_allow_html=True)

SOURCES = [
    {
        "title": "MedlinePlus: Common Cold",
        "url": "https://medlineplus.gov/commoncold.html",
        "keywords": {"cold", "cough", "sore", "throat", "runny", "nose", "congestion", "sneeze", "fever", "fluids", "rest"},
        "passage": "Common colds are usually mild and often improve in 7 to 10 days, though some symptoms can last 10 to 14 days. Rest, drink fluids, use saline nose drops or spray, and consider a clean humidifier. Antibiotics do not treat viral colds. Seek medical advice for trouble breathing, dehydration, fever lasting more than 4 days, symptoms lasting more than 10 days without improvement, or symptoms that improve and then worsen."
    },
    {
        "title": "MedlinePlus: Healthy Sleep",
        "url": "https://medlineplus.gov/healthysleep.html",
        "keywords": {"sleep", "insomnia", "tired", "bedtime", "wake", "caffeine", "routine"},
        "passage": "Helpful sleep habits include keeping a regular bedtime and wake time, avoiding caffeine later in the day, exercising regularly but not close to bedtime, keeping the bedroom cool, dark, and quiet, and allowing enough time for sleep. Adults generally need 7 to 9 hours, though needs vary. Speak with a health professional if sleep trouble continues."
    },
    {
        "title": "NHS: What to ask your doctor",
        "url": "https://www.nhs.uk/nhs-services/gps/what-to-ask-your-doctor/",
        "keywords": {"doctor", "appointment", "visit", "symptom", "symptoms", "questions", "clinician", "medicine", "medicines"},
        "passage": "Before an appointment, write down your main questions and describe symptoms, when they started, and what makes them better or worse. Bring a list of medicines and supplements. Ask what tests are for, how and when results arrive, what the next steps are, and who to contact if symptoms worsen. Ask the clinician to explain anything unclear."
    },
]

EMERGENCY_PATTERNS = [
    r"\b(chest pain|pressure in (my )?chest)\b",
    r"\b(can't breathe|cannot breathe|difficulty breathing|shortness of breath)\b",
    r"\b(face droop|slurred speech|sudden weakness|stroke symptoms?)\b",
    r"\b(unconscious|not waking up|severe bleeding|throat closing|overdose|active seizure)\b",
    r"\b(kill myself|suicidal intent|going to harm myself)\b",
]
EMERGENCY_REPLY = (
    "Please seek urgent medical help now. Do not wait for an AI response. "
    "If you are in India, call 112; otherwise call your local emergency number. "
    "Ask someone nearby to help. This automated warning is limited and is not a medical assessment."
)
SYSTEM_PROMPT = """You are CareGuide, a cautious health-information assistant for general education, not a doctor.
Answer only from the provided source passages and say when they do not cover the question.
Never diagnose, rule out, or confirm disease; never prescribe medicines or individualized doses.
For potentially life-threatening symptoms, recommend urgent in-person help immediately. India: call 112.
Use plain language, explain uncertainty, and encourage professional care for severe, persistent, or worsening symptoms.
Do not request identifying information. This can make mistakes and is not a substitute for professional care."""

def retrieve_sources(question):
    words = set(re.findall(r"[a-z]+", question.lower()))
    scored = []
    for source in SOURCES:
        score = len(words & source["keywords"])
        if score:
            scored.append((score, source))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [source for score, source in scored[:2] if score > 0]

def answer_question(question, history):
    if any(re.search(pattern, question, re.I) for pattern in EMERGENCY_PATTERNS):
        return EMERGENCY_REPLY, []

    sources = retrieve_sources(question)
    if not sources:
        return (
            "I couldn't find a relevant passage in CareGuide's small source library for that question. "
            "Please check with a qualified healthcare professional or consult a trusted health source. "
            "This chatbot covers only a few general topics and cannot assess personal symptoms.",
            [],
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        answer = "\n\n".join(source["passage"] for source in sources)
        return answer + "\n\nGeneral information only; this is not a diagnosis.", sources

    context = "\n\n".join(
        source["title"] + " (" + source["url"] + "): " + source["passage"]
        for source in sources
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nSource passages:\n" + context}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": question})
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 500,
    }).encode("utf-8")
    request = Request(
        API_URL,
        data=payload,
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read(1_000_000))
        return result["choices"][0]["message"]["content"], sources
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError):
        return "I couldn't reach the optional AI provider. Please try again later.", sources

st.title("✚ CareGuide")
st.caption("Health information, made clearer")
with st.sidebar:
    st.subheader("Explore health topics")
    st.markdown("**Common symptoms**\n\nEveryday health information")
    st.markdown("**Sleep & wellbeing**\n\nBuild healthy routines")
    st.markdown("**Prepare for a doctor visit**\n\nOrganise your questions")
    st.divider()
    st.error("**Need urgent help?** Do not wait for an AI response if someone may be in danger. In India call **112**; elsewhere call your local emergency number.")
    st.caption("Avoid sharing names or identifying details.")

st.info("For education only. CareGuide cannot diagnose or replace professional medical care. It has a small source library and can make mistakes.")
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("### How can I help you feel informed?")
    st.write("Ask about common cold self-care, sleep habits, or preparing for a doctor visit.")
    prompts = [
        "What can help with mild cold symptoms at home?",
        "What are practical habits for improving sleep quality?",
        "Help me prepare questions to ask a doctor about a new symptom.",
    ]
    cols = st.columns(3)
    for col, prompt in zip(cols, prompts):
        if col.button(prompt, use_container_width=True):
            st.session_state.pending_prompt = prompt
            st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            st.markdown("**Sources**")
            for source in message["sources"]:
                st.markdown(f"- [{source['title']}]({source['url']})")

prompt = st.session_state.pop("pending_prompt", None)
entered = st.chat_input("Ask a health information question…")
question = prompt or entered
if question:
    clean_question = question.strip()[:2000]
    st.session_state.messages.append({"role": "user", "content": clean_question})
    chat_history = [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.messages[:-1]
        if item["role"] in ("user", "assistant")
    ]
    with st.chat_message("user"):
        st.markdown(clean_question)
    with st.chat_message("assistant"):
        with st.spinner("Checking the source library…"):
            reply, used_sources = answer_question(clean_question, chat_history)
        st.markdown(reply)
        if used_sources:
            st.markdown("**Sources**")
            for source in used_sources:
                st.markdown(f"- [{source['title']}]({source['url']})")
    assistant_message = {"role": "assistant", "content": reply}
    if used_sources:
        assistant_message["sources"] = used_sources
    st.session_state.messages.append(assistant_message)

st.caption("Informational use only. Verify important health information with a qualified healthcare professional.")

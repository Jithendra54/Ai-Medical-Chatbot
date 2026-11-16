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

# Short paraphrased notes indexed from linked public-health references.
# This is retrieval over a small curated library, not model training or diagnosis.
SOURCES = [
    {
        "title": "Everyday health habits (CDC)",
        "url": "https://www.cdc.gov/howrightnow/taking-care/index.html",
        "keywords": {"health", "healthy", "improve", "improving", "tips", "tip", "wellness", "wellbeing", "lifestyle", "habits", "habit", "better", "general", "everyday", "prevent", "prevention", "live", "living", "routine"},
        "passage": "A practical starting point is to build a few sustainable habits: eat a variety of vegetables, fruits, whole grains, and protein; move more and sit less, starting with an amount that fits your current ability; keep a regular sleep schedule; stay connected and use relaxing activities to manage stress; avoid tobacco; and keep up with health appointments, recommended vaccines, and screenings. You do not need to change everything at once. If you have a health condition, disability, are pregnant, or are unsure what is safe for you, ask a clinician for personalized guidance.",
        "citations": [
            ("CDC: Taking Care of Your Body", "https://www.cdc.gov/howrightnow/taking-care/index.html"),
            ("WHO: Healthy diet", "https://www.who.int/news-room/fact-sheets/detail/healthy-diet"),
            ("WHO: Physical activity", "https://www.who.int/news-room/fact-sheets/detail/physical-activity/"),
            ("CDC: About Sleep", "https://www.cdc.gov/sleep/about/"),
            ("CDC: Preventive care", "https://www.cdc.gov/chronic-disease/prevention/preventive-care.html"),
        ],
    },
    {
        "title": "Healthy eating (WHO)",
        "url": "https://www.who.int/news-room/fact-sheets/detail/healthy-diet",
        "keywords": {"diet", "food", "eat", "eating", "nutrition", "meal", "meals", "vegetable", "vegetables", "fruit", "fruits", "fiber", "fibre", "wholegrain", "grains", "beans", "pulses", "sugar", "salt", "sodium"},
        "passage": "A healthy eating pattern varies with a person's needs and culture. WHO describes diversity, balance, moderation, and adequacy as useful principles. Choose a variety of minimally processed foods, including vegetables, fruits, pulses such as beans and lentils, and whole grains. Limit foods and drinks high in salt or sodium, free sugars, and unhealthy fats. People with medical conditions or special nutrition needs should ask a qualified clinician or dietitian for individual advice.",
        "citations": [("WHO: Healthy diet", "https://www.who.int/news-room/fact-sheets/detail/healthy-diet")],
    },
    {
        "title": "Physical activity (WHO)",
        "url": "https://www.who.int/news-room/fact-sheets/detail/physical-activity/",
        "keywords": {"exercise", "activity", "active", "walking", "walk", "movement", "fitness", "sedentary", "sitting", "workout", "strength", "strengthening", "sport"},
        "passage": "Some physical activity is better than none. WHO recommends that adults aim for 150–300 minutes of moderate-intensity aerobic activity each week, or an equivalent combination of moderate and vigorous activity, plus muscle-strengthening activity on 2 or more days per week. People who are currently inactive can start with small amounts and gradually build up. Recommendations differ by age and circumstances; ask a clinician what is appropriate if you have a condition, disability, are pregnant, or have concerns.",
        "citations": [("WHO: Physical activity", "https://www.who.int/news-room/fact-sheets/detail/physical-activity/")],
    },
    {
        "title": "Healthy sleep (CDC)",
        "url": "https://www.cdc.gov/sleep/about/",
        "keywords": {"sleep", "insomnia", "tired", "bedtime", "wake", "caffeine", "rest", "sleepless", "sleeping", "night"},
        "passage": "Sleep needs vary with age. CDC recommends at least 7 hours for most adults aged 18–60, with different recommendations for other age groups. A regular sleep and wake time can help. Talk with a healthcare provider if you have ongoing sleep problems.",
        "citations": [("CDC: About Sleep", "https://www.cdc.gov/sleep/about/"), ("MedlinePlus: Healthy Sleep", "https://medlineplus.gov/healthysleep.html")],
    },
    {
        "title": "Managing stress (MedlinePlus)",
        "url": "https://medlineplus.gov/stress.html",
        "keywords": {"stress", "stressed", "anxiety", "anxious", "relax", "relaxation", "breathing", "meditation", "mood", "mental", "overwhelmed", "cope"},
        "passage": "For ongoing stress, MedlinePlus suggests practical steps such as regular exercise, relaxing activities, enough sleep, limiting excess caffeine, prioritizing what needs attention now, and seeking support from family or friends. Get help from a healthcare professional when stress or mood symptoms interfere with daily life or persist. Seek immediate help if you may harm yourself or cannot stay safe.",
        "citations": [("MedlinePlus: Stress", "https://medlineplus.gov/stress.html")],
    },
    {
        "title": "Water and hydration (MedlinePlus)",
        "url": "https://medlineplus.gov/ency/article/002471.htm",
        "keywords": {"water", "hydration", "hydrate", "thirsty", "dehydration", "drink", "drinking", "fluids"},
        "passage": "Fluid needs vary with age, activity, climate, and health conditions, and fluids also come from foods and other beverages. MedlinePlus notes there is no single daily water amount that applies to everyone. Drinking when thirsty and having beverages with meals is a practical guide for many people; choose water over sugary drinks when possible. Ask a healthcare provider for advice if you have a condition that affects fluid needs.",
        "citations": [("MedlinePlus: Water in diet", "https://medlineplus.gov/ency/article/002471.htm")],
    },
    {
        "title": "Handwashing (CDC)",
        "url": "https://www.cdc.gov/Clean-Hands/About/",
        "keywords": {"hand", "hands", "wash", "washing", "hygiene", "germs", "infection", "infections", "soap", "sanitizer", "clean"},
        "passage": "Wash hands with soap and clean running water, especially before preparing or eating food, after using the toilet, after coughing, sneezing, or blowing your nose, and when caring for someone who is ill. Scrub all surfaces for at least 20 seconds. If soap and water are unavailable, CDC recommends hand sanitizer containing at least 60% alcohol.",
        "citations": [("CDC: About Handwashing", "https://www.cdc.gov/Clean-Hands/About/")],
    },
    {
        "title": "Preventive care (CDC)",
        "url": "https://www.cdc.gov/chronic-disease/prevention/preventive-care.html",
        "keywords": {"checkup", "checkups", "screening", "screenings", "vaccine", "vaccines", "vaccination", "preventive", "prevention", "appointment", "routine", "doctor", "dentist", "healthcare"},
        "passage": "Routine preventive care can help people stay well and identify some problems earlier. Check with a healthcare professional about which checkups, screening tests, and vaccines are appropriate for your age, health history, location, and circumstances. Recommendations are individual and can change over time.",
        "citations": [("CDC: Are You Up to Date on Your Preventive Care?", "https://www.cdc.gov/chronic-disease/prevention/preventive-care.html")],
    },
    {
        "title": "Quitting tobacco (WHO)",
        "url": "https://www.who.int/en/news-room/fact-sheets/detail/tobacco",
        "keywords": {"smoking", "smoke", "tobacco", "vaping", "nicotine", "quit", "quitting", "cigarette", "cigarettes"},
        "passage": "Stopping tobacco use has health benefits at any age. WHO reports that counselling and medication can more than double a tobacco user's chance of successfully quitting. A healthcare professional or local quit service can help find support that fits the person.",
        "citations": [("WHO: Tobacco and nicotine", "https://www.who.int/en/news-room/fact-sheets/detail/tobacco")],
    },
    {
        "title": "Common cold (MedlinePlus)",
        "url": "https://medlineplus.gov/commoncold.html",
        "keywords": {"cold", "cough", "sore", "throat", "runny", "nose", "congestion", "sneeze", "fever", "antibiotics"},
        "passage": "Common colds are usually mild and often improve in 7 to 10 days, though some symptoms can last 10 to 14 days. Rest, drink fluids, use saline nose drops or spray, and consider a clean humidifier. Antibiotics do not treat viral colds. Seek medical advice for trouble breathing, dehydration, fever lasting more than 4 days, symptoms lasting more than 10 days without improvement, or symptoms that improve and then worsen.",
        "citations": [("MedlinePlus: Common Cold", "https://medlineplus.gov/commoncold.html")],
    },
    {
        "title": "Preparing for a doctor visit (NHS)",
        "url": "https://www.nhs.uk/nhs-services/gps/what-to-ask-your-doctor/",
        "keywords": {"doctor", "appointment", "visit", "symptom", "symptoms", "questions", "clinician", "medicine", "medicines", "test", "tests"},
        "passage": "Before an appointment, write down your main questions and describe symptoms, when they started, and what makes them better or worse. Bring a list of medicines and supplements. Ask what tests are for, how and when results arrive, what the next steps are, and who to contact if symptoms worsen. Ask the clinician to explain anything unclear.",
        "citations": [("NHS: What to ask your doctor", "https://www.nhs.uk/nhs-services/gps/what-to-ask-your-doctor/")],
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

STOP_WORDS = {
    "a", "an", "and", "are", "about", "am", "any", "can", "could", "do", "does", "for",
    "from", "give", "help", "how", "i", "im", "is", "it", "me", "my", "of", "on", "please",
    "should", "some", "the", "to", "what", "when", "with", "would", "you", "your",
}

def normalize_words(text):
    words = set(re.findall(r"[a-z]+", text.lower()))
    return {word for word in words if word not in STOP_WORDS and len(word) > 2}

def retrieve_sources(question):
    query_words = normalize_words(question)
    if not query_words:
        return []

    broad_health = bool(query_words & {
        "health", "healthy", "improve", "improving", "tips", "tip", "wellness",
        "wellbeing", "lifestyle", "habits", "habit", "better", "general", "everyday",
    })
    scored = []
    for source in SOURCES:
        score = len(query_words & source["keywords"])
        if score:
            scored.append((score, source))
    scored.sort(key=lambda item: item[0], reverse=True)

    # Broad questions get a practical overview, while specific topic words still
    # bring their matching source to the top.
    if broad_health and (not scored or scored[0][0] <= 1):
        overview = SOURCES[0]
        related = [source for _, source in scored if source is not overview]
        return [overview] + related[:3]
    return [source for score, source in scored[:4] if score > 0]

def answer_question(question, history):
    if any(re.search(pattern, question, re.I) for pattern in EMERGENCY_PATTERNS):
        return EMERGENCY_REPLY, []

    sources = retrieve_sources(question)
    if not sources:
        return (
            "I couldn't find a relevant section in CareGuide's health library for that question. "
            "Try asking about everyday health habits, food, exercise, sleep, stress, hydration, handwashing, "
            "preventive care, common colds, or preparing for a doctor visit. "
            "For personal medical advice, contact a qualified healthcare professional.",
            [],
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        answer = "\n\n".join(
            "**" + source["title"] + "**\n" + source["passage"]
            for source in sources
        )
        return answer + "\n\nThis is general information, not a diagnosis.", sources

    context_parts = []
    for source in sources:
        citation_text = "; ".join(title + " (" + url + ")" for title, url in source["citations"])
        context_parts.append(source["title"] + " — " + citation_text + "\n" + source["passage"])
    context = "\n\n".join(context_parts)
    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nRetrieved source notes:\n" + context}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": question})
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 650,
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
        reply = result["choices"][0]["message"]["content"]
        return reply, sources
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError):
        answer = "\n\n".join(
            "**" + source["title"] + "**\n" + source["passage"]
            for source in sources
        )
        return answer + "\n\nThe optional AI service was unavailable, so these source notes are shown directly.", sources

st.title("✚ CareGuide")
st.caption("Health information, made clearer")
with st.sidebar:
    st.subheader("Explore health topics")
    st.caption("Choose a topic to start:")
    topic_prompts = [
        "Give me simple tips to improve my overall health",
        "What are some healthy foods to eat?",
        "How can I become more physically active?",
        "How can I sleep better?",
        "What can I do to manage stress?",
        "How should I prepare for a doctor visit?",
    ]
    for topic_prompt in topic_prompts:
        if st.button(topic_prompt, use_container_width=True):
            st.session_state.pending_prompt = topic_prompt
            st.rerun()
    st.divider()
    st.error("**Need urgent help?** Do not wait for an AI response if someone may be in danger. In India call **112**; elsewhere call your local emergency number.")
    st.caption("Avoid sharing names or identifying details.")

st.info("For education only. CareGuide cannot diagnose or replace professional medical care. Answers are based on a small library of linked public-health sources and can be incomplete.")
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("### How can I help you feel informed?")
    st.write("Ask about everyday health habits, nutrition, activity, sleep, stress, hydration, hygiene, preventive care, or common symptoms.")
    prompts = [
        "Give me simple tips to improve my overall health",
        "What are practical habits for improving sleep quality?",
        "What can help with mild cold symptoms at home?",
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
            citations = []
            for source in message["sources"]:
                citations.extend(source["citations"])
            seen = set()
            for title, url in citations:
                if url not in seen:
                    seen.add(url)
                    st.markdown(f"- [{title}]({url})")

pending = st.session_state.pop("pending_prompt", None)
entered = st.chat_input("Ask a general health question…")
question = pending or entered
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
        with st.spinner("Looking through the health library…"):
            reply, used_sources = answer_question(clean_question, chat_history)
        st.markdown(reply)
        if used_sources:
            st.markdown("**Sources**")
            citations = []
            for source in used_sources:
                citations.extend(source["citations"])
            seen = set()
            for title, url in citations:
                if url not in seen:
                    seen.add(url)
                    st.markdown(f"- [{title}]({url})")
    assistant_message = {"role": "assistant", "content": reply}
    if used_sources:
        assistant_message["sources"] = used_sources
    st.session_state.messages.append(assistant_message)

st.caption("Informational use only. Verify important health information with a qualified healthcare professional.")

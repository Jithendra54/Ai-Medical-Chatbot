# CareGuide — Python source-grounded health chatbot

CareGuide is an educational health-information chatbot served by a Python web server. The interface is generated and served by Python, and the chat API is handled in Python.

## How answers work

The app uses retrieval over a small, curated source library rather than training a model. It currently covers common colds, healthy sleep, and preparing for a doctor visit. Relevant questions receive short source-based guidance and links. Questions outside those topics receive a notice that the source library has no relevant passage.

Sources:

- [MedlinePlus: Common Cold](https://medlineplus.gov/commoncold.html)
- [MedlinePlus: Healthy Sleep](https://medlineplus.gov/healthysleep.html)
- [NHS: What to ask your doctor](https://www.nhs.uk/nhs-services/gps/what-to-ask-your-doctor/)

With no AI provider key configured, the app returns the curated passage text and citations directly. If an OpenAI-compatible API key is configured, the app can use it to compose an answer from the retrieved passages, and appends the source URLs. That provider may charge for usage. The knowledge base is small and does not constitute medical training data or a comprehensive medical reference.

## Hosting

The repo includes a Render Blueprint at `render.yaml` for its free web-service plan. Connect the GitHub repo to Render and create a Blueprint instance. Free services can sleep when idle and have resource and usage limits. GitHub Pages cannot run a Python server.

AI inference is optional for the cited source lookup. To enable model-written responses, set `OPENAI_API_KEY` in the hosting service environment. Set `OPENAI_MODEL` as needed (default: `gpt-4o-mini`) and optionally `OPENAI_BASE_URL` for a compatible provider. Do not commit API keys or put them in browser code. A free hosting plan does not make model inference free.

## Local run

Requires Python 3.10 or newer. The web server uses only Python's standard library.

```powershell
python app.py
```

Open http://localhost:8000. The `/health` endpoint is used by the host. No AI key is required for source-library answers.

## Privacy and safety

CareGuide does not save chat history. The browser sends recent conversation context with each request. If configured, chat messages are sent to the selected AI provider. Avoid entering identifying or sensitive patient details.

This is an informational student project, not a medical device or substitute for a qualified healthcare professional. It can make errors and cannot reliably diagnose or detect every emergency. For potentially life-threatening symptoms, call emergency services; in India call 112. Emergency phrase matching is a limited safeguard, not clinical triage.

## Deployment migration

The former Vite/WebLLM frontend and GitHub Pages deployment workflow have been removed from this branch. A Python server cannot run on GitHub Pages. A Render account/service is still needed before the Python app is live.

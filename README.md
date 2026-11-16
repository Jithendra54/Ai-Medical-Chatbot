# CareGuide — Python health information chatbot

CareGuide is an educational health-information chatbot. Its interface, source retrieval, and optional chat-provider integration are written in Python with Streamlit.

## How answers work

The app uses retrieval over a small curated source library rather than training a model. It currently covers common colds, healthy sleep, and preparing for a doctor visit. Relevant questions receive source-based guidance and links. Questions outside those topics receive a message that the source library has no relevant passage.

Sources:

- [MedlinePlus: Common Cold](https://medlineplus.gov/commoncold.html)
- [MedlinePlus: Healthy Sleep](https://medlineplus.gov/healthysleep.html)
- [NHS: What to ask your doctor](https://www.nhs.uk/nhs-services/gps/what-to-ask-your-doctor/)

Without an AI provider key, the app returns curated source passages and citations directly. An optional OpenAI-compatible API key can enable model-written answers based on the retrieved passages. That provider may charge for usage. The library is small and is not medical training data or a comprehensive reference.

## Deploy on Render

The repository includes a Render Blueprint at `render.yaml`. Connect the GitHub repository to Render and create a Blueprint instance. Select the `main` branch and the free web-service plan. Free services have usage limits and can sleep when idle; GitHub Pages cannot run this Python app.

To enable optional model-written responses, add `OPENAI_API_KEY` in the Render service's environment settings. Do not commit keys to GitHub or put them in browser code. The source-library responses work without this key.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. No AI key is needed for curated source answers.

## Privacy and safety

CareGuide does not save chat history between sessions. If configured, chat messages and recent context are sent to the selected AI provider. Avoid entering identifying or sensitive patient information.

This is an informational student project, not a medical device or substitute for a qualified healthcare professional. It can make errors and cannot reliably diagnose or detect every emergency. For potentially life-threatening symptoms, call emergency services; in India call 112. Emergency phrase matching is a limited safeguard, not clinical triage.

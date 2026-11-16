# CareGuide — Python health information chatbot

CareGuide is an educational health-information chatbot. Its interface and retrieval logic are written in Python with Streamlit.

## How answers work

CareGuide combines a small curated library of paraphrased health guidance with live, query-based results from the [MedlinePlus Web Service](https://medlineplus.gov/about/developers/webservices/), a free U.S. National Library of Medicine search service for health topics. It searches relevant topics and displays source links from MedlinePlus, CDC, WHO, and NHS. Search results are cached for 12 hours to reduce repeated requests. The NLM service limits request volume; this app also spaces outbound requests.

The app does **not train a model**. Without an AI provider key it returns source passages and summaries directly. An optional OpenAI-compatible API key can compose answers from retrieved passages, but the provider may charge for usage. The curated notes and live search are informational, can be incomplete, and are not a comprehensive medical reference.

## Privacy

When a question is submitted, CareGuide may send a short set of topic keywords to MedlinePlus.gov to search for matching health topics. It does not send the chat history to MedlinePlus. Avoid entering names, contact details, or other identifying information. If an AI provider key is configured, the current question and recent conversation context are sent to that provider.

## Sources

- [MedlinePlus Web Service](https://medlineplus.gov/about/developers/webservices/)
- [WHO: Healthy diet](https://www.who.int/news-room/fact-sheets/detail/healthy-diet)
- [WHO: Physical activity](https://www.who.int/news-room/fact-sheets/detail/physical-activity/)
- [CDC: About Sleep](https://www.cdc.gov/sleep/about/)
- [MedlinePlus: Stress](https://medlineplus.gov/stress.html)
- [CDC: Preventive care](https://www.cdc.gov/chronic-disease/prevention/preventive-care.html)
- [CDC: Handwashing](https://www.cdc.gov/Clean-Hands/About/)
- [MedlinePlus: Common Cold](https://medlineplus.gov/commoncold.html)
- [NHS: What to ask your doctor](https://www.nhs.uk/nhs-services/gps/what-to-ask-your-doctor/)

## Deploy on Render

The repository includes a Render Blueprint at `render.yaml`. Connect the GitHub repository to Render and create a Blueprint instance using the `main` branch and free web-service plan. Free services have usage limits and can sleep when idle. GitHub Pages cannot run this Python app.

To enable optional model-written answers, add `OPENAI_API_KEY` in the Render service's environment settings. Never commit keys to GitHub or put them in browser code. Live source lookup works without an AI key.

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

Open the local URL printed by Streamlit. Internet access is needed for live MedlinePlus search; curated source notes remain available if that search is unavailable.

## Medical safety

This is an informational student project, not a medical device or substitute for a qualified healthcare professional. It can make errors and cannot reliably diagnose or detect every emergency. For potentially life-threatening symptoms, call emergency services; in India call 112. Emergency phrase matching is a limited safeguard, not clinical triage.

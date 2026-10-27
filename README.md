# CareGuide — AI Medical Chatbot

CareGuide is a responsive web prototype based on the supplied **AI Chatbot (Medical Care)** synopsis. It uses a browser interface and Python/Flask backend, with Google Gemini as the configured hosted AI provider. API keys are stored server-side and are never sent to browser code.

## Features

- Responsive medical chat interface for desktop and mobile.
- Google Gemini API integration for hosted website responses.
- Google API key is stored only in the hosting provider’s secret environment variables.
- Render deployment blueprint targets a free web service; Gemini API free-tier quotas and model availability are controlled by Google.
- Short-term chat context held in browser memory; no chat database or server-side transcript logging.
- Clearly labelled demo mode when explicitly selected or when optional xAI mode lacks its key.
- Basic emergency phrase screening, medical disclaimer, India emergency number 112.
- Input validation, request-size bounds, basic per-IP rate limiting and security headers.
- Unit tests, Dockerfile, Windows/macOS/Linux launchers, and Render deployment blueprint.

## Run locally on Windows

Requires Python 3.10+ and internet access for the first dependency install.

1. Download or clone this repository.
2. Double-click `start_windows.bat`, or open PowerShell in this folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python app.py
```

For a local run, install [Ollama](https://ollama.com/download) for Windows and run ollama run qwen2.5:3b in PowerShell, then start Flask and open http://127.0.0.1:5000. For the public website, follow “Deploy the website for free” below. Never paste an API key into source files or commit the .env file.

If PowerShell blocks activation, allow it for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## macOS / Linux

Run `./start_mac_linux.sh`, or use:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# For local inference: ollama run qwen2.5:3b
python app.py
```

Open http://127.0.0.1:5000.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `AI_PROVIDER` | `google`, `ollama`, `demo`, or `xai` | `google` on Render; `ollama` locally |
| `GOOGLE_API_KEY` | Gemini key stored server-side only | Blank until configured |\n| `GOOGLE_MODEL` | Gemini model name | `gemini-3.8-flash` |\n| `OLLAMA_API_KEY` | Optional hosted Ollama key | Blank for local mode |
| `OLLAMA_API_URL` | Hosted or local chat endpoint | Auto-selects based on API key |
| `OLLAMA_MODEL` | Hosted or locally installed model | `gemma4:31b` hosted / `qwen2.5:3b` local |
| `XAI_API_KEY` | Optional key when explicitly using xAI | Blank |
| `XAI_MODEL` | Model ID available to your xAI account | `grok-4.6` |
| `RATE_LIMIT_PER_MINUTE` | Per-client request cap per rolling minute | `20` |
| `PORT` | Local or hosted port | `5000` |

When AI_PROVIDER=google and GOOGLE_API_KEY is set, the backend calls the Gemini generateContent API with the key in the x-goog-api-key header. The browser never receives the key. For local development, AI_PROVIDER=ollama can be used with an Ollama server.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests cover the homepage, health endpoint, input validation, emergency response path, demo mode, and security headers. They do not call the live model.

## Deploy the website for free

The Render Blueprint is configured for Google Gemini using a secret environment variable.

1. Open the [Render Dashboard](https://dashboard.render.com/) and choose **New + → Blueprint**.
2. Connect GitHub and select `Jithendra54/Ai-Medical-Chatbot` on branch `main`.
3. Set `GOOGLE_API_KEY` to a **new replacement key** under the service's Environment settings. Do not paste it into the source code, HTML, JavaScript, or GitHub.
4. Keep the service plan set to **Free**. Do not enable paid billing or add credits if your budget is ₹0.
5. Deploy. Open the `onrender.com` URL created by Render and test the chat. The free web service can sleep after inactivity.

Google's Gemini API offers a free tier for selected models, subject to rate and usage limits; verify current terms and quotas for your Google project. Free-tier data handling may differ from paid tiers. Because this is a health-information prototype, do not enter identifiable or sensitive patient details.

**Key security:** A key pasted into a chat is exposed. Revoke or rotate it in [Google AI Studio API keys](https://aistudio.google.com/apikey) or the Google Cloud Credentials page, then enter only the replacement as a Render secret.

## Medical and privacy limitations

- Educational prototype only, **not a medical device, diagnostic system, emergency triage, or substitute for a licensed clinician**. The emergency phrase check can miss emergencies and can generate false alerts; never rely on it to determine risk.
- For potentially life-threatening symptoms, call emergency services. In India call **112**; elsewhere use the local emergency number.
- Demo replies are static examples, not AI-generated or clinically validated.
- The app itself does not persist chat transcripts. In hosted mode, conversation messages are sent to Ollama's cloud to generate replies. Review the provider's current policies before entering health or sensitive information. Do not include names, addresses, ID numbers, or identifying details.
- Before real-world clinical use, seek qualified medical review and complete safety, privacy, security, and legal/regulatory assessments.

## Project structure

```text
app.py
templates/index.html
static/styles.css
static/app.js
tests/test_app.py
.env.example
requirements.txt
start_windows.bat
start_mac_linux.sh
Dockerfile
render.yaml
NOTICE.txt
```

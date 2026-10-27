# CareGuide — AI Medical Chatbot

CareGuide is a responsive web prototype based on the supplied **AI Chatbot (Medical Care)** synopsis. It uses a browser interface and Python/Flask backend. It supports local Ollama and Ollama’s hosted API. Public deployment stores the API key as a server-side secret, never in browser code.

## Features

- Responsive medical chat interface for desktop and mobile.
- Supports local Ollama for development and hosted Ollama API for the public website.
- Hosted mode uses an Ollama API key stored only in the hosting provider’s secret environment variables.
- Render deployment blueprint targets a free web service; Ollama starter-model usage is limited by the account’s included quota.
- Short-term chat context held in browser memory; no chat database or server-side transcript logging.
- Clearly labelled demo mode if `XAI_API_KEY` is not configured.
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
| `AI_PROVIDER` | `ollama`, `demo`, or `xai` | `ollama` |
| `OLLAMA_API_KEY` | Hosted Ollama API key (server secret) | Blank for local mode |
| `OLLAMA_API_URL` | Hosted or local chat endpoint | Auto-selects based on API key |
| `OLLAMA_MODEL` | Hosted or locally installed model | `gemma4:31b` hosted / `qwen2.5:3b` local |
| `XAI_API_KEY` | Optional key when explicitly using xAI | Blank |
| `XAI_MODEL` | Model ID available to your xAI account | `grok-4.6` |
| `RATE_LIMIT_PER_MINUTE` | Per-client request cap per rolling minute | `20` |
| `PORT` | Local or hosted port | `5000` |

When OLLAMA_API_KEY is present, CareGuide calls the hosted endpoint https://ollama.com/api/chat with bearer authentication. Without the key, it uses the local endpoint http://127.0.0.1:11434/api/chat. Use a model supported by your Ollama account. The website never sends the API key to the browser.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests cover the homepage, health endpoint, input validation, emergency response path, demo mode, and security headers. They do not call the live model.

## Deploy the website for free

This repository includes a Render Blueprint for a free Flask web service connected to the hosted Ollama API. Render free services can sleep after inactivity, so the first visit after a quiet period may take around a minute. Ollama’s free account includes limited monthly starter-model usage, not unlimited inference; do not add purchased credits or select paid models if you require a ₹0 budget.

1. Open the [Render Dashboard](https://dashboard.render.com/) and choose New + → Blueprint.
2. Connect GitHub and select Jithendra54/Ai-Medical-Chatbot on branch main.
3. Review the Blueprint. When asked for OLLAMA_API_KEY, enter your key as a secret environment variable. If Render does not prompt for it, open the service’s Environment tab and add OLLAMA_API_KEY as a secret.
4. Keep the instance plan set to Free. Do not add a payment method or buy Ollama credits.
5. Deploy. After the build succeeds, open the generated onrender.com URL and test the chatbot. Check /api/health if needed.

Security: Never put the key into app.py, HTML, JavaScript, README, or a public GitHub issue. If a key has already been exposed, revoke it and create a replacement in [Ollama API key settings](https://ollama.com/settings/keys).

The included Dockerfile can also be used on a compatible container host. Public hosting should use HTTPS and a production WSGI server.

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

# CareGuide — AI Medical Chatbot

CareGuide is a responsive web prototype based on the supplied **AI Chatbot (Medical Care)** synopsis. It uses a browser interface, Python/Flask backend, and xAI/Grok integration.

## Features

- Responsive medical chat interface for desktop and mobile.
- Flask backend and xAI chat-completions integration; the API key stays server-side.
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

Put your own xAI key after `XAI_API_KEY=` in `.env` to enable live Grok responses. Get a key at the [xAI Console](https://console.x.ai/). Leave it blank for demo mode. Open http://127.0.0.1:5000. Keep `.env` private; it is excluded from Git.

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
# Edit .env and set XAI_API_KEY if you want live answers.
python app.py
```

Open http://127.0.0.1:5000.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `XAI_API_KEY` | Enables live xAI API calls | Blank (demo mode) |
| `XAI_MODEL` | Model ID available to your xAI account | `grok-4.6` |
| `RATE_LIMIT_PER_MINUTE` | Per-client request cap per rolling minute | `20` |
| `PORT` | Local or hosted port | `5000` |

The API endpoint is `https://api.x.ai/v1/chat/completions`. Model access and billing depend on your xAI account; adjust `XAI_MODEL` to a model available to your account.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests cover the homepage, health endpoint, input validation, emergency response path, demo mode, and security headers. They do not call the live model.

## Deploy to Render

1. Sign in to [Render](https://render.com/), select **New + → Blueprint**, and connect this GitHub repository. Render will read `render.yaml`.
2. In the service's Environment settings, add `XAI_API_KEY` as a secret environment variable. Do not put it in this repository.
3. Deploy and check that `/api/health` responds with `{"status":"ok", ...}`.

The included Dockerfile can also be used on a compatible container host. Public hosting should use HTTPS and a production WSGI server (the Render configuration uses Gunicorn), not Flask's development server.

## Medical and privacy limitations

- Educational prototype only, **not a medical device, diagnostic system, emergency triage, or substitute for a licensed clinician**. The emergency phrase check can miss emergencies and can generate false alerts; never rely on it to determine risk.
- For potentially life-threatening symptoms, call emergency services. In India call **112**; elsewhere use the local emergency number.
- Demo replies are static examples, not AI-generated or clinically validated.
- The app itself does not persist chat transcripts. In live mode, conversation messages are sent to xAI to generate replies. Review the provider's current policies before entering health or sensitive information. Do not include names, addresses, ID numbers, or identifying details.
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

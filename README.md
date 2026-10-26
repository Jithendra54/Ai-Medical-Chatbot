# CareGuide — AI Medical Chatbot

CareGuide is a responsive web prototype based on the supplied **AI Chatbot (Medical Care)** synopsis. It uses a browser interface and Python/Flask backend. The default AI provider is a local Ollama model, so no paid API key is required.

## Features

- Responsive medical chat interface for desktop and mobile.
- Local AI responses through Ollama by default; no paid API key or per-message API fee.
- Optional xAI integration only if AI_PROVIDER=xai is deliberately configured.
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

Install [Ollama](https://ollama.com/download) for Windows. Then run `ollama run qwen2.5:3b` in PowerShell once to download the model, and keep Ollama running. Start the Flask app using the commands above and open http://127.0.0.1:5000. This local setup avoids paid API charges. On a laptop without a dedicated GPU, responses may be slower; available RAM affects performance. Keep `.env` private; it is excluded from Git.

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
| `AI_PROVIDER` | `ollama`, `demo`, or `xai` | `ollama` |
| `OLLAMA_API_URL` | Local Ollama chat endpoint | `http://127.0.0.1:11434/api/chat` |
| `OLLAMA_MODEL` | Model installed in Ollama | `qwen2.5:3b` |
| `XAI_API_KEY` | Optional key when explicitly using xAI | Blank |
| `XAI_MODEL` | Model ID available to your xAI account | `grok-4.6` |
| `RATE_LIMIT_PER_MINUTE` | Per-client request cap per rolling minute | `20` |
| `PORT` | Local or hosted port | `5000` |

By default, CareGuide calls Ollama at `http://127.0.0.1:11434/api/chat`, which runs on the same machine as Flask. Set `AI_PROVIDER=demo` for canned examples. Optional xAI integration requires `AI_PROVIDER=xai` and a valid `XAI_API_KEY`; this is not needed for the free local setup.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests cover the homepage, health endpoint, input validation, emergency response path, demo mode, and security headers. They do not call the live model.

## Local AI versus public deployment

The default Ollama configuration is for local use on your own computer. If you deploy this Flask app to a public cloud host, `127.0.0.1` refers to that cloud server—not your laptop—so it cannot use Ollama running on your laptop. GitHub Pages cannot run the Flask backend or local model. Public hosting with AI at ₹0 depends on a separate free compute/provider option and its limits; a paid API is not included.

The included Dockerfile can be used on a compatible container host. Public hosting should use HTTPS and a production WSGI server, not Flask’s development server.

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

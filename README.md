# CareGuide — Python AI Medical Chatbot

CareGuide is an educational health-information chatbot served by a Python web server. Python serves the complete interface and handles chat requests.

## Hosting

The repo includes a Render Blueprint at `render.yaml` configured for the free web-service plan. Connect this GitHub repository to Render and create a Blueprint instance. Render's free services may sleep when idle and have resource and usage limits. GitHub Pages cannot run this Python server.

After deploying, add `OPENAI_API_KEY` in the Render service environment. The app uses an OpenAI-compatible chat completions endpoint. Set `OPENAI_MODEL` as needed (default: `gpt-4o-mini`) and optionally `OPENAI_BASE_URL` for a compatible provider. Do not commit API keys or place them in browser code. AI provider usage may cost money; free hosting does not make model inference free.

## Local run

Requires Python 3.10 or newer. No third-party Python packages are needed for the server.

```powershell
$env:OPENAI_API_KEY="your-provider-key"
python app.py
```

Open http://localhost:8000. Without an API key, the page loads but chat displays a setup message; the limited emergency keyword response works locally.

## Privacy and safety

Chat messages are sent to the configured AI provider. CareGuide does not save chat history; the browser sends recent conversation context with each request. Avoid entering identifying or sensitive patient details. This is an informational student project, not a medical device or substitute for a qualified healthcare professional. It can make errors and cannot reliably diagnose or detect every emergency. For potentially life-threatening symptoms, call emergency services; in India call 112.

The emergency phrase check is a limited keyword safeguard, not clinical triage. Do not rely on it to detect emergencies.

## Deployment migration

The existing GitHub Pages workflow serves the previous static WebLLM app. A Python server cannot run on GitHub Pages. This branch adds a Render deployment blueprint, but creating a Render account/service and setting an AI provider key are required before the Python app is publicly live.

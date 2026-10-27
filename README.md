# CareGuide — Browser AI Medical Chatbot

CareGuide is a static website that runs a small open model directly in each visitor's browser using WebLLM and WebGPU. It does not require an AI API key, a Flask server, or paid AI inference.

## Live site

After GitHub Pages is enabled and the deployment workflow succeeds, the site should be available at:

**https://jithendra54.github.io/Ai-Medical-Chatbot/**

## How it works

- **AI engine:** WebLLM with the built-in `Llama-3.2-1B-Instruct-q4f16_1-MLC` model.
- **No API keys:** requests are not sent to Google, Ollama, or a hosted AI provider.
- **On-device inference:** the model runs in the visitor's browser using WebGPU.
- **Model caching:** WebLLM caches model artifacts in the browser where supported, to reduce repeat downloads.
- **Privacy:** chat history remains in page memory and is not sent to a CareGuide server.
- **Automatic deployment:** pushes to `main` build the Vite site and deploy it with GitHub Pages.

WebLLM is a third-party open-source project. Read its documentation at https://github.com/mlc-ai/web-llm.

## Requirements and limitations

- A modern browser with working WebGPU is required; Chrome or Edge are reasonable first choices.
- The first use downloads large model files. This can take time and uses bandwidth/storage on the visitor's device.
- Performance depends on browser, graphics hardware, available memory and thermal limits. Devices without compatible WebGPU support cannot use this browser-only AI.
- This is a small general-purpose model, not a medical model. It can make errors and must not be used for diagnosis, emergency triage, or treatment decisions.
- The site is free to host on GitHub Pages for a public repository, but the visitor's data/bandwidth costs are their own. No AI inference API billing is involved.

## Deploy

1. Open **Settings → Pages** for this repository.
2. Set **Build and deployment → Source** to **GitHub Actions**.
3. Open the **Actions** tab and check the workflow named **Build and deploy CareGuide to GitHub Pages**.
4. Once the workflow finishes successfully, open https://jithendra54.github.io/Ai-Medical-Chatbot/.

The workflow runs on every push to `main`; no secrets are required.

## Local development

Requires Node.js 22+ and npm:

```bash
npm install
npm run dev
```

Open the local URL shown by Vite. To test WebGPU inference locally, use a browser with WebGPU enabled.

## Medical safety

CareGuide is an informational student project, not a medical device or substitute for a qualified healthcare professional. It cannot reliably diagnose illness or detect every emergency. For potentially life-threatening symptoms, call emergency services; in India call 112. Do not enter identifying or sensitive patient information.

## License and attribution

WebLLM is distributed under the Apache-2.0 license by its maintainers. See https://github.com/mlc-ai/web-llm/blob/main/LICENSE for its license.

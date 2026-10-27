import { CreateMLCEngine } from "@mlc-ai/web-llm";
import "../static/styles.css";
import "./style.css";

const MODEL_ID = "Llama-3.2-1B-Instruct-q4f16_1-MLC";
const SYSTEM_PROMPT = [
  "You are CareGuide, a cautious health-information assistant for general education, not a doctor.",
  "Never diagnose, rule out, or confirm a disease. Explain uncertainty clearly.",
  "Never prescribe medicines or provide individualized dosing. Do not tell users to stop prescribed medicines.",
  "For potentially life-threatening symptoms, recommend urgent in-person help immediately. In India call 112; elsewhere call the local emergency number. Do not delay this advice.",
  "Do not claim that the app is clinically validated or that your answers replace a clinician.",
  "Be concise, calm, non-judgmental, and use plain language. Encourage professional advice for worrying, persistent, severe, or worsening symptoms.",
  "Do not ask for names, addresses, government IDs, or other identifying details.",
  "The model is small and can be wrong. Encourage users to verify important health information with a qualified professional."
].join(" ");

const conversation = document.getElementById("conversation");
const welcome = document.getElementById("welcome-state");
const messagesEl = document.getElementById("chat-messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const send = document.getElementById("send-button");
const modePill = document.getElementById("mode-pill");
const modeText = document.getElementById("mode-pill-text");
const notice = document.getElementById("demo-banner");
const noticeText = document.getElementById("notice-text");
const progressWrap = document.getElementById("model-progress-wrap");
const progressBar = document.getElementById("model-progress");
const progressFill = document.getElementById("model-progress-fill");
const progressLabel = document.getElementById("model-progress-label");
const toast = document.getElementById("toast");
const startButton = document.getElementById("start-ai-button");

let engine = null;
let enginePromise = null;
let busy = false;
let toastTimer;
const history = [];

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("toast-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("toast-visible"), 3000);
}

function setMode(mode) {
  modePill.classList.remove("mode-demo", "mode-live", "mode-loading", "mode-ready", "mode-error");
  if (mode === "ready") {
    modePill.classList.add("mode-live", "mode-ready");
    modeText.textContent = "BROWSER AI READY";
    startButton.textContent = "AI Ready";
  } else if (mode === "loading") {
    modePill.classList.add("mode-loading");
    modeText.textContent = "LOADING AI";
    startButton.textContent = "Loading…";
  } else if (mode === "unsupported" || mode === "error") {
    modePill.classList.add("mode-error");
    modeText.textContent = mode === "unsupported" ? "WEBGPU NEEDED" : "LOAD FAILED";
    startButton.textContent = "Retry AI";
  } else {
    modePill.classList.add("mode-demo");
    modeText.textContent = "BROWSER AI";
    startButton.textContent = "Load AI";
  }
  startButton.disabled = mode === "loading" || mode === "ready";
}

function setNotice(message, type = "info") {
  notice.hidden = false;
  noticeText.textContent = message;
  notice.dataset.kind = type;
}

function updateProgress(report) {
  progressWrap.hidden = false;
  const hasPercent = typeof report.progress === "number" && Number.isFinite(report.progress);
  const percent = hasPercent ? Math.max(0, Math.min(100, Math.round(report.progress * 100))) : 0;
  progressFill.style.width = percent + "%";
  progressBar.setAttribute("aria-valuenow", String(percent));
  progressLabel.textContent = report.text || (hasPercent ? "Loading model: " + percent + "%" : "Downloading and preparing the model…");
}

function explainWebGpuProblem() {
  return "This browser/device could not start WebGPU AI. Try the latest Chrome or Edge with hardware acceleration enabled. If this device has no compatible WebGPU graphics support, this no-API browser chatbot cannot run on it.";
}

async function loadEngine() {
  if (engine) return engine;
  if (enginePromise) return enginePromise;
  if (!("gpu" in navigator)) {
    setMode("unsupported");
    setNotice(explainWebGpuProblem(), "error");
    throw new Error(explainWebGpuProblem());
  }

  setMode("loading");
  setNotice("Loading the AI model in your browser. The first load can take a while and downloads model files; the browser may cache them for later visits.", "loading");
  progressWrap.hidden = false;
  progressLabel.textContent = "Checking WebGPU and preparing model…";
  progressFill.style.width = "0%";

  enginePromise = CreateMLCEngine(MODEL_ID, {
    initProgressCallback: (report) => updateProgress(report || {})
  });
  try {
    engine = await enginePromise;
    setMode("ready");
    progressWrap.hidden = true;
    setNotice("Browser AI is ready. Your conversation runs on this device; no AI API key is used. CareGuide is for education, not diagnosis.", "success");
    return engine;
  } catch (error) {
    enginePromise = null;
    engine = null;
    const message = error && error.message ? error.message : String(error);
    const friendly = "Could not load the browser model. " + message + " Check your connection and WebGPU support, then retry.";
    setMode("error");
    setNotice(friendly, "error");
    throw new Error(friendly);
  }
}

function addCopyAction(body, text) {
  const actions = document.createElement("div");
  actions.className = "message-actions";
  const copy = document.createElement("button");
  copy.type = "button";
  copy.className = "copy-button";
  copy.textContent = "Copy response";
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(text);
      showToast("Response copied");
    } catch {
      showToast("Copy is unavailable in this browser");
    }
  });
  actions.append(copy);
  body.append(actions);
}

function addMessage(role, text, options = {}) {
  welcome.hidden = true;
  const article = document.createElement("article");
  article.className = "message message-" + role + (options.pending ? " message-pending" : "");
  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "assistant" ? "✦" : "You";
  const body = document.createElement("div");
  body.className = "message-content";
  const meta = document.createElement("div");
  meta.className = "message-meta";
  const sender = document.createElement("strong");
  sender.textContent = role === "assistant" ? "CareGuide" : "You";
  const time = document.createElement("time");
  time.textContent = new Intl.DateTimeFormat([], { hour: "2-digit", minute: "2-digit" }).format(new Date());
  meta.append(sender, time);
  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;
  body.append(meta, bubble);
  if (role === "assistant" && !options.pending) addCopyAction(body, text);
  if (role === "user") article.append(body, avatar);
  else article.append(avatar, body);
  messagesEl.append(article);
  conversation.scrollTop = conversation.scrollHeight;
  return { article, bubble, body };
}

function autosize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
}

const EMERGENCY_PATTERNS = [
  /\b(chest pain|pressure in (my )?chest)\b/i,
  /\b(can't breathe|cannot breathe|difficulty breathing|shortness of breath)\b/i,
  /\b(face droop|slurred speech|sudden weakness|stroke symptoms?)\b/i,
  /\b(unconscious|not waking up|severe bleeding|throat closing|overdose|active seizure)\b/i,
  /\b(kill myself|suicidal intent|going to harm myself)\b/i
];

function possibleEmergency(text) {
  return EMERGENCY_PATTERNS.some((pattern) => pattern.test(text));
}

function localEmergencyReply() {
  return "Please seek urgent medical help now. Do not wait for an AI response. If you are in India, call 112; otherwise call your local emergency number. Ask someone nearby to help. This automated warning is limited and is not a medical assessment.";
}

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt || "";
    autosize();
    input.focus();
  });
});

document.getElementById("dismiss-demo-banner")?.addEventListener("click", () => {
  notice.hidden = true;
});

document.getElementById("new-chat-button")?.addEventListener("click", () => {
  history.length = 0;
  messagesEl.replaceChildren();
  welcome.hidden = false;
  showToast("New conversation started");
  input.focus();
});

document.getElementById("mobile-menu-button")?.addEventListener("click", () => {
  const shell = document.querySelector(".app-shell");
  const button = document.getElementById("mobile-menu-button");
  const open = shell.classList.toggle("sidebar-open");
  button.setAttribute("aria-expanded", String(open));
});

startButton.addEventListener("click", async () => {
  if (busy || engine) return;
  startButton.disabled = true;
  try {
    await loadEngine();
    showToast("Browser AI is ready");
  } catch (error) {
    showToast(error.message || "Could not load AI");
  } finally {
    if (!engine) startButton.disabled = false;
  }
});

input.addEventListener("input", autosize);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || busy) return;
  input.value = "";
  autosize();
  addMessage("user", text);
  busy = true;
  send.disabled = true;
  startButton.disabled = true;

  try {
    if (possibleEmergency(text)) {
      const reply = localEmergencyReply();
      history.push({ role: "user", content: text }, { role: "assistant", content: reply });
      addMessage("assistant", reply);
      return;
    }

    const ai = await loadEngine();
    history.push({ role: "user", content: text });
    const pending = addMessage("assistant", "Thinking…", { pending: true });
    let responseText = "";
    try {
      const stream = await ai.chat.completions.create({
        messages: [{ role: "system", content: SYSTEM_PROMPT }, ...history.slice(-10)],
        temperature: 0.2,
        max_tokens: 500,
        stream: true
      });
      for await (const chunk of stream) {
        const token = chunk.choices && chunk.choices[0] && chunk.choices[0].delta && chunk.choices[0].delta.content;
        if (typeof token === "string" && token) {
          responseText += token;
          pending.bubble.textContent = responseText;
          conversation.scrollTop = conversation.scrollHeight;
        }
      }
      if (!responseText.trim()) responseText = "The model did not return a response. Please try again.";
      pending.bubble.textContent = responseText;
      pending.article.classList.remove("message-pending");
      addCopyAction(pending.body, responseText);
      history.push({ role: "assistant", content: responseText });
    } catch (error) {
      pending.bubble.textContent = "I couldn't generate a response: " + (error.message || String(error));
      pending.article.classList.remove("message-pending");
      history.pop();
    }
  } catch (error) {
    addMessage("assistant", error.message || "The browser AI could not start on this device.");
  } finally {
    busy = false;
    send.disabled = false;
    startButton.disabled = Boolean(engine);
    input.focus();
  }
});

setMode("idle");
autosize();

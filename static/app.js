(() => {
  "use strict";
  const conversation = document.getElementById("conversation");
  const welcome = document.getElementById("welcome-state");
  const messagesEl = document.getElementById("chat-messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("message-input");
  const send = document.getElementById("send-button");
  const modePill = document.getElementById("mode-pill");
  const modeText = document.getElementById("mode-pill-text");
  const demoBanner = document.getElementById("demo-banner");
  const toast = document.getElementById("toast");
  const history = [];
  let busy = false;
  let toastTimer;

  function showToast(message) {
    toast.textContent = message;
    toast.classList.add("toast-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("toast-visible"), 2600);
  }

  function setMode(mode) {
    const live = mode === "grok";
    modePill.classList.toggle("mode-live", live);
    modePill.classList.toggle("mode-demo", !live);
    modeText.textContent = live ? "GROK AI" : "DEMO MODE";
    demoBanner.hidden = live;
  }

  function addMessage(role, text, options = {}) {
    welcome.hidden = true;
    const article = document.createElement("article");
    article.className = `message message-${role}`;
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
    time.textContent = new Intl.DateTimeFormat([], {hour:"2-digit",minute:"2-digit"}).format(new Date());
    meta.append(sender, time);
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    // Render all model/user text as text nodes; never interpret it as HTML.
    bubble.textContent = text;
    body.append(meta,bubble);
    if (role === "assistant" && !options.pending) {
      const actions = document.createElement("div");
      actions.className = "message-actions";
      const copy = document.createElement("button");
      copy.type = "button";
      copy.className = "copy-button";
      copy.textContent = "Copy response";
      copy.addEventListener("click", async () => {
        try { await navigator.clipboard.writeText(text); showToast("Response copied"); }
        catch { showToast("Copy is unavailable in this browser"); }
      });
      actions.append(copy);
      body.append(actions);
    }
    if (role === "user") article.append(body,avatar);
    else article.append(avatar,body);
    messagesEl.append(article);
    conversation.scrollTop = conversation.scrollHeight;
    return {article,bubble};
  }

  function addTyping() {
    const result = addMessage("assistant","CareGuide is preparing a response…",{pending:true});
    result.article.classList.add("message-pending");
    return result.article;
  }

  function autosize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 160) + "px";
  }

  document.querySelectorAll("[data-prompt]").forEach(button => {
    button.addEventListener("click", () => {
      input.value = button.dataset.prompt || "";
      autosize();
      input.focus();
    });
  });

  document.getElementById("dismiss-demo-banner")?.addEventListener("click", () => {
    demoBanner.hidden = true;
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

  input.addEventListener("input", autosize);
  input.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async event => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text || busy) return;
    input.value = "";
    autosize();
    history.push({role:"user",content:text});
    addMessage("user",text);
    busy = true;
    send.disabled = true;
    const pending = addTyping();
    try {
      const response = await fetch("/api/chat", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({messages:history.slice(-12)})
      });
      const data = await response.json();
      pending.remove();
      if (!response.ok) {
        history.pop();
        addMessage("assistant",data.error || "The request could not be completed. Please try again.");
      } else {
        setMode(data.mode || "demo");
        addMessage("assistant",data.reply || "No response was returned.");
        history.push({role:"assistant",content:data.reply || ""});
        if (data.emergency) showToast("Urgent health guidance displayed");
      }
    } catch {
      pending.remove();
      history.pop();
      addMessage("assistant","I couldn't connect to the server. Check your internet connection and try again.");
    } finally {
      busy = false;
      send.disabled = false;
      input.focus();
    }
  });

  fetch("/api/health").then(r=>r.json()).then(data=>setMode(data.mode)).catch(()=>setMode("demo"));
  autosize();
})();

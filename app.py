import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
API_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
SYSTEM_PROMPT = """You are CareGuide, a cautious health-information assistant for general education, not a doctor.
Never diagnose, rule out, or confirm a disease. Explain uncertainty clearly.
Never prescribe medicines or provide individualized dosing. Do not tell users to stop prescribed medicines.
For potentially life-threatening symptoms, recommend urgent in-person help immediately. In India call 112; elsewhere call the local emergency number. Do not delay this advice.
Do not claim clinical validation or that your answers replace a clinician. Be concise, calm, non-judgmental, and use plain language.
Encourage professional advice for worrying, persistent, severe, or worsening symptoms. Do not request identifying details.
This model can be wrong. Encourage verification with a qualified professional."""

EMERGENCY_PATTERNS = [
    r"\\b(chest pain|pressure in (my )?chest)\\b",
    r"\\b(can't breathe|cannot breathe|difficulty breathing|shortness of breath)\\b",
    r"\\b(face droop|slurred speech|sudden weakness|stroke symptoms?)\\b",
    r"\\b(unconscious|not waking up|severe bleeding|throat closing|overdose|active seizure)\\b",
    r"\\b(kill myself|suicidal intent|going to harm myself)\\b",
]
EMERGENCY_REPLY = ("Please seek urgent medical help now. Do not wait for an AI response. "
                   "If you are in India, call 112; otherwise call your local emergency number. "
                   "Ask someone nearby to help. This automated warning is limited and is not a medical assessment.")

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f6f8fc">
<meta name="description" content="CareGuide offers general health information and helps prepare for a clinician visit.">
<title>CareGuide — Health information assistant</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:#172b3a;background:#f6f8fc;font-synthesis:none}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 72% 2%,#e7f4f1 0,transparent 35%),#f6f8fc}
button,textarea{font:inherit}.shell{max-width:1440px;min-height:100vh;margin:auto;display:grid;grid-template-columns:290px 1fr}
aside{background:#fff;border-right:1px solid #e8edf1;padding:26px 20px;display:flex;flex-direction:column;gap:22px}
.brand{display:flex;gap:12px;align-items:center;text-decoration:none;color:inherit}.brand-mark{width:42px;height:42px;border-radius:14px;background:#dff3ee;color:#18866c;display:grid;place-items:center;font-size:25px;font-weight:700}.brand-mark span{display:block}.brand strong{display:block;font-size:17px;letter-spacing:-.03em}.brand small,.topic small{display:block;color:#768793;font-size:12px;margin-top:3px}
.new-chat{border:0;border-radius:12px;padding:13px 14px;background:#117c69;color:#fff;font-weight:650;text-align:left;cursor:pointer}
.section-title{font-size:10px;letter-spacing:.13em;color:#84949e;font-weight:750;margin-top:4px}
.topics{display:grid;gap:8px}.topic{background:white;border:1px solid #e9eef1;border-radius:13px;padding:12px;text-align:left;cursor:pointer;color:#243746}.topic:hover,.suggestion:hover{border-color:#9bcbbd;background:#f8fcfa}.topic strong{font-size:13px}.topic-icon{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:9px;background:#e6f4f1;color:#157b68;margin-right:7px}
.spacer{flex:1}.urgent{border:1px solid #f1d9d5;border-radius:15px;background:#fff9f7;padding:15px}.urgent b{font-size:12px;color:#ae4b40}.urgent p{font-size:12px;line-height:1.5;color:#566875}.urgent a{color:#a43c36;font-weight:750;text-decoration:none}.privacy{font-size:12px;color:#60727d;line-height:1.5}
main{height:100vh;min-height:650px;display:flex;flex-direction:column}.topbar{height:68px;border-bottom:1px solid #e6ecef;background:#ffffffc9;display:flex;align-items:center;justify-content:space-between;padding:0 34px}.crumb{font-size:13px;color:#73838e}.crumb strong{color:#263c49}.pill{padding:7px 11px;border-radius:999px;background:#e5f4ef;color:#18715e;font-size:11px;font-weight:750;letter-spacing:.05em}
.content{width:min(850px,100%);padding:28px 30px 20px;margin:auto;flex:1;min-height:0;display:flex;flex-direction:column}
.banner{background:#eef6fa;border:1px solid #dcebf1;color:#476574;padding:12px 14px;border-radius:12px;font-size:12px;line-height:1.5;margin-bottom:18px}
.conversation{flex:1;min-height:220px;overflow:auto;padding:12px 5px}
.welcome{text-align:center;padding:4px 0 18px}.orb{width:62px;height:62px;border-radius:22px;background:linear-gradient(145deg,#dbf2ed,#edf4ff);display:grid;place-items:center;color:#13836e;font-size:30px;margin:0 auto 16px}
.eyebrow{font-size:10px;letter-spacing:.14em;color:#568b7e;font-weight:800}.welcome h1{font-size:clamp(32px,5vw,48px);line-height:1.08;letter-spacing:-.055em;margin:13px 0;color:#173343}.welcome h1 span{color:#16816b}.welcome p{color:#687985;max-width:550px;margin:0 auto;font-size:14px;line-height:1.6}
.suggestions{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:24px 0}.suggestion{min-height:88px;text-align:left;border:1px solid #e3eaed;background:#fff;border-radius:13px;padding:13px;cursor:pointer;color:#263c49}.suggestion strong{display:block;font-size:12px;margin-bottom:5px}.suggestion small{color:#72828d;font-size:11px;line-height:1.4}
.disclaimer{font-size:11px;color:#84919a}.messages{display:grid;gap:17px}.message{display:flex;gap:10px;max-width:88%;align-items:flex-start}.message.user{margin-left:auto;flex-direction:row-reverse}.avatar{width:30px;height:30px;flex:none;border-radius:11px;background:#def2ec;color:#147b66;display:grid;place-items:center;font-size:12px;font-weight:800}.user .avatar{background:#e9edf8;color:#596aab}.bubble-wrap{min-width:0}.meta{font-size:11px;color:#71818c;margin:0 0 5px 2px}.bubble{background:#fff;border:1px solid #e7ecee;border-radius:4px 14px 14px;padding:12px 14px;line-height:1.6;font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere}.user .bubble{background:#eaf5f2;border-color:#d7ebe5;border-radius:14px 4px 14px 14px}.copy{border:0;background:none;color:#657a84;font-size:11px;padding:7px 2px;cursor:pointer}
.composer{border:1px solid #dfe7e9;border-radius:16px;background:white;padding:11px;box-shadow:0 10px 35px #2039470a}.composer textarea{width:100%;resize:none;border:0;outline:0;padding:8px;max-height:160px;min-height:48px;color:#243746}.composer textarea::placeholder{color:#9ba8ae}.controls{display:flex;align-items:center;justify-content:space-between;padding:0 4px}.hint{font-size:10px;color:#8a989f}.send{border:0;background:#137e6a;color:white;border-radius:10px;padding:9px 15px;font-weight:700;cursor:pointer}.send:disabled{opacity:.55}.foot{display:flex;justify-content:space-between;gap:10px;color:#8b979d;font-size:10px;padding:10px 3px 0}.toast{position:fixed;bottom:25px;left:50%;transform:translate(-50%,20px);opacity:0;background:#183c40;color:white;padding:11px 16px;border-radius:12px;font-size:12px;transition:.2s;pointer-events:none}.toast.show{opacity:1;transform:translate(-50%,0)}
@media(max-width:800px){.shell{grid-template-columns:1fr}aside{display:none}.topbar{padding:0 18px}.content{padding:18px 15px 13px}.suggestions{grid-template-columns:1fr}.suggestion{min-height:auto}.foot{display:block;line-height:1.6}.message{max-width:96%}}
</style>
</head>
<body>
<div class="shell">
<aside>
<a class="brand" href="/"><span class="brand-mark">+</span><span><strong>CareGuide</strong><small>Health, made clearer</small></span></a>
<button class="new-chat" id="new-chat">＋ &nbsp;New conversation</button>
<div class="section-title">EXPLORE HEALTH TOPICS</div>
<div class="topics">
<button class="topic" data-prompt="What can help with mild cold symptoms at home?"><span class="topic-icon">✚</span><strong>Common symptoms</strong><small>Everyday health information</small></button>
<button class="topic" data-prompt="What are practical habits for improving sleep quality?"><span class="topic-icon">☾</span><strong>Sleep &amp; wellbeing</strong><small>Build healthy routines</small></button>
<button class="topic" data-prompt="Help me prepare questions to ask a doctor about a new symptom."><span class="topic-icon">☷</span><strong>Doctor visit prep</strong><small>Prepare for a clinician visit</small></button>
</div>
<div class="spacer"></div>
<section class="urgent"><b>● &nbsp;NEED URGENT HELP?</b><p>Do not wait for an AI response if someone may be in danger.</p><a href="tel:112">India emergency number &nbsp;112 ↗</a><p>Outside India, call your local emergency number.</p></section>
<div class="privacy">✓ &nbsp;Messages are processed by the configured AI provider and are not stored by CareGuide.</div>
</aside>
<main>
<header class="topbar"><div class="crumb">Health tools &nbsp; / &nbsp; <strong>Virtual assistant</strong></div><span class="pill">PYTHON WEB APP</span></header>
<div class="content">
<div class="banner"><strong>For education only.</strong> CareGuide cannot diagnose or replace professional medical care. Avoid sharing names or identifying details. If this may be an emergency, call emergency services.</div>
<section class="conversation" id="conversation" aria-live="polite">
<div class="welcome" id="welcome"><div class="orb">✚</div><div class="eyebrow">YOUR HEALTH INFORMATION COMPANION</div><h1>How can I help<br><span>you feel informed?</span></h1><p>Ask a general health question, learn about common symptoms, or prepare for a conversation with a healthcare professional.</p>
<div class="suggestions">
<button class="suggestion" data-prompt="What can help with mild cold symptoms at home?"><strong>✚ &nbsp;Common symptoms</strong><small>Understand what you are experiencing</small></button>
<button class="suggestion" data-prompt="What are practical habits for improving sleep quality?"><strong>☾ &nbsp;Healthy routines</strong><small>Small steps for everyday wellbeing</small></button>
<button class="suggestion" data-prompt="Help me prepare questions to ask a doctor about a new symptom."><strong>☷ &nbsp;Prepare for a visit</strong><small>Organise notes for your clinician</small></button>
</div><div class="disclaimer">CareGuide can make mistakes. Verify important information with a qualified healthcare professional.</div></div>
<div class="messages" id="messages"></div>
</section>
<div class="composer"><form id="form"><textarea id="input" maxlength="2000" rows="2" placeholder="Ask a health question…" aria-label="Your health question" required></textarea><div class="controls"><span class="hint">ⓘ Avoid sharing names or identifying details.</span><button class="send" id="send" type="submit">Send &nbsp;➤</button></div></form></div>
<div class="foot"><span>Informational use only. Not a diagnosis.</span><span>Enter to send · Shift + Enter for a new line</span></div>
</div>
</main>
</div><div id="toast" class="toast" role="status" aria-live="polite"></div>
<script>
const form=document.querySelector("#form"),input=document.querySelector("#input"),messages=document.querySelector("#messages"),welcome=document.querySelector("#welcome"),conversation=document.querySelector("#conversation"),send=document.querySelector("#send"),toast=document.querySelector("#toast");
let history=[],busy=false,timer;
function notify(s){toast.textContent=s;toast.classList.add("show");clearTimeout(timer);timer=setTimeout(()=>toast.classList.remove("show"),2600)}
function append(role,text){welcome.hidden=true;const row=document.createElement("article");row.className="message "+role;const avatar=document.createElement("div");avatar.className="avatar";avatar.textContent=role==="assistant"?"✦":"You";const wrap=document.createElement("div");wrap.className="bubble-wrap";const meta=document.createElement("div");meta.className="meta";meta.textContent=role==="assistant"?"CareGuide":"You";const bubble=document.createElement("div");bubble.className="bubble";bubble.textContent=text;wrap.append(meta,bubble);row.append(avatar,wrap);messages.append(row);conversation.scrollTop=conversation.scrollHeight;return{row,bubble,wrap}}
document.querySelectorAll("[data-prompt]").forEach(b=>b.addEventListener("click",()=>{input.value=b.dataset.prompt;input.focus()}));
document.querySelector("#new-chat").addEventListener("click",()=>{history=[];messages.replaceChildren();welcome.hidden=false;input.focus();notify("New conversation started")});
input.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();form.requestSubmit()}});
form.addEventListener("submit",async e=>{e.preventDefault();const text=input.value.trim();if(!text||busy)return;input.value="";append("user",text);busy=true;send.disabled=true;const pending=append("assistant","Thinking…");try{history.push({role:"user",content:text});const response=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text,history:history.slice(-10,-1)})});const data=await response.json();if(!response.ok)throw new Error(data.error||"The request failed");pending.bubble.textContent=data.reply;history.push({role:"assistant",content:data.reply});const copy=document.createElement("button");copy.className="copy";copy.textContent="Copy response";copy.onclick=async()=>{try{await navigator.clipboard.writeText(data.reply);notify("Response copied")}catch{notify("Copy is unavailable")}};pending.wrap.append(copy)}catch(err){pending.bubble.textContent=err.message||"Could not get a response";history.pop()}finally{busy=false;send.disabled=false;input.focus()}});
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif self.path == "/health":
            self._send(200, '{"status":"ok"}')
        else:
            self._send(404, '{"error":"Not found"}')

    def do_POST(self):
        if self.path != "/api/chat":
            self._send(404, '{"error":"Not found"}')
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 12000:
                self._send(400, json.dumps({"error": "Please send a shorter message."}))
                return
            payload = json.loads(self.rfile.read(size))
            message = payload.get("message", "")
            if not isinstance(message, str) or not message.strip() or len(message) > 2000:
                self._send(400, json.dumps({"error": "Enter a question under 2,000 characters."}))
                return
            if any(re.search(pattern, message, re.I) for pattern in EMERGENCY_PATTERNS):
                self._send(200, json.dumps({"reply": EMERGENCY_REPLY}))
                return
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self._send(503, json.dumps({"error": "AI provider is not configured yet. Set OPENAI_API_KEY in the hosting service environment."}))
                return
            raw_history = payload.get("history", [])
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if isinstance(raw_history, list):
                for item in raw_history[-8:]:
                    if isinstance(item, dict) and item.get("role") in ("user", "assistant") and isinstance(item.get("content"), str):
                        messages.append({"role": item["role"], "content": item["content"][:2000]})
            messages.append({"role": "user", "content": message.strip()})
            request_data = json.dumps({"model": MODEL, "messages": messages, "temperature": 0.2, "max_tokens": 500}).encode("utf-8")
            req = Request(API_URL, data=request_data, headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=45) as response:
                result = json.loads(response.read(1000000))
            reply = result["choices"][0]["message"]["content"]
            self._send(200, json.dumps({"reply": reply}))
        except HTTPError as exc:
            self._send(502, json.dumps({"error": "The AI provider returned an error. Check its API key, model access, and usage limits."}))
        except (URLError, TimeoutError):
            self._send(502, json.dumps({"error": "The AI provider could not be reached. Try again shortly."}))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            self._send(400, '{"error":"The request was not valid."}')
        except Exception:
            self._send(500, '{"error":"Something went wrong. Please try again."}')

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))

if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

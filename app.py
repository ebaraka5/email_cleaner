from flask import Flask, request, jsonify, session
import imaplib
import email
from email.header import decode_header
import os
import re
from datetime import timedelta

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MailSweep - Email Cleanup</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0a0a0f;--surface:#13131a;--border:#252535;--accent:#e8ff5a;--accent2:#ff5a7e;--text:#e8e8f0;--muted:#6b6b8a;--danger:#ff4444;--success:#4aff91;--mono:'DM Mono',monospace;--sans:'Syne',sans-serif;--radius:12px;--transition:0.18s cubic-bezier(.4,0,.2,1)}
html{font-size:16px}
body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:2rem 1rem 4rem;background-image:radial-gradient(ellipse 80% 40% at 50% -10%,rgba(232,255,90,0.07) 0%,transparent 60%),radial-gradient(ellipse 40% 30% at 90% 80%,rgba(255,90,126,0.05) 0%,transparent 50%)}
header{width:100%;max-width:700px;display:flex;align-items:baseline;gap:1rem;margin-bottom:3rem;padding-top:1rem}
.logo{font-size:1.8rem;font-weight:800;letter-spacing:-0.03em;color:var(--text)}
.logo span{color:var(--accent)}
.tagline{font-family:var(--mono);font-size:0.7rem;color:var(--muted);letter-spacing:0.08em;text-transform:uppercase}
.card{width:100%;max-width:700px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:2rem;margin-bottom:1.5rem;animation:fadeUp 0.4s ease both}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
.card h2{font-size:0.75rem;font-family:var(--mono);text-transform:uppercase;letter-spacing:0.12em;color:var(--muted);margin-bottom:1.25rem}
label{display:block;font-family:var(--mono);font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;margin-top:1rem}
label:first-of-type{margin-top:0}
input[type="text"],input[type="email"],input[type="password"]{width:100%;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);font-family:var(--mono);font-size:0.9rem;padding:0.7rem 1rem;outline:none;transition:border-color var(--transition)}
input:focus{border-color:var(--accent)}
input::placeholder{color:var(--muted)}
button{font-family:var(--sans);font-weight:600;font-size:0.88rem;border:none;border-radius:8px;cursor:pointer;padding:0.7rem 1.4rem;transition:all var(--transition);letter-spacing:0.01em;white-space:nowrap}
.btn-primary{background:var(--accent);color:#0a0a0f;width:100%;margin-top:1.25rem;padding:0.85rem;font-size:0.95rem}
.btn-primary:hover{background:#f5ff80;transform:translateY(-1px)}
.btn-primary:active{transform:translateY(0)}
.btn-primary:disabled{opacity:0.4;cursor:not-allowed;transform:none}
.btn-danger{background:0;color:var(--danger);border:1px solid var(--danger);padding:0.5rem 1rem;font-size:0.8rem}
.btn-danger:hover{background:rgba(255,68,68,0.1)}
.btn-ghost{background:0;color:var(--muted);border:1px solid var(--border);font-size:0.78rem;padding:0.45rem 0.9rem}
.btn-ghost:hover{color:var(--text);border-color:var(--muted)}
.status{font-family:var(--mono);font-size:0.78rem;padding:0.6rem 0.9rem;border-radius:6px;margin-top:0.9rem;display:none}
.status.info{background:rgba(232,255,90,0.08);color:var(--accent);display:block}
.status.error{background:rgba(255,68,68,0.08);color:var(--danger);display:block}
.status.success{background:rgba(74,255,145,0.08);color:var(--success);display:block}
.who{font-family:var(--mono);font-size:0.78rem;color:var(--muted);display:flex;align-items:center;gap:0.6rem;margin-bottom:1.25rem}
.who .dot{width:7px;height:7px;background:var(--success);border-radius:50%;display:inline-block;box-shadow:0 0 6px var(--success)}
.sender-list{max-height:380px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.sender-item{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:0.65rem 0;border-bottom:1px solid var(--border);animation:fadeUp 0.2s ease both}
.sender-item:last-child{border-bottom:0}
.sender-info{flex:1;min-width:0}
.sender-name{font-family:var(--mono);font-size:0.82rem;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sender-count{font-family:var(--mono);font-size:0.7rem;color:var(--muted)}
.sender-actions{display:flex;gap:0.5rem;flex-shrink:0}
.search-wrap{position:relative;margin-bottom:1rem}
.search-wrap input{padding-left:2.2rem}
.search-icon{position:absolute;left:0.75rem;top:50%;transform:translateY(-50%);color:var(--muted);font-size:0.85rem;pointer-events:none}
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:100;backdrop-filter:blur(4px);opacity:0;pointer-events:none;transition:opacity var(--transition)}
.modal-overlay.open{opacity:1;pointer-events:all}
.modal{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:2rem;max-width:420px;width:90%;transform:scale(0.95);transition:transform var(--transition)}
.modal-overlay.open .modal{transform:scale(1)}
.modal h3{font-size:1.1rem;margin-bottom:0.5rem}
.modal p{font-family:var(--mono);font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem;line-height:1.6}
.modal p strong{color:var(--accent2)}
.modal-actions{display:flex;gap:0.75rem;justify-content:flex-end}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid rgba(0,0,0,0.2);border-top-color:#0a0a0f;border-radius:50%;animation:spin 0.7s linear infinite;vertical-align:middle;margin-right:6px}
@keyframes spin{to{transform:rotate(360deg)}}
[data-section]{display:none}
[data-section].active{display:block}
.tip{background:rgba(232,255,90,0.04);border:1px solid rgba(232,255,90,0.15);border-radius:8px;padding:0.75rem 1rem;font-family:var(--mono);font-size:0.74rem;color:var(--muted);line-height:1.6;margin-top:1rem}
.tip strong{color:var(--accent)}
.empty{text-align:center;padding:2rem;font-family:var(--mono);font-size:0.8rem;color:var(--muted)}
</style>
</head>
<body>

<header>
  <div class="logo">Mail<span>Sweep</span></div>
  <div class="tagline">// bulk email cleanup</div>
</header>

<div class="card" data-section="login" id="sec-login">
  <h2>// Connect your email</h2>
  <label>Email address</label>
  <input type="email" id="inp-email" placeholder="you@example.com">
  <label>Password / App Password</label>
  <input type="password" id="inp-pass" placeholder="••••••••••••">
  <label>IMAP server (optional)</label>
  <input type="text" id="inp-imap" placeholder="leave blank for auto-detect">
  <div class="tip"><strong>Gmail/Outlook/Yahoo?</strong> You need an App Password. Gmail: myaccount.google.com/apppasswords</div>
  <button class="btn-primary" id="btn-login">Connect</button>
  <div class="status" id="login-status"></div>
</div>

<div class="card" data-section="main" id="sec-main">
  <div class="who"><span class="dot"></span><span id="lbl-who">connected</span><button class="btn-ghost" id="btn-logout">logout</button></div>
  <h2>// Delete by sender</h2>
  <label>Sender to delete</label>
  <input type="text" id="inp-sender" placeholder="spam@example.com">
  <button class="btn-primary" id="btn-preview">Preview</button>
  <div class="status" id="preview-status"></div>
  <div id="confirm-wrap" style="display:none;margin-top:1rem;">
    <button class="btn-danger" style="width:100%;padding:0.8rem" id="btn-delete">Delete All</button>
  </div>
  <div class="status" id="delete-status"></div>
</div>

<div class="card" data-section="senders" id="sec-senders">
  <h2>// Top senders</h2>
  <button class="btn-primary" id="btn-scan">Scan mailbox</button>
  <div class="search-wrap" id="search-wrap" style="display:none;margin-top:1rem">
    <span class="search-icon">⌕</span>
    <input type="text" id="inp-search" placeholder="Filter...">
  </div>
  <div class="sender-list" id="sender-list"><div class="empty">Click Scan to load senders.</div></div>
  <div class="status" id="scan-status"></div>
</div>

<div class="modal-overlay" id="modal">
  <div class="modal">
    <h3>Confirm delete?</h3>
    <p>Delete <strong id="modal-count">0</strong> emails from <strong id="modal-sender"></strong>. Cannot undo.</p>
    <div class="modal-actions">
      <button class="btn-ghost" id="modal-cancel">Cancel</button>
      <button class="btn-danger" id="modal-confirm">Yes, delete</button>
    </div>
  </div>
</div>

<script>
var $=function(id){return document.getElementById(id)};
var show=function(id){$(id).style.display=''};
var hide=function(id){$(id).style.display='none'};

function setStatus(id,type,msg){var el=$(id);el.className='status '+type;el.textContent=msg}
function clearStatus(id){var el=$(id);el.className='status';el.textContent=''}

function showSection(name){
  ['login','main','senders'].forEach(function(s){
    var el=$('sec-'+s);
    el.style.display=s===name?'block':'none';
  });
  if(name==='main')$('sec-senders').style.display='block';
}

async function api(path,body){
  var opts={method:body?'POST':'GET',headers:{'Content-Type':'application/json'}};
  if(body)opts.body=JSON.stringify(body);
  var r=await fetch(path,opts);
  return r.json();
}

// LOGIN
$('btn-login').addEventListener('click',async function(){
  var btn=$('btn-login');
  btn.disabled=true;
  btn.innerHTML='<span class="spinner"></span> Connecting...';
  clearStatus('login-status');
  var res=await api('/api/login',{email:$('inp-email').value,password:$('inp-pass').value,imap_server:$('inp-imap').value});
  if(res.ok){$('lbl-who').textContent=$('inp-email').value;showSection('main')}
  else{setStatus('login-status','error','✗ '+res.error)}
  btn.disabled=false;
  btn.textContent='Connect';
});

// LOGOUT
$('btn-logout').addEventListener('click',async function(){
  await api('/api/logout',{});
  showSection('login');
  $('inp-pass').value='';
  hide('confirm-wrap');
  clearStatus('preview-status');
  clearStatus('delete-status');
});

// PREVIEW
$('btn-preview').addEventListener('click',async function(){
  var sender=$('inp-sender').value.trim();
  if(!sender){setStatus('preview-status','error','Enter a sender.');return}
  clearStatus('preview-status');hide('confirm-wrap');
  $('btn-preview').innerHTML='<span class="spinner"></span>';
  $('btn-preview').disabled=true;
  var res=await api('/api/preview',{sender:sender});
  $('btn-preview').textContent='Preview';
  $('btn-preview').disabled=false;
  if(res.ok){
    if(res.count===0){setStatus('preview-status','info','No emails found.')}
    else{setStatus('preview-status','info','Found '+res.count+' email(s).');show('confirm-wrap');window._pendingCount=res.count}
  }else{setStatus('preview-status','error','✗ '+res.error)}
});

// MODAL
var _pendingSender=null;
function openConfirmModal(sender,count){_pendingSender=sender;$('modal-count').textContent=count;$('modal-sender').textContent=sender;$('modal').classList.add('open')}

$('btn-delete').addEventListener('click',function(){var sender=$('inp-sender').value.trim();openConfirmModal(sender,window._pendingCount||'?')});

$('modal-cancel').addEventListener('click',function(){$('modal').classList.remove('open');_pendingSender=null});

$('modal-confirm').addEventListener('click',async function(){
  $('modal').classList.remove('open');
  var sender=_pendingSender;
  _pendingSender=null;
  if(!sender)return;
  $('btn-delete').disabled=true;
  $('btn-delete').innerHTML='<span class="spinner" style="border-top-color:var(--danger)"></span> Deleting...';
  clearStatus('delete-status');
  var res=await api('/api/delete',{sender:sender});
  $('btn-delete').disabled=false;
  $('btn-delete').innerHTML='Delete All';
  if(res.ok){
    setStatus('delete-status','success','✓ Deleted '+res.deleted);
    hide('confirm-wrap');clearStatus('preview-status');$('inp-sender').value='';
    if($('sender-list').dataset.loaded)loadSenders();
  }else{setStatus('delete-status','error','✗ '+res.error)}
});

// SCANNER
var allSenders=[];
$('btn-scan').addEventListener('click',loadSenders);

async function loadSenders(){
  $('btn-scan').innerHTML='<span class="spinner"></span> Scanning...';
  $('btn-scan').disabled=true;
  $('sender-list').innerHTML='<div class="empty">Scanning...</div>';
  hide('search-wrap');clearStatus('scan-status');
  var res=await api('/api/senders');
  $('btn-scan').textContent='Rescan';$('btn-scan').disabled=false;
  if(res.ok){
    allSenders=res.senders;$('sender-list').dataset.loaded='1';show('search-wrap');renderSenders(allSenders);
  }else{setStatus('scan-status','error','✗ '+res.error)}
}

var senderStore={};
function renderSenders(list){
  if(list.length===0){$('sender-list').innerHTML='<div class="empty">No senders.</div>';return}
  senderStore={};
  var html='';
  for(var i=0;i<list.length;i++){
    var sender=list[i][0],count=list[i][1],idx='s'+i;
    senderStore[idx]={sender:sender,count:count};
    html+='<div class="sender-item"><div class="sender-info"><div class="sender-name" title="'+esc(sender)+'">'+esc(sender)+'</div><div class="sender-count">'+count+' email'+(count!==1?'s':'')+' </div></div><div class="sender-actions"><button class="btn-ghost" onclick="window._selectClick(''+idx+'')">Select</button><button class="btn-danger" onclick="window._deleteClick(''+idx+'')">Delete</button></div></div>';
  }
  $('sender-list').innerHTML=html;
}

window._selectClick=function(idx){
  if(senderStore[idx]){prefill(senderStore[idx].sender)}
};

window._deleteClick=function(idx){
  if(senderStore[idx]){quickDelete(senderStore[idx].sender,senderStore[idx].count)}
};

function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}

$('inp-search').addEventListener('input',function(){
  var q=this.value.toLowerCase();
  renderSenders(allSenders.filter(function(item){return item[0].toLowerCase().indexOf(q)!==-1}))
});

function prefill(sender){
  var match=sender.match(/<(.+?)>/);
  $('inp-sender').value=match?match[1]:sender;
  $('sec-main').scrollIntoView({behavior:'smooth'});
}

function quickDelete(sender,count){prefill(sender);openConfirmModal($('inp-sender').value,count)}

showSection('login');
</script>
</body>
</html>
"""

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production-please")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

IMAP_SERVERS = {
    "gmail.com": "imap.gmail.com",
    "googlemail.com": "imap.gmail.com",
    "outlook.com": "outlook.office365.com",
    "hotmail.com": "outlook.office365.com",
    "live.com": "outlook.office365.com",
    "msn.com": "outlook.office365.com",
    "yahoo.com": "imap.mail.yahoo.com",
    "ymail.com": "imap.mail.yahoo.com",
    "icloud.com": "imap.mail.me.com",
    "me.com": "imap.mail.me.com",
    "aol.com": "imap.aol.com",
    "protonmail.com": "imap.protonmail.ch",
    "proton.me": "imap.protonmail.ch",
    "zoho.com": "imap.zoho.com",
}

def get_imap_server(email_addr, custom_server=None):
    if custom_server:
        return custom_server
    domain = email_addr.split("@")[-1].lower()
    return IMAP_SERVERS.get(domain)

def connect(email_addr, password, custom_server=None):
    server = get_imap_server(email_addr, custom_server)
    if not server:
        raise ValueError("Unknown email provider. Enter IMAP server manually.")
    mail = imaplib.IMAP4_SSL(server, 993)
    mail.socket().settimeout(25)
    mail.login(email_addr, password)
    return mail

def decode_str(s):
    if s is None:
        return ""
    try:
        parts = decode_header(s)
        result = []
        for part, enc in parts:
            if isinstance(part, bytes):
                result.append(part.decode(enc or "utf-8", errors="replace"))
            else:
                result.append(str(part))
        return " ".join(result).strip()
    except Exception:
        return str(s)

def escape_imap_string(s):
    """Escape IMAP special characters."""
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    return s

def get_folders(mail):
    """Get all selectable IMAP folders."""
    status, folder_list = mail.list()
    folders = []
    if status != "OK":
        return ["INBOX"]
    for item in folder_list:
        if item is None:
            continue
        decoded = item.decode("utf-8", errors="replace")
        if "\\Noselect" in decoded or "\\NoSelect" in decoded:
            continue
        match = re.search(r' (?:"([^"]+)"|([^\s"][^\s]*))$', decoded)
        if match:
            name = match.group(1) or match.group(2)
            if name:
                folders.append(name)
    return folders if folders else ["INBOX"]

def select_folder(mail, folder):
    for attempt in ['"{}"'.format(folder), folder]:
        try:
            status, data = mail.select(attempt, readonly=False)
            if status == "OK":
                return True
        except Exception:
            pass
    return False

def select_folder_readonly(mail, folder):
    for attempt in ['"{}"'.format(folder), folder]:
        try:
            status, data = mail.select(attempt, readonly=True)
            if status == "OK":
                return True
        except Exception:
            pass
    return False

def search_from(mail, sender_query):
    """Search for emails from a sender."""
    all_ids = set()
    escaped = escape_imap_string(sender_query)
    queries = ['FROM "{}"'.format(escaped)]
    if " " not in sender_query and "\\" not in sender_query:
        queries.append('FROM {}'.format(escaped))
    for q in queries:
        try:
            status, data = mail.search(None, q)
            if status == "OK" and data and data[0]:
                for uid in data[0].split():
                    all_ids.add(uid)
        except Exception:
            continue
    return list(all_ids)

SKIP_FOLDER_KEYWORDS = ["trash", "deleted", "junk", "spam", "drafts", "sent", "archive", "all mail", "important", "starred", "bin", "[gmail]", "outbox", "chat"]

def should_skip_folder(name):
    lower = name.lower()
    return any(kw in lower for kw in SKIP_FOLDER_KEYWORDS)

def fetch_senders_from_folder(mail, folder, max_emails=2000):
    """Fetch senders from a folder."""
    sender_counts = {}
    if not select_folder_readonly(mail, folder):
        return sender_counts
    status, data = mail.search(None, "ALL")
    if status != "OK" or not data or not data[0]:
        return sender_counts
    ids = data[0].split()
    if not ids:
        return sender_counts
    ids = ids[-max_emails:]
    for i in range(0, len(ids), 1000):
        chunk_ids = ids[i:i+1000]
        id_set = b",".join(chunk_ids).decode()
        try:
            status, msg_data = mail.fetch(id_set, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
            if status != "OK" or not msg_data:
                continue
            for chunk in msg_data:
                if isinstance(chunk, tuple) and len(chunk) >= 2:
                    try:
                        msg = email.message_from_bytes(chunk[1])
                        sender = decode_str(msg.get("From", "")).strip()
                        if sender:
                            sender_counts[sender] = sender_counts.get(sender, 0) + 1
                    except Exception:
                        continue
        except Exception:
            continue
    return sender_counts

@app.route("/")
def index():
    return HTML_PAGE

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email_addr = data.get("email", "").strip()
    password = data.get("password", "").strip()
    custom_imap = data.get("imap_server", "").strip() or None

    if not email_addr or not password:
        return jsonify({"ok": False, "error": "Email and password required."}), 400
    
    if "@" not in email_addr or "." not in email_addr.split("@")[-1]:
        return jsonify({"ok": False, "error": "Invalid email format."}), 400

    try:
        mail = connect(email_addr, password, custom_imap)
        try:
            mail.logout()
        except Exception:
            pass
        session.permanent = True
        session["email"] = email_addr
        session["password"] = password
        session["imap_server"] = custom_imap
        return jsonify({"ok": True})
    except imaplib.IMAP4.error:
        return jsonify({"ok": False, "error": "Login failed. Check email/password."}), 401
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/senders", methods=["GET"])
def list_senders():
    if "email" not in session:
        return jsonify({"ok": False, "error": "Not logged in."}), 401

    try:
        mail = connect(session["email"], session["password"], session.get("imap_server"))
        sender_counts = {}
        folders = get_folders(mail)

        priority = [f for f in folders if f.upper() == "INBOX"]
        others = [f for f in folders if f.upper() != "INBOX" and not should_skip_folder(f)]
        scan_order = priority + others

        for folder in scan_order[:20]:
            try:
                counts = fetch_senders_from_folder(mail, folder, max_emails=2000)
                for sender, count in counts.items():
                    sender_counts[sender] = sender_counts.get(sender, 0) + count
            except Exception:
                continue

        try:
            mail.logout()
        except Exception:
            pass

        sorted_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)
        return jsonify({"ok": True, "senders": sorted_senders[:100]})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/preview", methods=["POST"])
def preview():
    if "email" not in session:
        return jsonify({"ok": False, "error": "Not logged in."}), 401

    sender_query = request.json.get("sender", "").strip()
    if not sender_query:
        return jsonify({"ok": False, "error": "Enter a sender."}), 400

    try:
        mail = connect(session["email"], session["password"], session.get("imap_server"))
        folders = get_folders(mail)
        folders = folders[:20]
        total = 0

        for folder in folders:
            try:
                if not select_folder_readonly(mail, folder):
                    continue
                ids = search_from(mail, sender_query)
                total += len(ids)
            except Exception:
                continue

        try:
            mail.logout()
        except Exception:
            pass
        return jsonify({"ok": True, "count": total})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/delete", methods=["POST"])
def delete():
    if "email" not in session:
        return jsonify({"ok": False, "error": "Not logged in."}), 401

    sender_query = request.json.get("sender", "").strip()
    if not sender_query:
        return jsonify({"ok": False, "error": "Enter a sender."}), 400

    try:
        mail = connect(session["email"], session["password"], session.get("imap_server"))
        folders = get_folders(mail)
        total_deleted = 0

        for folder in folders:
            try:
                if not select_folder(mail, folder):
                    continue
                ids = search_from(mail, sender_query)
                if not ids:
                    continue
                id_set = b",".join(ids).decode()
                mail.store(id_set, "+FLAGS", "\\Deleted")
                mail.expunge()
                total_deleted += len(ids)
            except Exception:
                continue

        try:
            mail.logout()
        except Exception:
            pass
        return jsonify({"ok": True, "deleted": total_deleted})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

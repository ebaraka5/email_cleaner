from flask import Flask, request, jsonify, session
import imaplib, email, os, re
from email.header import decode_header
from datetime import timedelta

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>MailSweep</title><link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;800" rel="stylesheet"><style>*{box-sizing:border-box;margin:0;padding:0}:root{--bg:#0a0a0f;--surface:#13131a;--border:#252535;--accent:#e8ff5a;--danger:#ff4444;--success:#4aff91;--text:#e8e8f0;--muted:#6b6b8a}body{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:2rem 1rem}.card{width:100%;max-width:700px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:2rem;margin-bottom:1.5rem}h2{font-size:0.75rem;font-family:'DM Mono',monospace;color:var(--muted);margin-bottom:1rem;text-transform:uppercase}label{display:block;font-family:'DM Mono',monospace;font-size:0.72rem;color:var(--muted);margin-top:1rem;margin-bottom:0.4rem}input{width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);font-family:'DM Mono',monospace;padding:0.7rem;border-radius:8px;outline:none}input:focus{border-color:var(--accent)}button{font-family:'Syne',sans-serif;border:none;border-radius:8px;cursor:pointer;padding:0.7rem 1.4rem;transition:all 0.18s}.btn-primary{background:var(--accent);color:#0a0a0f;width:100%;margin-top:1.25rem;font-weight:600}.btn-primary:hover{background:#f5ff80}.btn-ghost{background:0;color:var(--muted);border:1px solid var(--border);font-size:0.78rem}.btn-ghost:hover{color:var(--text)}.btn-danger{background:0;color:var(--danger);border:1px solid var(--danger);padding:0.5rem 1rem;font-size:0.8rem}.status{font-family:'DM Mono',monospace;font-size:0.78rem;padding:0.6rem 0.9rem;margin-top:0.9rem;display:none}.status.info{background:rgba(232,255,90,0.08);color:var(--accent);display:block}.status.error{background:rgba(255,68,68,0.08);color:var(--danger);display:block}.status.success{background:rgba(74,255,145,0.08);color:var(--success);display:block}.who{font-family:'DM Mono',monospace;font-size:0.78rem;color:var(--muted);display:flex;align-items:center;gap:0.6rem;margin-bottom:1.25rem}.who .dot{width:7px;height:7px;background:var(--success);border-radius:50%;box-shadow:0 0 6px var(--success)}.sender-list{max-height:380px;overflow-y:auto}.sender-item{display:flex;justify-content:space-between;padding:0.65rem 0;border-bottom:1px solid var(--border)}.sender-info{flex:1;min-width:0}.sender-name{font-family:'DM Mono',monospace;font-size:0.82rem;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.sender-count{font-family:'DM Mono',monospace;font-size:0.7rem;color:var(--muted)}.sender-actions{display:flex;gap:0.5rem}.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:100;opacity:0;pointer-events:none;transition:opacity 0.18s}.modal-overlay.open{opacity:1;pointer-events:all}.modal{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:2rem;max-width:420px;width:90%}.modal h3{font-size:1.1rem;margin-bottom:0.5rem}.modal p{font-family:'DM Mono',monospace;font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem}.modal-actions{display:flex;gap:0.75rem;justify-content:flex-end}.spinner{display:inline-block;width:14px;height:14px;border:2px solid rgba(0,0,0,0.2);border-top-color:#0a0a0f;border-radius:50%;animation:spin 0.7s linear infinite;margin-right:6px}@keyframes spin{to{transform:rotate(360deg)}}[data-section]{display:none}[data-section].active{display:block}.empty{text-align:center;padding:2rem;font-family:'DM Mono',monospace;font-size:0.8rem;color:var(--muted)}</style></head><body><div class="card"><div style="font-size:1.8rem;font-weight:800;margin-bottom:2rem">Mail<span style="color:var(--accent)">Sweep</span></div><div data-section="login" id="login"><h2>Connect Email</h2><label>Email</label><input type="email" id="email" placeholder="you@example.com"><label>Password</label><input type="password" id="pass" placeholder="••••••••••"><label>IMAP Server (optional)</label><input type="text" id="imap"><button class="btn-primary" id="btn-login">Connect</button><div class="status" id="login-status"></div></div><div data-section="main" id="main"><div class="who"><span class="dot"></span><span id="who">connected</span><button class="btn-ghost" id="btn-logout">logout</button></div><h2>Delete by Sender</h2><label>Sender Email</label><input type="text" id="sender"><button class="btn-primary" id="btn-preview">Preview</button><div class="status" id="preview-status"></div><div id="confirm" style="display:none;margin-top:1rem"><button class="btn-danger" style="width:100%;padding:0.8rem" id="btn-delete">Delete All</button></div><div class="status" id="delete-status"></div></div><div data-section="senders" id="senders"><h2>Top Senders</h2><button class="btn-primary" id="btn-scan">Scan Mailbox</button><div style="margin-top:1rem;display:none" id="search-wrap"><input type="text" id="search" placeholder="Filter..."></div><div class="sender-list" id="list"><div class="empty">Click Scan.</div></div><div class="status" id="scan-status"></div></div></div><div class="modal-overlay" id="modal"><div class="modal"><h3>Confirm Delete?</h3><p>Delete <strong id="m-count">0</strong> emails from <strong id="m-sender"></strong>. Cannot undo.</p><div class="modal-actions"><button class="btn-ghost" id="modal-cancel">Cancel</button><button class="btn-danger" id="modal-ok">Yes, Delete</button></div></div></div><script>
var $=id=>document.getElementById(id);
var show=id=>$(id).style.display='';
var hide=id=>$(id).style.display='none';
var setStatus=(id,type,msg)=>{var e=$(id);e.className='status '+type;e.textContent=msg};
var clearStatus=id=>{var e=$(id);e.className='status';e.textContent=''};
var showSection=name=>{['login','main','senders'].forEach(s=>{var e=$('sec-'+s.replace('-',''));e.style.display=s===name?'block':'none'})};
var api=async(path,body)=>{var opts={method:body?'POST':'GET',headers:{'Content-Type':'application/json'}};if(body)opts.body=JSON.stringify(body);var r=await fetch(path,opts);return r.json()};

$('btn-login').addEventListener('click',async function(){
  this.disabled=true;
  this.innerHTML='<span class="spinner"></span> Connecting...';
  clearStatus('login-status');
  var res=await api('/api/login',{email:$('email').value,password:$('pass').value,imap_server:$('imap').value});
  if(res.ok){$('who').textContent=$('email').value;$('login').style.display='none';$('main').style.display='block';$('senders').style.display='block'}
  else{setStatus('login-status','error','✗ '+res.error)}
  this.disabled=false;
  this.textContent='Connect';
});

$('btn-logout').addEventListener('click',async function(){
  await api('/api/logout',{});
  $('login').style.display='block';
  $('main').style.display='none';
  $('senders').style.display='none';
  $('pass').value='';
});

$('btn-preview').addEventListener('click',async function(){
  var sender=$('sender').value.trim();
  if(!sender){setStatus('preview-status','error','Enter a sender.');return}
  clearStatus('preview-status');hide('confirm');
  this.innerHTML='<span class="spinner"></span>';this.disabled=true;
  var res=await api('/api/preview',{sender:sender});
  this.textContent='Preview';this.disabled=false;
  if(res.ok){
    if(res.count===0){setStatus('preview-status','info','No emails found.')}
    else{setStatus('preview-status','info','Found '+res.count+' email(s).');show('confirm');window._count=res.count}
  }else{setStatus('preview-status','error','✗ '+res.error)}
});

var _sender=null;
$('btn-delete').addEventListener('click',function(){_sender=$('sender').value.trim();$('m-count').textContent=window._count;$('m-sender').textContent=_sender;$('modal').classList.add('open')});
$('modal-cancel').addEventListener('click',()=>$('modal').classList.remove('open'));
$('modal-ok').addEventListener('click',async function(){
  $('modal').classList.remove('open');
  $('btn-delete').disabled=true;
  $('btn-delete').innerHTML='<span class="spinner" style="border-top-color:var(--danger)"></span> Deleting...';
  clearStatus('delete-status');
  var res=await api('/api/delete',{sender:_sender});
  $('btn-delete').disabled=false;
  $('btn-delete').textContent='Delete All';
  if(res.ok){
    setStatus('delete-status','success','✓ Deleted '+res.deleted);hide('confirm');clearStatus('preview-status');$('sender').value='';
    if($('list').dataset.loaded)loadSenders();
  }else{setStatus('delete-status','error','✗ '+res.error)}
});

var senders=[];
$('btn-scan').addEventListener('click',loadSenders);

async function loadSenders(){
  $('btn-scan').innerHTML='<span class="spinner"></span> Scanning...';$('btn-scan').disabled=true;
  $('list').innerHTML='<div class="empty">Scanning...</div>';
  clearStatus('scan-status');
  var res=await api('/api/senders');
  $('btn-scan').textContent='Rescan';$('btn-scan').disabled=false;
  if(res.ok){senders=res.senders;$('list').dataset.loaded='1';$('search-wrap').style.display='';renderSenders(senders)}
  else{setStatus('scan-status','error','✗ '+res.error)}
}

var store={};
function renderSenders(list){
  if(list.length===0){$('list').innerHTML='<div class="empty">No senders.</div>';return}
  store={};var html='';
  for(var i=0;i<list.length;i++){
    var sender=list[i][0],count=list[i][1],idx='s'+i;
    store[idx]={sender:sender,count:count};
    html+='<div class="sender-item"><div class="sender-info"><div class="sender-name" title="'+esc(sender)+'">'+esc(sender)+'</div><div class="sender-count">'+count+' email'+(count!==1?'s':'')+' </div></div><div class="sender-actions"><button class="btn-ghost sel" data-idx="'+idx+'">Select</button><button class="btn-danger del" data-idx="'+idx+'">Delete</button></div></div>';
  }
  $('list').innerHTML=html;
  document.querySelectorAll('.sel').forEach(b=>b.addEventListener('click',function(){var d=store[this.getAttribute('data-idx')];if(d)prefill(d.sender)}));
  document.querySelectorAll('.del').forEach(b=>b.addEventListener('click',function(){var d=store[this.getAttribute('data-idx')];if(d)quickDelete(d.sender,d.count)}));
}

function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}

$('search').addEventListener('input',function(){var q=this.value.toLowerCase();renderSenders(senders.filter(s=>s[0].toLowerCase().indexOf(q)!==-1))});

function prefill(sender){$('sender').value=sender;$('main').scrollIntoView({behavior:'smooth'})}
function quickDelete(sender,count){prefill(sender);_sender=sender;$('m-count').textContent=count;$('m-sender').textContent=sender;$('modal').classList.add('open')}

$('login').style.display='block';
</script></body></html>"""

app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY","change-this")
app.config["PERMANENT_SESSION_LIFETIME"]=timedelta(hours=2)
app.config["SESSION_COOKIE_SAMESITE"]="Lax"

SERVERS={"gmail.com":"imap.gmail.com","googlemail.com":"imap.gmail.com","outlook.com":"outlook.office365.com","hotmail.com":"outlook.office365.com","live.com":"outlook.office365.com","msn.com":"outlook.office365.com","yahoo.com":"imap.mail.yahoo.com","ymail.com":"imap.mail.yahoo.com","icloud.com":"imap.mail.me.com","me.com":"imap.mail.me.com","aol.com":"imap.aol.com","protonmail.com":"imap.protonmail.ch","proton.me":"imap.protonmail.ch","zoho.com":"imap.zoho.com"}

def get_server(email,custom=None):
    if custom:return custom
    domain=email.split("@")[-1].lower()
    return SERVERS.get(domain)

def connect(email,password,custom=None):
    server=get_server(email,custom)
    if not server:raise ValueError("Unknown provider")
    mail=imaplib.IMAP4_SSL(server,993)
    mail.socket().settimeout(25)
    mail.login(email,password)
    return mail

def decode_str(s):
    if not s:return ""
    try:
        parts=decode_header(s)
        result=[]
        for part,enc in parts:
            if isinstance(part,bytes):result.append(part.decode(enc or "utf-8",errors="replace"))
            else:result.append(str(part))
        return " ".join(result).strip()
    except:return str(s)

def escape_imap(s):
    s=s.replace("\\","\\\\")
    s=s.replace('"','\\"')
    return s

def get_folders(mail):
    status,folder_list=mail.list()
    folders=[]
    if status!="OK":return ["INBOX"]
    for item in folder_list:
        if not item:continue
        decoded=item.decode("utf-8",errors="replace")
        if "\\Noselect" in decoded:continue
        match=re.search(r' (?:"([^"]+)"|([^\s"][^\s]*))$',decoded)
        if match:
            name=match.group(1) or match.group(2)
            if name:folders.append(name)
    return folders if folders else ["INBOX"]

def select_folder_ro(mail,folder):
    for attempt in ['"{}"'.format(folder),folder]:
        try:
            status,data=mail.select(attempt,readonly=True)
            if status=="OK":return True
        except:pass
    return False

def select_folder(mail,folder):
    for attempt in ['"{}"'.format(folder),folder]:
        try:
            status,data=mail.select(attempt,readonly=False)
            if status=="OK":return True
        except:pass
    return False

def search_from(mail,sender):
    all_ids=set()
    escaped=escape_imap(sender)
    queries=['FROM "{}"'.format(escaped)]
    if " " not in sender and "\\" not in sender:queries.append('FROM {}'.format(escaped))
    for q in queries:
        try:
            status,data=mail.search(None,q)
            if status=="OK" and data and data[0]:
                for uid in data[0].split():all_ids.add(uid)
        except:pass
    return list(all_ids)

SKIP=["trash","deleted","junk","spam","drafts","sent","archive","all mail","[gmail]","outbox"]
def skip_folder(name):return any(k in name.lower() for k in SKIP)

def fetch_from_folder(mail,folder,max_emails=2000):
    counts={}
    if not select_folder_ro(mail,folder):return counts
    status,data=mail.search(None,"ALL")
    if status!="OK" or not data or not data[0]:return counts
    ids=data[0].split()
    if not ids:return counts
    ids=ids[-max_emails:]
    for i in range(0,len(ids),1000):
        chunk_ids=ids[i:i+1000]
        id_set=b",".join(chunk_ids).decode()
        try:
            status,msg_data=mail.fetch(id_set,"(BODY.PEEK[HEADER.FIELDS (FROM)])")
            if status!="OK" or not msg_data:continue
            for chunk in msg_data:
                if isinstance(chunk,tuple) and len(chunk)>=2:
                    try:
                        msg=email.message_from_bytes(chunk[1])
                        sender=decode_str(msg.get("From","")).strip()
                        if sender:counts[sender]=counts.get(sender,0)+1
                    except:pass
        except:pass
    return counts

@app.route("/")
def index():return HTML

@app.route("/api/login",methods=["POST"])
def login():
    data=request.json
    email_addr=data.get("email","").strip()
    password=data.get("password","").strip()
    custom_imap=data.get("imap_server","").strip() or None
    if not email_addr or not password:return jsonify({"ok":False,"error":"Email and password required."}),400
    if "@" not in email_addr:return jsonify({"ok":False,"error":"Invalid email."}),400
    try:
        mail=connect(email_addr,password,custom_imap)
        try:mail.logout()
        except:pass
        session.permanent=True
        session["email"]=email_addr
        session["password"]=password
        session["imap_server"]=custom_imap
        return jsonify({"ok":True})
    except imaplib.IMAP4.error:return jsonify({"ok":False,"error":"Login failed."}),401
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),500

@app.route("/api/logout",methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok":True})

@app.route("/api/senders",methods=["GET"])
def list_senders():
    if "email" not in session:return jsonify({"ok":False,"error":"Not logged in."}),401
    try:
        mail=connect(session["email"],session["password"],session.get("imap_server"))
        counts={}
        folders=get_folders(mail)
        priority=[f for f in folders if f.upper()=="INBOX"]
        others=[f for f in folders if f.upper()!="INBOX" and not skip_folder(f)]
        scan_folders=priority+others[:20]
        for folder in scan_folders:
            try:
                c=fetch_from_folder(mail,folder,2000)
                for sender,count in c.items():counts[sender]=counts.get(sender,0)+count
            except:pass
        try:mail.logout()
        except:pass
        sorted_senders=sorted(counts.items(),key=lambda x:x[1],reverse=True)
        return jsonify({"ok":True,"senders":sorted_senders[:100]})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),500

@app.route("/api/preview",methods=["POST"])
def preview():
    if "email" not in session:return jsonify({"ok":False,"error":"Not logged in."}),401
    sender=request.json.get("sender","").strip()
    if not sender:return jsonify({"ok":False,"error":"Enter a sender."}),400
    try:
        mail=connect(session["email"],session["password"],session.get("imap_server"))
        folders=get_folders(mail)
        total=0
        for folder in folders[:20]:
            try:
                if select_folder_ro(mail,folder):total+=len(search_from(mail,sender))
            except:pass
        try:mail.logout()
        except:pass
        return jsonify({"ok":True,"count":total})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),500

@app.route("/api/delete",methods=["POST"])
def delete():
    if "email" not in session:return jsonify({"ok":False,"error":"Not logged in."}),401
    sender=request.json.get("sender","").strip()
    if not sender:return jsonify({"ok":False,"error":"Enter a sender."}),400
    try:
        mail=connect(session["email"],session["password"],session.get("imap_server"))
        folders=get_folders(mail)
        total=0
        for folder in folders:
            try:
                if select_folder(mail,folder):
                    ids=search_from(mail,sender)
                    if ids:
                        id_set=b",".join(ids).decode()
                        mail.store(id_set,"+FLAGS","\\Deleted")
                        mail.expunge()
                        total+=len(ids)
            except:pass
        try:mail.logout()
        except:pass
        return jsonify({"ok":True,"deleted":total})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),500

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)

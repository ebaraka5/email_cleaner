from flask import Flask, request, jsonify, session, render_template
import imaplib
import email
from email.header import decode_header
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production-please")

# ── IMAP server presets ───────────────────────────────────────────────────────
IMAP_SERVERS = {
    "gmail.com":        "imap.gmail.com",
    "googlemail.com":   "imap.gmail.com",
    "outlook.com":      "outlook.office365.com",
    "hotmail.com":      "outlook.office365.com",
    "live.com":         "outlook.office365.com",
    "msn.com":          "outlook.office365.com",
    "yahoo.com":        "imap.mail.yahoo.com",
    "ymail.com":        "imap.mail.yahoo.com",
    "icloud.com":       "imap.mail.me.com",
    "me.com":           "imap.mail.me.com",
    "aol.com":          "imap.aol.com",
    "protonmail.com":   "imap.protonmail.ch",
    "proton.me":        "imap.protonmail.ch",
    "zoho.com":         "imap.zoho.com",
}

def get_imap_server(email_addr, custom_server=None):
    if custom_server:
        return custom_server
    domain = email_addr.split("@")[-1].lower()
    return IMAP_SERVERS.get(domain)

def connect(email_addr, password, custom_server=None):
    server = get_imap_server(email_addr, custom_server)
    if not server:
        raise ValueError(f"Unknown email provider. Please enter your IMAP server manually.")
    mail = imaplib.IMAP4_SSL(server, 993)
    mail.login(email_addr, password)
    return mail

def decode_str(s):
    if s is None:
        return ""
    parts = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(part)
    return " ".join(result)

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email_addr   = data.get("email", "").strip()
    password     = data.get("password", "").strip()
    custom_imap  = data.get("imap_server", "").strip() or None

    if not email_addr or not password:
        return jsonify({"ok": False, "error": "Email and password are required."}), 400

    try:
        mail = connect(email_addr, password, custom_imap)
        mail.logout()
        # Store credentials in server-side session (never sent back to browser)
        session["email"]       = email_addr
        session["password"]    = password
        session["imap_server"] = custom_imap
        return jsonify({"ok": True})
    except imaplib.IMAP4.error as e:
        return jsonify({"ok": False, "error": "Login failed — check your email/password or App Password."}), 401
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/senders", methods=["GET"])
def list_senders():
    """Return the top senders by email count across all folders."""
    if "email" not in session:
        return jsonify({"ok": False, "error": "Not logged in."}), 401

    try:
        mail = connect(session["email"], session["password"], session.get("imap_server"))

        # Gather all folder names
        status, folders = mail.list()
        folder_names = []
        for f in folders:
            parts = f.decode().split(' "." ')
            if len(parts) >= 2:
                folder_names.append(parts[-1].strip().strip('"'))

        sender_counts = {}

        for folder in folder_names:
            try:
                status, _ = mail.select(f'"{folder}"', readonly=True)
                if status != "OK":
                    continue
                status, data = mail.search(None, "ALL")
                if status != "OK" or not data[0]:
                    continue
                ids = data[0].split()
                # Fetch only headers (fast)
                for uid in ids:
                    status, msg_data = mail.fetch(uid, "(BODY[HEADER.FIELDS (FROM)])")
                    if status != "OK":
                        continue
                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)
                    sender = decode_str(msg.get("From", "")).strip()
                    if sender:
                        sender_counts[sender] = sender_counts.get(sender, 0) + 1
            except Exception:
                continue

        mail.logout()

        # Sort by count descending
        sorted_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)
        return jsonify({"ok": True, "senders": sorted_senders[:100]})  # top 100

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/preview", methods=["POST"])
def preview():
    """Count how many emails would be deleted for a given sender."""
    if "email" not in session:
        return jsonify({"ok": False, "error": "Not logged in."}), 401

    sender_query = request.json.get("sender", "").strip()
    if not sender_query:
        return jsonify({"ok": False, "error": "No sender specified."}), 400

    try:
        mail = connect(session["email"], session["password"], session.get("imap_server"))
        status, folders = mail.list()
        folder_names = []
        for f in folders:
            parts = f.decode().split(' "." ')
            if len(parts) >= 2:
                folder_names.append(parts[-1].strip().strip('"'))

        total = 0
        for folder in folder_names:
            try:
                mail.select(f'"{folder}"', readonly=True)
                status, data = mail.search(None, f'FROM "{sender_query}"')
                if status == "OK" and data[0]:
                    total += len(data[0].split())
            except Exception:
                continue

        mail.logout()
        return jsonify({"ok": True, "count": total})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/delete", methods=["POST"])
def delete():
    """Delete all emails from a given sender across all folders."""
    if "email" not in session:
        return jsonify({"ok": False, "error": "Not logged in."}), 401

    sender_query = request.json.get("sender", "").strip()
    if not sender_query:
        return jsonify({"ok": False, "error": "No sender specified."}), 400

    try:
        mail = connect(session["email"], session["password"], session.get("imap_server"))
        status, folders = mail.list()
        folder_names = []
        for f in folders:
            parts = f.decode().split(' "." ')
            if len(parts) >= 2:
                folder_names.append(parts[-1].strip().strip('"'))

        total_deleted = 0

        for folder in folder_names:
            try:
                mail.select(f'"{folder}"')
                status, data = mail.search(None, f'FROM "{sender_query}"')
                if status != "OK" or not data[0]:
                    continue
                ids = data[0].split()
                for uid in ids:
                    mail.store(uid, "+FLAGS", "\\Deleted")
                mail.expunge()
                total_deleted += len(ids)
            except Exception:
                continue

        mail.logout()
        return jsonify({"ok": True, "deleted": total_deleted})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# MailSweep — Email Cleanup Tool

A self-hosted web app to delete all emails from any sender across any IMAP email account (Gmail, Outlook, Yahoo, and more).

---

## Features
- Works with any IMAP-compatible email provider
- Auto-detects IMAP server for Gmail, Outlook, Yahoo, iCloud, AOL, ProtonMail, Zoho
- Scan your mailbox to see top senders
- Preview how many emails will be deleted before confirming
- Deletes across ALL folders, not just Inbox
- Credentials are never stored — session only

---

## Deploying to Railway (Free) — Recommended

1. **Create a GitHub account** at github.com if you don't have one.

2. **Upload these files to a new GitHub repository:**
   - app.py
   - requirements.txt
   - Procfile
   - templates/index.html

3. **Create a Railway account** at railway.app (free tier available).

4. Click **"New Project" → "Deploy from GitHub repo"** and select your repo.

5. Railway will auto-detect Python and deploy it.

6. Go to your project → **Settings → Environment Variables** and add:
   ```
   SECRET_KEY = any-long-random-string-you-make-up
   ```

7. Your app will be live at a URL like `https://your-app.up.railway.app`

---

## Deploying to Render (Free Alternative)

1. Upload files to GitHub (same as above).
2. Create account at render.com.
3. New → Web Service → connect your GitHub repo.
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add environment variable: `SECRET_KEY = your-secret-here`
6. Deploy!

---

## How to use Gmail / Yahoo / Outlook

These providers block regular password logins for IMAP. You need an **App Password**:

- **Gmail:** myaccount.google.com → Security → 2-Step Verification → App passwords
- **Yahoo:** account.yahoo.com → Security → Generate app password
- **Outlook/Hotmail:** account.microsoft.com → Security → Advanced security → App passwords

Leave the "IMAP server" field blank — it's auto-detected.

---

## Security Notes

- This app does NOT store your password anywhere. It's held in a server-side session only.
- For extra security, set a strong SECRET_KEY environment variable.
- This is intended for personal use only. Do not share the URL publicly.

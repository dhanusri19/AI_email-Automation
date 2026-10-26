# Intern Review Chatbot (Flask + React + MySQL)

Rule-based chatbot (no LLM). HR uploads Excel -> validate -> MySQL -> chat/voice to manage reviews,
emails (always with HR confirmation), attendance, feedback, follow-ups, reports.

## 1. Database
Install MySQL, then:  `mysql -u root -p < backend/schema.sql`

## 2. Backend (Anaconda Prompt)
```
conda create -n internbot python=3.11 -y
conda activate internbot
cd backend
pip install -r requirements.txt
```
Edit `backend/.env` (MySQL password, Gmail App Password; keep TEST_EMAIL_OVERRIDE = your own email while testing).
```
python app.py        # http://localhost:5000/api/health
```

## 3. Frontend (needs Node.js)
```
cd frontend
npm install
npm start            # http://localhost:3000  (use Chrome/Edge for the mic)
```

## 4. Test flow
1. Upload tab: `backend/sample_data/interns_broken.xlsx` -> errors listed row by row; then `interns_sample.xlsx` -> 100 saved.
2. Chat: "show reviews today", "show Intern 005", "schedule Intern 001 on 2026-11-02 at 10:30" -> "yes".
3. A conflicting slot is rejected (same mentor/link/time). Nothing changes without "yes".
4. "send review emails" -> "yes" (goes to TEST_EMAIL_OVERRIDE). See Emails tab logs.
5. Dashboard: mark Done/Missed, flag overdue, download Excel/PDF reports.
6. Feedback tab: save feedback; `needs_followup` shows under Suggested Follow-ups -> request -> confirm.

## 5. Broadcast message
HR can send an announcement email to all interns directly via chat or the Emails tab:
- Type in chat:
  ```
  announce: Reviews moved | Hi {name}, tomorrow's review is postponed to Friday 3 PM. Regards, HR
  ```
- Bot asks for confirmation: `"Send this to N interns? Subject: [Notification] ... Message: ... Say yes or no."`
- Reply `"yes"` to send, or `"no"` to cancel. Nothing is sent before `"yes"`.


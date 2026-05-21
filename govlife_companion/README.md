# GovLife Companion

GovLife Companion is a personal life management app for government employees and their families. It helps users manage salary, monthly budget, loans, leave, PF, insurance, health, education, transfers, trips, retirement, reminders, reports, and AI planning.

The app is built with **Streamlit**, **Python**, **SQLite**, **Plotly**, and the **OpenAI API**.

## Main Features

- Login and registration with hashed passwords
- User and Admin roles
- Dashboard with cards, charts, and smart alerts
- Salary Budget Planner with auto budget recommendation
- Loan and EMI Tracker
- CL and EL Leave Tracker
- PF Tracker with retirement projection
- Insurance Tracker with renewal reminders
- Health Tracker
- Children Education Planner
- Transfer Life Manager
- Trip Planner
- Retirement and Pension Planner
- Reminders Center
- AI Assistant with voice input and multi-language support
- Monthly PDF report
- CSV reports
- Family Profiles
- Notifications page
- Backup and Restore
- Mobile-friendly UI

## Supported Languages

- English
- Hindi
- Urdu
- Telugu
- Roman Hindi

Users can select language before login and also change it from the sidebar after login.

## Tech Stack

- Frontend: Streamlit
- Backend: Python
- Database: SQLite
- Charts: Plotly
- AI: OpenAI API
- PDF: pypdf and reportlab
- Voice input: streamlit-mic-recorder
- Authentication: bcrypt password hashing

## Folder Structure

```text
govlife_companion/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── assets/
│   └── style.css
├── database/
│   ├── db.py
│   └── schema.sql
├── modules/
│   ├── ai_assistant.py
│   ├── auth.py
│   ├── backup_restore.py
│   ├── budget.py
│   ├── dashboard.py
│   ├── education.py
│   ├── family_profiles.py
│   ├── health.py
│   ├── insurance_tracker.py
│   ├── leave_tracker.py
│   ├── loans.py
│   ├── notifications.py
│   ├── pf_tracker.py
│   ├── reminders.py
│   ├── reports.py
│   ├── retirement.py
│   ├── smart_alerts.py
│   ├── transfer.py
│   └── trips.py
├── uploads/
│   └── .gitkeep
└── utils/
    ├── calculations.py
    ├── helpers.py
    ├── monthly_report.py
    ├── pdf_reader.py
    ├── recommendations.py
    ├── security.py
    ├── smart_alerts.py
    └── translations.py
```

## Environment Setup

This project uses a Python virtual environment. A virtual environment keeps this app's packages separate from other Python projects on your computer.

### What We Created

The project environment was created like this:

```powershell
python -m venv .venv
```

This creates a folder named `.venv` inside the project.

The `.venv` folder should **not** be pushed to GitHub. It is already ignored in `.gitignore`.

## Setup in VS Code

Open the project folder in VS Code:

```powershell
cd C:\Users\shaik\Documents\employe\govlife_companion
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Install packages:

```powershell
pip install -r requirements.txt
```

If you are using macOS or Linux, activate the environment like this:

```bash
source .venv/bin/activate
```

Then install packages:

```bash
pip install -r requirements.txt
```

## Environment File

Create a `.env` file in the `govlife_companion` folder.

You can copy `.env.example` and rename it to `.env`.

```env
OPENAI_API_KEY=your_openai_api_key_here

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SENDER_EMAIL=your_email@gmail.com
RECEIVER_EMAIL=receiver_email@gmail.com
```

Important:

- Do not commit `.env` to GitHub.
- `.env` is already added to `.gitignore`.
- You can also enter the OpenAI API key inside the AI Assistant page.
- SMTP fields are optional. They are only needed for email notification sending.

## Run the App

Make sure your virtual environment is activated first:

```powershell
.venv\Scripts\activate
```

Then run:

```powershell
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## Full Run Steps From Fresh Download

Use these steps if someone downloads this project from GitHub:

```powershell
git clone your_repo_url_here
cd govlife_companion
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

After that, open:

```text
http://localhost:8501
```

Then add your OpenAI API key either in `.env` or inside the AI Assistant page.

## Demo Login

User account:

```text
Email: demo@govlife.in
Password: demo123
```

Admin account:

```text
Email: admin@govlife.in
Password: admin123
```

## How to Use

1. Select your language.
2. Login or create a new account.
3. Use the sidebar to open modules.
4. Add salary, expenses, loans, leave, PF, insurance, health, education, trips, and retirement details.
5. Open Dashboard to see summary cards and charts.
6. Open AI Assistant to ask questions or use voice input.
7. Open Reports to download CSV and monthly PDF report.
8. Use Backup & Restore to download a local database backup.

## AI Assistant

The AI Assistant can help with:

- Monthly budget planning
- EMI safety
- Leave messages
- PF growth explanation
- Insurance renewal checklist
- Retirement planning
- Family planning
- Health reminders
- Trip planning
- PDF summaries

The AI does not give legal, medical, pension, PF, or insurance guarantees. Always verify official rules with your department, PF portal, bank, or insurance company.

## GitHub Push Checklist

Before pushing:

```powershell
git status
```

Make sure these are not committed:

- `.env`
- `govlife.db`
- `.venv/`
- `__pycache__/`
- uploaded private files
- local backups

Then push:

```powershell
git add .
git commit -m "Add GovLife Companion app"
git push
```

## What Is Needed

To run this project, you need:

- Python 3.10 or newer
- VS Code or any code editor
- Internet connection for first package installation
- `requirements.txt` installed
- `.env` file for OpenAI API key
- OpenAI API key for AI Assistant, voice AI replies, and PDF summarizer
- Microphone permission in browser for voice input
- Optional Gmail app password or SMTP details for email notifications

Files that should be pushed to GitHub:

- `app.py`
- `requirements.txt`
- `.env.example`
- `README.md`
- `assets/`
- `database/`
- `modules/`
- `utils/`
- `uploads/.gitkeep`

Files that should not be pushed:

- `.env`
- `.venv/`
- `govlife.db`
- `__pycache__/`
- `backups/`
- private uploaded files

## Security Notes

- Passwords are hashed.
- API keys are not hardcoded.
- `.env` is ignored by Git.
- SQLite database is local.
- Backup files may contain private data, so do not upload them publicly.
- This app is for personal planning and tracking only.

## Future Ideas

- Cloud database support
- Real SMS or WhatsApp API integration
- Encrypted file locker
- Better admin analytics
- Mobile app packaging
- Department-wise pension/PF rule configuration

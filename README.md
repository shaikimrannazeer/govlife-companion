# GovLife Companion

GovLife Companion is a Streamlit app for government employees and their families. It helps manage salary, budget, loans, CL/EL leave, PF, insurance, health, children education, transfers, trips, retirement planning, reminders, reports, and AI assistance.

The full project code is inside:

```text
govlife_companion/
```

## Features

- Login and registration
- User and Admin roles
- Multi-language support
- Dashboard with charts and smart alerts
- Salary Budget Planner
- Loan and EMI Tracker
- CL and EL Leave Tracker
- PF Tracker
- Insurance Tracker
- Health Tracker
- Children Education Planner
- Transfer Life Manager
- Trip Planner
- Retirement Planner
- Reminders Center
- AI Assistant with voice input
- Monthly PDF report
- Backup and Restore

## Tech Stack

- Python
- Streamlit
- SQLite
- Plotly
- OpenAI API
- pypdf
- reportlab
- streamlit-mic-recorder

## Setup

Open terminal in the repository folder:

```powershell
cd govlife_companion
```

Create virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Environment File

Copy `.env.example` to `.env`:

```powershell
copy .env.example .env
```

Add your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Do not push `.env` to GitHub.

## Run

```powershell
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Demo Login

User:

```text
demo@govlife.in
demo123
```

Admin:

```text
admin@govlife.in
admin123
```

## Needed

- Python 3.10 or newer
- VS Code or any code editor
- Internet for installing packages
- OpenAI API key for AI features
- Microphone permission for voice input
- Optional SMTP details for email notifications

## Security

- `.env` is ignored
- `govlife.db` is ignored
- `.venv/` is ignored
- uploaded private files are ignored
- backups are ignored

For full details, see:

```text
govlife_companion/README.md
```


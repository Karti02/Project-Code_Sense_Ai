# CodeSense AI – Smart Workspace Assistant

An AI-powered developer productivity assistant that automatically tracks
coding activity, analyzes work habits, and predicts productivity using
Machine Learning. Built as a B.Tech AI/ML college project with Flask,
Scikit-learn, Pandas, and a modern Bootstrap 5 dashboard.

---

## ✨ Features

- **User system** — register, login, logout, profile
- **Live dashboard** — coding time, productivity score, keyboard/mouse
  activity, sessions, languages used, compile count, charts, auto-refreshing
  every 5 seconds
- **Activity monitor** — detects the active IDE/app (VS Code, PyCharm,
  Cursor, Notepad++, Terminal), session start/end, idle time
- **Project & language detection** — infers project + file + one of 16
  supported languages automatically
- **Screenshot automation** — PyAutoGUI captures a screenshot every N
  minutes (configurable/toggleable), saved under `screenshots/YYYY/MM/DD/`
- **Analytics (Pandas)** — daily/weekly/monthly summaries, most used
  language, most productive day, longest/average session, project usage
- **Charts (Chart.js)** — weekly coding hours, language distribution,
  productivity trend
- **Machine Learning** — RandomForestRegressor vs LinearRegression trained
  on your own activity data (auto-bootstrapped with synthetic rows if you
  don't have much history yet), predicts today/tomorrow/weekly productivity,
  shows R² accuracy + feature importance
- **Reports** — downloadable PDF reports (daily/weekly/monthly) via ReportLab
- **Settings** — screenshot on/off + interval, daily goal, dark/light mode,
  export/import data as JSON, reset analytics
- **Gamification** — daily coding streaks + achievement badges
- **Search & filter** — activity history searchable by app/project/file/
  language and filterable by date

Everything runs **100% locally** with **SQLite** — no paid APIs, no cloud
services.

---

## 🧱 Tech Stack

| Layer          | Tools |
|----------------|-------|
| Backend        | Python 3.11, Flask, Flask-Login, Flask-SQLAlchemy |
| Database       | SQLite |
| Machine Learning | scikit-learn, pandas, numpy |
| Automation     | PyAutoGUI, `keyboard`, `mouse`, psutil |
| Visualization  | Matplotlib (reports), Chart.js (dashboard) |
| Frontend       | HTML, CSS, Bootstrap 5, vanilla JavaScript |
| PDF reports    | ReportLab |

---

## 📁 Folder Structure

```
codesense-ai/
├── app/
│   ├── routes/          # Flask blueprints (auth, dashboard, activity, ml, reports, settings)
│   ├── models/          # SQLAlchemy models
│   ├── templates/       # Jinja2 templates
│   ├── static/          # css/, js/, images/
│   ├── services/        # activity_service, stats_service, export_service
│   ├── collectors/      # window/input/screenshot collectors, language detector
│   ├── ml/               # dataset_generator, train, predict
│   └── utils/            # helpers
├── database/
├── datasets/             # auto-generated ML training CSVs
├── screenshots/          # auto-captured screenshots (YYYY/MM/DD)
├── reports/               # generated PDF reports
├── instance/              # SQLite database file lives here
├── config.py
├── run.py
├── seed_demo_data.py       # optional: fills 3 weeks of realistic demo data
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note on OS-specific permissions:**
> - The `keyboard` / `mouse` libraries need administrator/root privileges
>   on some systems to install global hooks (Windows: run as Administrator;
>   Linux: run with `sudo` or add your user to the `input` group).
> - PyAutoGUI needs a graphical desktop session (it will not work over SSH
>   without a display) to take screenshots or read the mouse position.
> - If these permissions aren't available, the app still runs fine —
>   keyboard/mouse counts and screenshots will just report as zero/disabled
>   instead of crashing.

### 3. (Optional) Seed demo data for a quick presentation

```bash
python seed_demo_data.py
```

This creates a `demo` account (`demo` / `demo1234`) with 3 weeks of
realistic sample activity, so the dashboard and ML page have data to show
immediately.

### 4. Run the app

```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser, register an account (or
log in as `demo`), and start coding — the dashboard updates automatically.

---

## 🤖 How the Machine Learning works

1. **Dataset generation** (`app/ml/dataset_generator.py`) — builds a
   feature table from your `DailyStat` rows:
   `coding_time, keyboard_count, mouse_clicks, compile_count,
   project_switches, idle_time, languages_used, sessions` → target
   `productivity_score`. If you don't have much history yet, it tops the
   dataset up with synthetic-but-realistic rows so the model can still
   train (clearly a bootstrap, not a replacement for real data).
2. **Training** (`app/ml/train.py`) — trains a `RandomForestRegressor`
   and a `LinearRegression` baseline, compares them by R² on a held-out
   test split, and saves whichever performs better.
3. **Prediction** (`app/ml/predict.py`) — predicts today's score from
   today's stats so far, tomorrow's score from a 7-day rolling average,
   and a 7-point weekly trend.

No deep learning, no TensorFlow/PyTorch — kept intentionally simple and
explainable for a viva.

---

## 🎓 Notes for Viva / Presentation

- The **Feature Importance** panel on the ML page is a great talking
  point — it shows *which* habits the model thinks matter most for your
  productivity score.
- The **heuristic formula** in `app/utils/helpers.py`
  (`compute_heuristic_score`) is used to label data in real time and as a
  sanity baseline — it's simple enough to explain on a whiteboard: more
  coding time and compiles increase the score, more idle time and context
  switching decrease it.
- All screenshots, reports, and the SQLite database stay on your machine —
  nothing is uploaded anywhere.

---

## 🔐 Administrator Setup

CodeSense AI supports an `admin` role with access to a restricted
`/admin` dashboard (user management, aggregate usage stats). No admin
account or password is ever hard-coded in the source — you create the
first one yourself via the Flask CLI:

```bash
# Option A: pass the password via an environment variable
ADMIN_USERNAME=admin ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD='a-long-random-passphrase' \
    flask --app run.py create-admin

# Option B: omit ADMIN_PASSWORD and you'll be prompted securely
# (input is hidden and never written to shell history)
flask --app run.py create-admin --username admin --email admin@example.com
```

If `flask create-admin` isn't recognized (e.g. `Error: No such command`),
that means the `flask` CLI isn't discovering this project's app — usually
a wrong working directory or virtualenv. Use the equivalent standalone
script instead, run from the project root (same folder as `run.py`):

```bash
ADMIN_PASSWORD='a-long-random-passphrase' python create_admin.py --username admin --email admin@example.com
```

Requirements enforced by the command:
- The password must be at least 12 characters.
- Running it again on an existing username/email promotes that account
  to admin (set `ADMIN_RESET_PASSWORD=1` if you also want to reset the
  password at the same time).

Every route under `/admin` is protected server-side by an
`@admin_required` decorator (see `app/utils/decorators.py`), enforced
both per-view and via a blueprint-wide `before_request` guard, so the
check can't be bypassed even if a new admin route forgets to add it.
The "Admin" link in the sidebar is only a convenience — it's hidden for
non-admins, but the real access control is the server-side check.

---

## ⚠️ Disclaimer

This project tracks **your own** keyboard/mouse activity and application
usage on **your own** machine for personal productivity insight. It is not
intended for monitoring other people without their knowledge or consent.
#   P r o j e c t - C o d e _ S e n s e _ A i  
 
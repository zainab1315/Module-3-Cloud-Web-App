# Cloud Notes &#9729; | Module 3 - Cloud Services &amp; Web App Deployment

A small, beginner-friendly **Flask** web app deployed to the cloud.
Users type a **name** and a **note**, the note is saved in a **managed PostgreSQL
database**, and the latest **50** notes are listed on the page.

Built as part of the **Codomax Digital Solutions** internship (Day 11-15, Module 3).

---

## 1. Overview

| Item | Detail |
|---|---|
| App name | Cloud Notes |
| Framework | Flask 3 + Flask-SQLAlchemy |
| Language | Python 3.11 |
| Web server | Gunicorn (production WSGI server) |
| Database | PostgreSQL on Render (SQLite locally) |
| Cloud platform | Render.com (free tier) |
| Health check | `/health` |
| JSON API | `/api/notes` |
| Secrets | Environment variables only - nothing secret is in the code |

---

## 2. Deployment flow

This is the flow required for Module 3:
**Application Code -> Cloud Compute -> Database/Storage -> Networking -> Live Web Application**

| # | Stage | What happens | Where |
|---|---|---|---|
| 1 | **Application Code** | Python Flask code pushed to GitHub. The platform reads `requirements.txt` to know what to install. | GitHub repository |
| 2 | **Cloud Compute** | Render builds the app with `pip install -r requirements.txt` and runs it with `gunicorn app:app`. This is the compute service. | Render Web Service |
| 3 | **Database / Storage** | Notes are stored in a managed PostgreSQL instance created in the Render dashboard. The connection string arrives as `DATABASE_URL`. | Render PostgreSQL |
| 4 | **Networking** | Render assigns a public HTTPS URL, its load balancer forwards requests to the Gunicorn container, and the app connects out to PostgreSQL on port 5432. The `/health` endpoint lets the platform monitor uptime. | Render edge network |
| 5 | **Live Web Application** | The site is online 24/7 at the generated `onrender.com` URL. Anyone with the link can add and read notes. | Public URL |

---

## 3. Project structure

```
Module3-Cloud-Web-App/
|
|-- app.py                 # The whole application: config, logging, database model and the 3 routes
|-- templates/
|   `-- index.html         # The single web page - the form, the error box and the list of notes
|-- static/
|   `-- style.css          # Responsive, mobile-friendly styling (plain CSS, no framework)
|-- test_app.py            # Automated tests for /, /health, /api/notes, validation and XSS escaping
|-- requirements.txt       # The Python packages to install: Flask, Flask-SQLAlchemy, gunicorn, psycopg2-binary
|-- Procfile               # Tells the platform the start command: "web: gunicorn app:app"
|-- .env.example           # Example environment variables - copy to .env; the real .env is never committed
|-- .gitignore             # Stops secrets, .env, *.db, __pycache__, venv and *.pem from being committed
`-- README.md              # This file
```

**What each file does in one line**

| File | One-line purpose |
|---|---|
| `app.py` | Creates the Flask app, reads environment variables, sets up logging, defines the `Note` table and the `/`, `/health` and `/api/notes` routes. |
| `templates/index.html` | The HTML page with the add-note form and the list of the latest 50 notes. |
| `static/style.css` | Makes the page look clean and work on phones (media query for small screens). |
| `test_app.py` | Runs 25 automatic checks on the app and prints PASS or FAIL for each one. |
| `requirements.txt` | Lists the four Python libraries the app needs, with fixed versions. |
| `Procfile` | One line that tells Render the web process is `gunicorn app:app`. |
| `.env.example` | A template of the environment variables - shows the names and safe placeholder values. |
| `.gitignore` | A safety list that keeps `.env`, `*.db`, `__pycache__`, `venv` and `*.pem` out of Git. |

---

## 4. Environment variables

All configuration comes from environment variables. **No secret is ever written in the code.**

| Variable | Required? | Default if missing | What it does |
|---|---|---|---|
| `SECRET_KEY` | Yes in production | Random temporary key (with a warning in the logs) | Secret key Flask uses to sign session cookies. |
| `DATABASE_URL` | Yes in production | `sqlite:///cloud_notes.db` | Database connection string. `postgres://` is converted to `postgresql://` automatically. |
| `APP_NAME` | No | `Cloud Notes` | The name shown in the page header and in the JSON responses. |
| `MAX_MESSAGE_LENGTH` | No | `500` | Longest note allowed, in characters. Longer input is rejected. |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING` or `ERROR`. |
| `PORT` | No (auto on Render) | `5000` | The port the local server listens on. Render sets `PORT` by itself. |

### The two secret rules

1. **Never commit `.env`.** It is already listed in `.gitignore`.
2. **Never print a secret.** The app has a `mask_database_url()` helper that turns
   `postgresql://user:supersecret@host/db` into `postgresql://user:\*\*\*\*@host/db`
   before writing anything to the logs.

Generate a good `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 5. Run it locally

```bash
# 1. Go into the project folder
cd Module3-Cloud-Web-App

# 2. Create a virtual environment (keeps packages separate from your computer)
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 4. Install the packages
pip install -r requirements.txt

# 5. Create your own settings file (Windows: copy .env.example .env)
copy .env.example .env

# 6. Start the app
python app.py
```

Open **<http://127.0.0.1:5000>** in your browser.
Add a note, then check <http://127.0.0.1:5000/health> and <http://127.0.0.1:5000/api/notes>.

### Run the tests

```bash
python test_app.py
```

Expected output ends with:

```
ALL TESTS PASSED (25 checks)
```

### Run it the way the cloud runs it

```bash
gunicorn app:app
```

---

## 6. Deploy to Render (free tier) - step by step

### Step 1 - Push the code to GitHub

```bash
git init
git add .
git commit -m "Cloud Notes - Module 3 web app"
git branch -M main
git remote add origin https://github.com/zainab1315/Module-3-Cloud-Web-App.git
git push -u origin main
```

Confirm on GitHub that `.env`, `*.db` and `venv/` are **not** in the file list.

### Step 2 - Create the free PostgreSQL database

1. Go to <https://dashboard.render.com> and sign in.
2. Click **New +** -> **Postgres**.
3. Fill in the form:
   - **Name:** `cloud-notes-db`
   - **Database:** `cloud_notes`
   - **User:** leave the generated value
   - **Region:** pick the region closest to you (e.g. `Oregon`)
   - **PostgreSQL Version:** `16`
   - **Plan:** **Free**
4. Click **Create Database**.
5. Wait about 1-2 minutes until the status shows **Available**.
6. Inside the database page, open the **Internal Database URL** section and copy the
   connection string. It looks like this:

   ```
   postgresql://cloud_notes_user:<YOUR_PASSWORD>@internal.d-aide-c8e1.internal:5432/cloud_notes
   ```

   This URL contains a password. Keep it private - paste it straight into Render in Step 4.

### Step 3 - Create the Web Service

1. Still on the Render dashboard, click **New +** -> **Web Service**.
2. **Connect a repository:** select `zainab1315/Module-3-Cloud-Web-App` and click **Connect**.
   (First time only: Render asks for GitHub permission - click **Authorize**.)
3. Configure the service:

   | Field | Value |
   |---|---|
   | Name | `cloud-notes` |
   | Region | Same region as the database |
   | Branch | `main` |
   | **Root Directory** | leave empty |
   | **Runtime** | `Python` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn app:app` |
   | Instance Type | **Free** |

4. Click **Create Web Service**.

### Step 4 - Add the environment variables (the secret part)

1. On the Web Service page, open the **Environment** tab.
2. Click **Add Environment Variable** and add each one:

   | Key | Value |
   |---|---|
   | `SECRET_KEY` | The long random string you generated (click **Generate** next to the field to let Render make one) |
   | `DATABASE_URL` | The Internal Database URL copied in Step 2 |
   | `APP_NAME` | `Cloud Notes` |
   | `MAX_MESSAGE_LENGTH` | `500` |
   | `LOG_LEVEL` | `INFO` |

3. Click **Save Changes**. Any change here triggers a new deploy.

### Step 5 - Deploy and test

1. Open the **Events** tab and watch the build. You should see:

   ```
   ==> Installing dependencies
   Successfully installed Flask-3.0.3 Flask-SQLAlchemy-3.1.1 gunicorn-22.0.0 psycopg2-binary-2.9.9
   ==> Starting process with command: gunicorn app:app
   Service live
   ```

2. When it says **Service live**, copy the URL from the top of the dashboard, for example
   `https://cloud-notes.onrender.com`.
3. Test the live site:
   - `https://cloud-notes.onrender.com/` - the form and the note list
   - `https://cloud-notes.onrender.com/health` - must show `"status": "healthy"`
   - `https://cloud-notes.onrender.com/api/notes` - must show `"count": 0` (or more)
4. Open the **Logs** tab. You should see lines like:

   ```
   2026-01-15 10:20:31 | INFO | cloud_notes | Cloud Notes starting | LOG_LEVEL=INFO | DB=postgresql://cloud_notes_user:****@internal...
   2026-01-15 10:20:45 | INFO | cloud_notes | Note added by Zainab (id=1)
   ```

   Note the `****` - the password is masked, exactly as designed.

### Step 6 - Keep the free instance awake (optional)

Free instances sleep after 15 minutes of inactivity and the first request after that
takes about 50 seconds. To avoid this, create a free **UptimeRobot** monitor (or use
Render's paid "always on" option):

1. Sign up at <https://uptimerobot.com> (free account).
2. **Add New Monitor** -> Type: `HTTP(s)` -> Friendly name: `Cloud Notes`.
3. URL: `https://cloud-notes.onrender.com/health`
4. Monitoring Interval: `5 minutes`.
5. Click **Create Monitor**.

---

## 7. Endpoints

| Method | Route | Returns | Purpose |
|---|---|---|---|
| `GET` | `/` | HTML page | Form to add a note + the latest 50 notes, newest first. |
| `POST` | `/` | Redirect (302) | Validates and saves the note, then redirects back to `/`. |
| `GET` | `/health` | JSON + `200` / `503` | Runs `SELECT 1` on the database. Used by the cloud platform for monitoring. |
| `GET` | `/api/notes` | JSON | The latest notes as JSON. Supports `?limit=10` (max 50). |
| `GET` | `/static/style.css` | CSS | The stylesheet. |

### Example responses

`GET /health`

```json
{
  "status": "healthy",
  "app": "Cloud Notes",
  "database": "connected",
  "details": "database connection OK",
  "notes_displayed": 50,
  "timestamp": "2026-01-15T10:20:31.123456+00:00"
}
```

`GET /api/notes`

```json
{
  "count": 1,
  "app": "Cloud Notes",
  "notes": [
    {
      "id": 1,
      "author": "Zainab",
      "message": "Deployed Cloud Notes to Render.",
      "created_at": "2026-01-15T10:20:45.987654+00:00"
    }
  ]
}
```

---

## 8. Troubleshooting

| Problem | Why it happens | How to fix |
|---|---|---|
| **Build fails: `ERROR: Could not find a version that satisfies the requirement`** | The version in `requirements.txt` does not exist for the Python version on Render. | Check the exact versions on <https://pypi.org/project/Flask/>. Or loosen to `Flask>=3.0,<4.0`. Make sure the **Runtime** is set to a Python version that matches. |
| **Build fails: `error: command 'gcc' failed`** | Render picked a build that needs compiling. | `psycopg2-binary` normally avoids this. Confirm the package name is exactly `psycopg2-binary`. Re-deploy with **Clear Build Cache**. |
| **Deploy succeeds but the site shows `502 Bad Gateway`** | The app crashed on start, so there is nothing behind the URL. | Open **Logs**. The last traceback is the real cause. Most often it is a database error - check `DATABASE_URL`. Also confirm the start command has no typo and no brackets. |
| **`502` or `Internal Server Error` with `could not translate host name`** | Wrong region or a bad hostname in the database URL. | The database and the web service must be in the **same region**. Re-copy the **Internal Database URL** (not the external one). |
| **`psycopg2.OperationalError: could not connect to server`** | `DATABASE_URL` missing, wrong, or the free database expired. | Confirm the variable name is exactly `DATABASE_URL`. Confirm the value starts with `postgresql://`. Check the database still shows **Available**. |
| **`relation "notes" does not exist`** | The table was never created. | The app calls `db.create_all()` on start, so trigger a fresh deploy. Confirm the start command is `gunicorn app:app`. |
| **`502` right after adding an environment variable** | The service was still restarting. | Wait 60 seconds and refresh. Check the **Events** tab for the new build. |
| **Free instance sleeps / site is very slow** | Normal free-tier behaviour: sleep after 15 minutes idle. | Set up the UptimeRobot monitor from Step 6, or expect the first request after waking to take up to a minute. |
| **`Application does not exist` / wrong app on the URL** | The Render service name does not match. | Use the exact URL Render shows at the top of the Web Service dashboard. |
| **`cannot import name 'app'`** | Wrong start command or wrong file name. | Use exactly `gunicorn app:app` (lowercase `app`, one colon, no `.py`). |
| **Nothing appears in the Logs tab** | `LOG_LEVEL` is set too high, or the app crashed before logging. | Set `LOG_LEVEL=INFO` (or `DEBUG` while debugging) and trigger a request. |

---

## 9. Security practices used

- **Secrets only in environment variables.** `.env` is git-ignored and never committed.
- **Passwords never printed.** `mask_database_url()` hides the password in logs.
- **Input validation.** Name max 80 characters, note max `MAX_MESSAGE_LENGTH` characters.
- **HTML escaping / XSS protection.** HTML tags are stripped from input, and Jinja2
  escapes all output again, so `<script>` tags become harmless text.
- **No SQL injection.** SQLAlchemy sends parameterised queries - raw SQL is never built
  by string concatenation.
- **Production WSGI server.** Gunicorn handles many requests properly, unlike Flask's
  development server.
- **HTTPS only.** Render issues a TLS certificate automatically.

---

## 10. Key learnings

1. **The same code runs locally and in the cloud** - only the environment variables change.
2. **`DATABASE_URL` is the bridge** between the app and a managed database. The
   `postgres://` to `postgresql://` fix is a real-world detail worth remembering.
3. **Never hard-code secrets.** Environment variables plus a `.gitignore` remove the risk
   of leaking a password into Git history.
4. **Logs are a cloud feature, not just a local one.** Printing to stdout is what makes
   the Render log dashboard work.
5. **`/health` is what makes auto-scaling and monitoring possible.** A monitoring service
   needs a simple yes/no answer about whether the app and its database are alive.
6. **Managed services save real time.** A managed PostgreSQL database handles backups,
   patching and uptime, so the code only has to connect.
7. **Free tiers have costs.** Sleeping instances and monthly limits are quota behaviour
   you must plan for.
8. **Troubleshooting is part of cloud work.** Build errors, 502s and connection refused
   are normal - the answer is always in the logs.

---

## 11. Author

**Thajudeen Shuknatha Zainab**
GitHub: <https://github.com/zainab1315>
Repository: <https://github.com/zainab1315/Module-3-Cloud-Web-App>

Codomax Digital Solutions - Internship Programme, Module 3 (Day 11-15):
*Cloud Services &amp; Web App Deployment*

---

## 12. License

Released for educational and internship purposes.
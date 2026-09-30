"""
Simple test script for Cloud Notes.

It starts the real Flask test client, visits every page, adds notes and checks
the answers. Run it with:

    python test_app.py

Expected result: all checks print PASS and the script ends with "ALL TESTS PASSED".
"""

import os
import sys
import tempfile

# Use a temporary SQLite database so the test never touches your real data.
TMP_DB = os.path.join(tempfile.gettempdir(), "cloud_notes_test.db")
if os.path.exists(TMP_DB):
    os.remove(TMP_DB)

os.environ["DATABASE_URL"] = "sqlite:///" + TMP_DB.replace("\\", "/")
os.environ["SECRET_KEY"] = "test-key-not-a-real-secret"
os.environ["APP_NAME"] = "Cloud Notes"
os.environ["MAX_MESSAGE_LENGTH"] = "200"
os.environ["LOG_LEVEL"] = "WARNING"

import app as cloud_notes  # noqa: E402

results = []


def check(name, condition, extra=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, condition))
    print("[%s] %s %s" % (status, name, extra))


with cloud_notes.app.test_client() as client:
    # --- 1. Home page loads ---------------------------------------------
    resp = client.get("/")
    check("GET / returns 200", resp.status_code == 200, "(got %s)" % resp.status_code)
    check("Home page shows the form", b"Add a note" in resp.data)
    check("Home page shows the app name", b"Cloud Notes" in resp.data)

    # --- 2. Adding a valid note -----------------------------------------
    resp = client.post("/", data={"author": "Zainab", "message": "Hello from Cloud Module 3!"})
    check("POST / with valid note redirects", resp.status_code == 302)
    page = client.get("/").data.decode("utf-8")
    check("New note appears on the page", "Hello from Cloud Module 3!" in page)
    check("Author appears on the page", "Zainab" in page)

    # --- 3. Health check -------------------------------------------------
    resp = client.get("/health")
    check("GET /health returns 200", resp.status_code == 200, "(got %s)" % resp.status_code)
    data = resp.get_json()
    check("Health says healthy", data["status"] == "healthy", "(got %s)" % data["status"])
    check("Health says database connected", data["database"] == "connected")
    check("Health reports notes_displayed = 50", data["notes_displayed"] == 50)

    # --- 4. JSON API -----------------------------------------------------
    resp = client.get("/api/notes")
    check("GET /api/notes returns 200", resp.status_code == 200)
    data = resp.get_json()
    check("API returns the saved note", data["count"] == 1, "(count=%s)" % data["count"])
    check("API note has author", data["notes"][0]["author"] == "Zainab")
    check("API note has a timestamp", data["notes"][0]["created_at"] is not None)

    # --- 5. Input validation --------------------------------------------
    resp = client.post("/", data={"author": "", "message": "no name here"})
    check("Empty name is rejected", b"Please enter your name" in resp.data)

    resp = client.post("/", data={"author": "Zainab", "message": ""})
    check("Empty note is rejected", b"Please enter a note" in resp.data)

    resp = client.post("/", data={"author": "Zainab", "message": "x" * 500})
    check("Too-long note is rejected", b"too long" in resp.data)

    # --- 6. HTML escaping / XSS protection --------------------------------
    resp = client.post("/", data={"author": "<script>alert(1)</script>",
                                  "message": "safe text"})
    page = resp.data.decode("utf-8")
    check("Script tag is stripped", "<script>alert(1)</script>" not in page)
    check("Escaped text is safe", "&lt;script&gt;" in page or "alert(1)" not in page)

    # --- 7. 404 handler ----------------------------------------------------
    resp = client.get("/no-such-page")
    check("Unknown page returns 404", resp.status_code == 404, "(got %s)" % resp.status_code)
    resp = client.get("/api/does-not-exist")
    check("Unknown API page returns JSON 404", resp.get_json()["error"] == "not found")

    # --- 8. Database URL normalisation -------------------------------------
    original = cloud_notes.normalize_database_url
    check("postgres:// is converted",
          original("postgres://u:p@host:5432/db") == "postgresql://u:p@host:5432/db")
    check("postgresql:// is left alone",
          original("postgresql://u:p@host:5432/db") == "postgresql://u:p@host:5432/db")
    check("sqlite:// is left alone",
          original("sqlite:///local.db") == "sqlite:///local.db")

    # --- 9. Secrets are masked in logs ---------------------------------------
    masked = cloud_notes.mask_database_url("postgresql://user:supersecret@host:5432/db")
    check("Database password is masked", "supersecret" not in masked, "(masked=%s)" % masked)

print("")
failed = [n for n, ok in results if not ok]
if failed:
    print("%d TEST(S) FAILED:" % len(failed))
    for name in failed:
        print("  - %s" % name)
    sys.exit(1)

print("ALL TESTS PASSED (%d checks)" % len(results))

# The SQLite file may still be open, so a delete failure here is harmless.
try:
    if os.path.exists(TMP_DB):
        os.remove(TMP_DB)
except OSError:
    pass
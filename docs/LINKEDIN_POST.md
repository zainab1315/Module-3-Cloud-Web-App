# LinkedIn Post - Module 3 Complete

**Copy everything between the two lines below and paste it into LinkedIn.**

---

Module 3 Complete ✅ | Cloud Services & Web App Deployment

Day 11–15 of my internship at **Codomax Digital Solutions** is done, and I went from learning about the cloud to actually deploying on it. 🚀

This module was all about turning code into a real, live website — and understanding every piece in between.

☁️ **What I explored**

• **Compute** — how VMs, containers and serverless differ, and when to use each
• **Object storage** — buckets, versioning and why files shouldn't live in your database
• **Managed databases** — letting the provider handle backups, patching and uptime
• **Virtual networking** — public vs private subnets, security groups, load balancers
• **IAM policies** — least privilege, written as explicit JSON instead of blanket access
• **Cloud monitoring** — logs, metrics, alerts and why a health check must test real dependencies

🔐 **What I learned about doing this safely**

Secrets belong in environment variables, never in code. A `.gitignore` stops `.env` and `*.pem` from ever reaching Git history — because once a secret is pushed, deleting it later does NOT remove it. And logging needs care: my app masks the database password as `****` in every log line, so logs stay safe to share.

🚀 **The project: Cloud Notes**

A Flask web app where you enter a name and a note, and it saves to a managed PostgreSQL database and lists the latest 50 notes.

The flow I deployed, end to end:

`Application Code → Cloud Compute → Database / Storage → Networking → Live Web Application`

🧱 Built with Flask · Flask-SQLAlchemy · Gunicorn · PostgreSQL
🔍 Endpoints: `/` · `/health` · `/api/notes`
✅ 25/25 automated tests passing before deploy
🔒 Input validation, HTML escaping, no secrets in the repo

🧠 **My biggest takeaway**

The same code ran on my laptop and in the cloud completely unchanged — the only difference was a set of environment variables. That clicked something for me: deploying to the cloud isn't about magic, it's about knowing where your configuration, your secrets and your data are supposed to live.

The hardest bugs weren't in my code — they were `postgres://` vs `postgresql://`, a database in the wrong region, and a 502 that only made sense once I read the deploy logs. Cloud work is mostly troubleshooting, and that's a skill in itself.

📂 **GitHub:** https://github.com/zainab1315/Module-3-Cloud-Web-App
🌐 **Live app:** https://cloud-notes-app.onrender.com
❤️ **Health check:** https://cloud-notes-app.onrender.com/health

📄 The full Module 3 report is in the repository as both DOCX and PDF.

Huge thanks to the trainers and mentors at **Codomax Digital Solutions** for this module — the hands-on cloud demos made all of this click. 🙏

If you're on a cloud journey too, remember: read the logs first, and never trust a `.env` that isn't git-ignored. ☁️

#CloudComputing #AWS #Azure #GCP #Render #Flask #Python #PostgreSQL #WebDeployment #DevOps #CloudEngineering #FullStack #Internship #CodomaxDigitalSolutions #LearningInPublic #100DaysOfCode #TechLearning #CloudNative #SQL #GitHub

---

## Posting tips

1. Paste only the text between the two `---` lines.
2. Paste the **Live app** link as a link preview: paste the URL on its own line and wait for LinkedIn to generate the card.
3. Post between **8–10 AM** for the best reach.
4. After posting, reply to your first comment with the GitHub link again — it boosts visibility.
5. Rename the service on Render to `cloud-notes` so the URL matches the caption.
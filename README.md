# Smart Civic — Civic Issue Management Platform

A full-stack web application that lets citizens report infrastructure problems (potholes, leaks, garbage) and lets administrators track, manage, and resolve them in real time.

---

## Features

| Feature | Description |
|---|---|
| Citizen Portal | Register, log in, submit complaints with photo and map pin |
| Admin Portal | View all complaints, update statuses, see analytics |
| Auto-Categorisation | Complaints auto-tagged as Water / Road / Sanitation / General |
| Kanban Board | Drag-and-drop style view of Pending → In Progress → Resolved |
| Notifications | Citizens receive a notification every time status changes |
| JWT API | REST API endpoints secured with JSON Web Tokens |
| Map Integration | Leaflet map for geo-tagging complaints |

---

## Tech Stack

- **Backend:** Python 3.x, Django 5.2, Django REST Framework
- **Auth:** Django sessions (UI) + JWT (API)
- **Database:** SQLite (local dev) / PostgreSQL (production on Render)
- **Frontend:** HTML, Tailwind CSS, vanilla JavaScript
- **Static files:** WhiteNoise (no separate CDN needed)
- **Deployment:** Render

---

## Local Development Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/smart-civic.git
cd smart-civic/smart_civic

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your local .env file
cp .env.example .env
# Edit .env: set DEBUG=True, leave DATABASE_URL blank

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser (admin account)
python manage.py createsuperuser

# 7. Start development server
python manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

---

## Database Design

```
User (Django built-in)
 └── Complaint   [FK: user]   — title, desc, location, lat/lng, status, category, image
      └── Comment [FK: complaint, user] — text
 └── Notification [FK: user]  — message, is_read
```

**Why PostgreSQL over SQLite for production?**
- SQLite stores data in a single file — on Render's free tier that file is wiped on every redeploy
- PostgreSQL is a persistent, managed database — data survives restarts and deploys
- PostgreSQL supports concurrent writes, which SQLite cannot handle safely
- PostgreSQL's query planner uses the indexes we added (`user+status`, `status`, `created_at`)

---

## Deploy on Render (with PostgreSQL)

### Option A — Automatic (render.yaml)
1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo — Render reads `render.yaml` and creates everything automatically

### Option B — Manual
1. **Create a PostgreSQL database** on Render → note the Internal Database URL
2. **Create a Web Service** on Render:
   - Runtime: Python
   - Build Command: `./build.sh`
   - Start Command: `gunicorn smart_civic.wsgi:application --workers 2 --threads 2 --timeout 120`
3. **Set Environment Variables** in Render:
   | Key | Value |
   |---|---|
   | `SECRET_KEY` | (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | `your-app-name.onrender.com` |
   | `DATABASE_URL` | (paste the Internal Database URL from step 1) |
4. Click **Deploy** — `build.sh` runs `collectstatic` and `migrate` automatically

---

## Live Demo

https:https://smart-civic-1.onrender.com/


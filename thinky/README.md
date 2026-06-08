# Thinky Backend

Django REST API for the Thinky educational game.

## Railway Deployment

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Prepare for Railway deployment"
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

### 2. Create Railway project

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. **New Project** → **Deploy from GitHub repo** → select your repository.
3. Open the service **Settings** and set **Root Directory** to: `thinky`
4. Add **PostgreSQL** from **+ New** → **Database** → **PostgreSQL** (Railway sets `DATABASE_URL` automatically).

### 3. Environment variables

In Railway → your service → **Variables**, add:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Long random string (generate one) |
| `DEBUG` | `False` |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `GEMINI_API_KEY` | Your Gemini API key (optional) |

`DATABASE_URL` and `RAILWAY_PUBLIC_DOMAIN` are set by Railway automatically.

### 4. Generate domain

Railway → service → **Settings** → **Networking** → **Generate Domain**.

### 5. Verify

- API docs: `https://YOUR-DOMAIN.railway.app/api/docs/`
- Admin: `https://YOUR-DOMAIN.railway.app/admin/`

## Local development

```bash
cd thinky
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env    # then edit .env
python manage.py migrate
python manage.py runserver
```

For the full local dependency set (TensorFlow, etc.), use `requirements-local.txt`.

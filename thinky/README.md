# Thinky Backend

Django REST API for the Thinky educational game.

## Railway Deployment

### 1. Push to GitHub

```bash
git add .
git commit -m "Merge and add Railway deployment"
git push -u origin main
```

### 2. Create Railway project

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. **New Project** → **Deploy from GitHub repo** → select your repository.
3. Open the service **Settings** and set **Root Directory** to: `thinky`
4. (Optional) Add a **Volume** mounted at `/data` so SQLite data survives redeploys.

### 3. Environment variables

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Long random string |
| `DEBUG` | `False` |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `GEMINI_API_KEY` | Your Gemini API key (optional) |

### 4. Generate domain

Railway → service → **Settings** → **Networking** → **Generate Domain**.

### 5. Verify

- API docs: `https://YOUR-DOMAIN.railway.app/api/docs/`
- Admin: `https://YOUR-DOMAIN.railway.app/admin/`

## Local development

```bash
cd thinky
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

For the full local dependency set (TensorFlow, etc.), use `requirements-local.txt`.

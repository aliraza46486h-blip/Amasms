# SMS Proxy Server

Multi-slot SMS OTP proxy — bypasses CORS, fires from server side.

## Files
- `app.py` — main server
- `requirements.txt` — dependencies
- `Procfile` — for hosting platforms
- `runtime.txt` — Python version

## Local Run
```bash
pip install -r requirements.txt
python app.py
```

## API Endpoints

### GET /
Status check

### GET /slots
List all configured slots

### POST /fire-all
Fire all enabled slots
```json
{"phone": "03001234567", "count": 1}
```

### POST /fire-slot/0
Fire slot by index (0 = first slot)
```json
{"phone": "03001234567", "count": 3}
```

## Add New API Slot
Open `app.py`, add to `API_SLOTS` list:
```python
{
    "name": "SiteName OTP",
    "enabled": True,
    "url": "https://api.site.com/send-otp",
    "method": "POST",
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_TOKEN"
    },
    "body": {"phone": "{phone}"},
    "body_type": "json"
}
```

## Host on Render.com (Free)
1. GitHub pe upload karo ye folder
2. render.com pe jao → New Web Service
3. GitHub repo connect karo
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`
6. Deploy → URL milegi

## Host on Railway.app (Free)
1. railway.app pe jao
2. New Project → Deploy from GitHub
3. Repo select karo → auto deploy
4. URL milegi dashboard mein

## Tool mein use karo
Apne SMS tool mein URL change karo:
```
https://YOUR-APP-URL.onrender.com/fire-all
```
Body:
```json
{"phone": "{phone}", "count": 1}
```

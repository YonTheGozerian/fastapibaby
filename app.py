'''from typing import Optional

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}
    '''

import os
import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import redis

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- SQLite on a Render Persistent Disk ---
DB_PATH = os.getenv("DB_PATH", "/var/data/app.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS visits (n INTEGER)")
    cur = conn.cursor()
    cur.execute("SELECT n FROM visits")
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO visits (n) VALUES (0)")
        conn.commit()
    return conn

# --- Redis (Render Key Value exposes a Redis-compatible URL) ---
REDIS_URL = os.getenv("REDIS_URL")
r = redis.Redis.from_url(REDIS_URL) if REDIS_URL else None

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # SQLite counter
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT n FROM visits")
    n = (cur.fetchone()[0] or 0) + 1
    cur.execute("UPDATE visits SET n=?", (n,))
    conn.commit()

    # Redis demo
    cache_hits = None
    if r:
        cache_hits = r.incr("cache_hits")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "visits": n,
            "cache_hits": cache_hits
        }
    )

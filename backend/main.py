import json
from pathlib import Path

from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from fastapi import Form, Request

from fastapi.responses import RedirectResponse

from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

import bcrypt

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="change-this-secret-key")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"

TOPIC_LEARNING_TAGS = {
    "KKT": ["stationarity", "complementary_slackness", "constraint_qualification"],
    "convex function": ["hessian_check", "convexity_proof"],
    "実行可能解": ["feasibility_check"],
    "大域的最適解": ["global_optimality"],
}


def to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def normalize_problem(problem):
    normalized = dict(problem)
    normalized["topics"] = to_list(normalized.get("topics"))
    normalized["keywords"] = to_list(normalized.get("keywords"))

    try:
        normalized["difficulty"] = int(normalized["difficulty"])
    except (KeyError, TypeError, ValueError):
        normalized["difficulty"] = None

    learning_tags = set(normalized.get("learning_tags") or [])
    for topic in normalized["topics"]:
        learning_tags.update(TOPIC_LEARNING_TAGS.get(topic, []))
    normalized["learning_tags"] = sorted(learning_tags)

    proof_skills = set(normalized.get("proof_skills") or [])
    for keyword in normalized["keywords"]:
        key = keyword.lower()
        if "complementary" in key:
            proof_skills.add("complementary_slackness")
        if "stationary" in key:
            proof_skills.add("stationarity")
        if "hessian" in key:
            proof_skills.add("hessian_check")
    normalized["proof_skills"] = sorted(proof_skills)

    return normalized


def load_all_problems():
    problems = []

    for file in DATA_DIR.glob("H*.json"):
        with open(file, "r", encoding="utf-8") as f:
            problems.extend(json.load(f))

    return problems


def unique_values(problems, field):
    values = set()
    for problem in problems:
        value = problem.get(field)
        if isinstance(value, list):
            values.update(value)
        elif value not in (None, ""):
            values.add(value)
    return sorted(values)


@app.get("/metadata")
def get_metadata():
    problems = load_all_problems()
    return {
        "years": unique_values(problems, "year"),
        "types": unique_values(problems, "type"),
        "topics": unique_values(problems, "topics"),
        "keywords": unique_values(problems, "keywords"),
        "difficulties": unique_values(problems, "difficulty"),
        "proof_skills": unique_values(problems, "proof_skills"),
        "count": len(problems),
    }


@app.get("/", response_class=HTMLResponse)
def home():
    html_path = TEMPLATES_DIR / "home.html"
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/problems-page", response_class=HTMLResponse)

def problems_page():

    html_path = TEMPLATES_DIR / "index.html"

    with open(html_path, "r", encoding="utf-8") as f:

        return f.read()


@app.get("/problem/{problem_id}", response_class=HTMLResponse)
def problem_page(problem_id: str):
    html_path = TEMPLATES_DIR / "problem.html"
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/problems")

def get_problems():

    return load_all_problems_from_db()


@app.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    problems = load_all_problems()
    for problem in problems:
        if problem["id"] == problem_id:
            return problem

    return {"error": "Problem not found"}

import sqlite3
DB_PATH = BASE_DIR / "site.db"

def load_all_problems_from_db():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("SELECT * FROM problems")

    rows = cur.fetchall()

    problems = []

    for row in rows:

        problem = dict(row)

        cur.execute(

            "SELECT topic FROM problem_topics WHERE problem_id = ?",

            (problem["id"],)

        )

        problem["topics"] = [r["topic"] for r in cur.fetchall()]

        cur.execute(

            "SELECT keyword FROM problem_keywords WHERE problem_id = ?",

            (problem["id"],)

        )

        problem["keywords"] = [r["keyword"] for r in cur.fetchall()]

        problems.append(problem)

    conn.close()

    return problems

@app.get("/register")

def register_page():

    html_path = TEMPLATES_DIR / "register.html"

    with open(html_path, "r", encoding="utf-8") as f:

        return HTMLResponse(f.read())

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):

    print("USERNAME =", repr(username))
    print("PASSWORD =", repr(password))

    if len(password.encode("utf-8")) > 72:
        return "Password is too long. Please use a password within 72 bytes."

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    password_hash = bcrypt.hashpw(
    password.encode("utf-8"),
    bcrypt.gensalt()
).decode("utf-8")

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "Username already exists"

    conn.close()
    return RedirectResponse("/login", status_code=303)

    try:

        cur.execute(

            "INSERT INTO users (username, password_hash) VALUES (?, ?)",

            (username, password_hash)

        )

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return "Username already exists"

    conn.close()

    return RedirectResponse("/login", status_code=303)

@app.get("/login")

def login_page():

    html_path = TEMPLATES_DIR / "login.html"

    with open(html_path, "r", encoding="utf-8") as f:

        return HTMLResponse(f.read())

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()

    if user is None:
        return "User not found"

    if not bcrypt.checkpw(

    password.encode("utf-8"),

    user["password_hash"].encode("utf-8")

):  return "Wrong password"

    request.session["user_id"] = user["id"]
    request.session["username"] = user["username"]

    return RedirectResponse("/", status_code=303)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

def init_user_tables():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

@app.post("/add-mistake/{problem_id}")

def add_mistake(problem_id: str, request: Request):

    if "user_id" not in request.session:

        return {"success": False, "message": "login required"}

    user_id = request.session["user_id"]

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()

    cur.execute("""

        INSERT OR IGNORE INTO mistakes (user_id, problem_id)

        VALUES (?, ?)

    """, (user_id, problem_id))

    conn.commit()

    conn.close()

    return {"success": True}

def init_mistake_table():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mistakes (
        user_id INTEGER NOT NULL,
        problem_id TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, problem_id)
    )
    """)

    conn.commit()
    conn.close()
    
@app.post("/remove-mistake/{problem_id}")

def remove_mistake(problem_id: str, request: Request):

    if "user_id" not in request.session:

        return {"success": False}

    user_id = request.session["user_id"]

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()

    cur.execute("""

        DELETE FROM mistakes

        WHERE user_id = ? AND problem_id = ?

    """, (user_id, problem_id))

    conn.commit()

    conn.close()

    return {"success": True}

@app.get("/is-mistake/{problem_id}")
def is_mistake(problem_id: str, request: Request):

    if "user_id" not in request.session:
        return {"saved": False}

    user_id = request.session["user_id"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT 1 FROM mistakes
        WHERE user_id = ? AND problem_id = ?
    """, (user_id, problem_id))

    row = cur.fetchone()

    conn.close()

    return {"saved": row is not None}


init_user_tables()
init_mistake_table()

@app.get("/mypage")

def mypage(request: Request):

    if "user_id" not in request.session:

        return RedirectResponse("/login", status_code=303)

    html_path = TEMPLATES_DIR / "mypage.html"

    with open(html_path, "r", encoding="utf-8") as f:

        return HTMLResponse(f.read())
@app.get("/my-mistakes")

def my_mistakes(request: Request):

    if "user_id" not in request.session:

        return []

    user_id = request.session["user_id"]

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()

    cur.execute("""

        SELECT problem_id, created_at

        FROM mistakes

        WHERE user_id = ?

        ORDER BY created_at DESC

    """, (user_id,))

    rows = cur.fetchall()

    conn.close()

    return [

        {

            "problem_id": row[0],

            "created_at": row[1]

        }

        for row in rows

    ]
    
    @app.get("/is-mistake/{problem_id}")
    def is_mistake(problem_id: str, request: Request):

      if "user_id" not in request.session:
        return {"saved": False}

    user_id = request.session["user_id"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT 1 FROM mistakes
        WHERE user_id = ? AND problem_id = ?
    """, (user_id, problem_id))

    row = cur.fetchone()

    conn.close()

    return {"saved": row is not None}
    


app.mount("/static", StaticFiles(directory="static"), name="static")

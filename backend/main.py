import json
from pathlib import Path

from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI()

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
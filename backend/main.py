import json
from pathlib import Path

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


def load_all_problems():
    problems = []
    for file in DATA_DIR.glob("H*.json"):
        with open(file, "r", encoding="utf-8") as f:
            problems.extend(json.load(f))
    return problems


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
    return load_all_problems()


@app.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    problems = load_all_problems()
    for problem in problems:
        if problem["id"] == problem_id:
            return problem
    return {"error": "Problem not found"}

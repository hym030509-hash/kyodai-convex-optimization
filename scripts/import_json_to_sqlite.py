import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "site.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS problems (
    id TEXT PRIMARY KEY,
    year TEXT,
    problem TEXT,
    type TEXT,
    difficulty TEXT,
    common_text TEXT,
    problem_text TEXT,
    solution_text TEXT,
    latex_source TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS problem_topics (
    problem_id TEXT,
    topic TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS problem_keywords (
    problem_id TEXT,
    keyword TEXT
)
""")

cur.execute("DELETE FROM problems")
cur.execute("DELETE FROM problem_topics")
cur.execute("DELETE FROM problem_keywords")

for file in DATA_DIR.glob("H*.json"):
    with open(file, "r", encoding="utf-8") as f:
        problems = json.load(f)

    for p in problems:
        cur.execute("""
        INSERT OR REPLACE INTO problems
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p.get("id"),
            p.get("year"),
            p.get("problem"),
            p.get("type"),
            p.get("difficulty"),
            p.get("common_text"),
            p.get("problem_text"),
            p.get("solution_text"),
            p.get("latex_source")
        ))

        for topic in p.get("topics", []):
            cur.execute(
                "INSERT INTO problem_topics VALUES (?, ?)",
                (p.get("id"), topic)
            )

        for keyword in p.get("keywords", []):
            cur.execute(
                "INSERT INTO problem_keywords VALUES (?, ?)",
                (p.get("id"), keyword)
            )

conn.commit()
conn.close()

print(f"Imported JSON files into {DB_PATH}")
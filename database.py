from __future__ import annotations

import aiosqlite
import json
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "quest.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                members TEXT DEFAULT '[]',
                route TEXT DEFAULT '[]',
                current_stage_index INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                started_at REAL DEFAULT 0,
                finished_at REAL DEFAULT 0,
                is_finished INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                stage_number INTEGER NOT NULL,
                photo_file_id TEXT,
                video_file_id TEXT,
                secret_code TEXT,
                text_answer TEXT,
                status TEXT DEFAULT 'pending',
                reject_reason TEXT,
                submitted_at REAL DEFAULT 0,
                reviewed_at REAL DEFAULT 0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.commit()


# --- Game state ---

async def get_game_active() -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM game_state WHERE key = 'active'"
        )
        row = await cursor.fetchone()
        return row is not None and row[0] == "1"


async def set_game_active(active: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO game_state (key, value) VALUES ('active', ?)",
            ("1" if active else "0",),
        )
        await db.commit()


# --- Teams ---

async def register_team(chat_id: int, name: str, route: list[int]) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO teams (chat_id, name, route) VALUES (?, ?, ?)",
            (chat_id, name, json.dumps(route)),
        )
        await db.commit()
        return cursor.lastrowid


async def get_team_by_chat(chat_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM teams WHERE chat_id = ?", (chat_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        team = dict(row)
        team["route"] = json.loads(team["route"])
        team["members"] = json.loads(team["members"])
        return team


async def get_team_by_id(team_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        team = dict(row)
        team["route"] = json.loads(team["route"])
        team["members"] = json.loads(team["members"])
        return team


async def set_team_members(chat_id: int, members: list[str]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE teams SET members = ? WHERE chat_id = ?",
            (json.dumps(members, ensure_ascii=False), chat_id),
        )
        await db.commit()


async def start_team_timer(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE teams SET started_at = ? WHERE chat_id = ?",
            (time.time(), chat_id),
        )
        await db.commit()


async def advance_team(team_id: int, ball: int):
    async with aiosqlite.connect(DB_PATH) as db:
        team = await get_team_by_id(team_id)
        new_index = team["current_stage_index"] + 1
        new_score = team["score"] + ball

        if new_index >= len(team["route"]):
            await db.execute(
                "UPDATE teams SET current_stage_index = ?, score = ?, "
                "is_finished = 1, finished_at = ? WHERE id = ?",
                (new_index, new_score, time.time(), team_id),
            )
        else:
            await db.execute(
                "UPDATE teams SET current_stage_index = ?, score = ? WHERE id = ?",
                (new_index, new_score, team_id),
            )
        await db.commit()


async def get_all_teams() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM teams ORDER BY score DESC, finished_at ASC")
        rows = await cursor.fetchall()
        teams = []
        for row in rows:
            team = dict(row)
            team["route"] = json.loads(team["route"])
            team["members"] = json.loads(team["members"])
            teams.append(team)
        return teams


async def get_team_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM teams")
        row = await cursor.fetchone()
        return row[0]


# --- Submissions ---

async def create_submission(
    team_id: int,
    stage_number: int,
    photo_file_id: str | None = None,
    video_file_id: str | None = None,
    secret_code: str | None = None,
    text_answer: str | None = None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO submissions "
            "(team_id, stage_number, photo_file_id, video_file_id, secret_code, text_answer, submitted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (team_id, stage_number, photo_file_id, video_file_id, secret_code, text_answer, time.time()),
        )
        await db.commit()
        return cursor.lastrowid


async def get_pending_submissions() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT s.*, t.name as team_name, t.chat_id as team_chat_id "
            "FROM submissions s JOIN teams t ON s.team_id = t.id "
            "WHERE s.status = 'pending' ORDER BY s.submitted_at ASC"
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_submission(submission_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT s.*, t.name as team_name, t.chat_id as team_chat_id "
            "FROM submissions s JOIN teams t ON s.team_id = t.id "
            "WHERE s.id = ?",
            (submission_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_submission_status(submission_id: int, status: str, reject_reason: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE submissions SET status = ?, reject_reason = ?, reviewed_at = ? WHERE id = ?",
            (status, reject_reason, time.time(), submission_id),
        )
        await db.commit()

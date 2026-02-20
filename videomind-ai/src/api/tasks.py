"""Task board API endpoints (file-backed for fast iteration)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

TASKS_FILE = Path(__file__).resolve().parents[2] / "data" / "tasks.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_store() -> None:
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text(json.dumps({"tasks": []}, indent=2), encoding="utf-8")


def _read_store() -> dict:
    _ensure_store()
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))


def _write_store(payload: dict) -> None:
    payload["updated_at"] = _now_iso()
    TASKS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class TaskCreate(BaseModel):
    title: str
    owner: str  # Paul | David
    status: str = "todo"  # todo | doing | blocked | done
    priority: str = "medium"  # low | medium | high
    notes: Optional[str] = None
    due_date: Optional[str] = None


class TaskActivityCreate(BaseModel):
    text: str
    author: str = "David"


class TaskPatch(BaseModel):
    title: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[str] = None


@router.get("/tasks")
async def list_tasks():
    store = _read_store()
    tasks = store.get("tasks", [])
    tasks.sort(key=lambda t: (t.get("status") != "doing", t.get("priority") != "high", t.get("created_at", "")))
    return {"count": len(tasks), "items": tasks}


@router.post("/tasks")
async def create_task(task: TaskCreate):
    store = _read_store()
    now = _now_iso()
    row = {
        "id": str(uuid4()),
        "title": task.title,
        "owner": task.owner,
        "status": task.status,
        "priority": task.priority,
        "notes": task.notes,
        "due_date": task.due_date,
        "created_at": now,
        "updated_at": now,
        "activity": [
            {"ts": now, "author": "David", "text": f"Task created ({task.status})"}
        ],
    }
    store.setdefault("tasks", []).append(row)
    _write_store(store)
    return {"success": True, "item": row}


@router.patch("/tasks/{task_id}")
async def patch_task(task_id: str, patch: TaskPatch):
    store = _read_store()
    tasks: List[dict] = store.get("tasks", [])
    row = next((t for t in tasks if t.get("id") == task_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    now = _now_iso()
    activity = row.setdefault("activity", [])

    for field, value in patch.model_dump(exclude_none=True).items():
        prev = row.get(field)
        row[field] = value
        if prev != value:
            activity.append({"ts": now, "author": "David", "text": f"{field} changed: {prev} → {value}"})

    row["updated_at"] = now

    _write_store(store)
    return {"success": True, "item": row}


@router.post("/tasks/{task_id}/activity")
async def add_task_activity(task_id: str, body: TaskActivityCreate):
    store = _read_store()
    tasks: List[dict] = store.get("tasks", [])
    row = next((t for t in tasks if t.get("id") == task_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    now = _now_iso()
    row.setdefault("activity", []).append({"ts": now, "author": body.author, "text": body.text})
    row["updated_at"] = now
    _write_store(store)
    return {"success": True, "item": row}


@router.post("/tasks/bootstrap")
async def bootstrap_tasks():
    store = _read_store()
    if store.get("tasks"):
        return {"success": True, "created": 0}

    seeds = [
        {
            "title": "Scale AI training directory to 100+ quality videos",
            "owner": "David",
            "status": "doing",
            "priority": "high",
            "notes": "Use batch ingest + quality filters; prioritize OpenClaw + AI workflow creators.",
            "due_date": None,
        },
        {
            "title": "Create YouTube Data API key and connect metadata enrichment",
            "owner": "Paul",
            "status": "todo",
            "priority": "high",
            "notes": "Needed for richer channel metadata and better content targeting.",
            "due_date": None,
        },
        {
            "title": "Choose email stack (Beehiiv or ConvertKit) for weekly digest",
            "owner": "Paul",
            "status": "todo",
            "priority": "medium",
            "notes": "Goal: launch digest quickly with minimal ops overhead.",
            "due_date": None,
        },
        {
            "title": "Build public launch plan (hosting + domain)",
            "owner": "David",
            "status": "todo",
            "priority": "medium",
            "notes": "Use existing domain if available. Keep launch lightweight.",
            "due_date": None,
        },
    ]

    now = _now_iso()
    store["tasks"] = [
        {
            "id": str(uuid4()),
            "created_at": now,
            "updated_at": now,
            "activity": [{"ts": now, "author": "David", "text": "Bootstrapped task"}],
            **seed,
        }
        for seed in seeds
    ]
    _write_store(store)
    return {"success": True, "created": len(seeds)}

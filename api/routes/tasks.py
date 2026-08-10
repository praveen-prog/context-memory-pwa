from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from db_connection import get_supabase

router = APIRouter()

class TaskAdd(BaseModel):
    user_id: str
    location_id: str
    title: str
    description: Optional[str] = ""
    priority: int = 1

class TaskComplete(BaseModel):
    task_id: str
    user_id: str
    method: str = "manual"

@router.post("/add")
def add_task(payload: TaskAdd):
    sb = get_supabase()
    result = sb.table("tasks").insert({
        "user_id": payload.user_id,
        "location_id": payload.location_id,
        "title": payload.title,
        "description": payload.description,
        "status": "pending",
        "priority": payload.priority
    }).execute()
    return {"status": "added", "task": result.data[0]}

@router.post("/complete")
def complete_task(payload: TaskComplete):
    sb = get_supabase()
    from datetime import datetime, timezone
    sb.table("tasks").update({
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", payload.task_id).execute()
    sb.table("task_completions").insert({
        "task_id": payload.task_id,
        "user_id": payload.user_id,
        "method": payload.method,
        "confidence": 1.0
    }).execute()
    return {"status": "completed"}

@router.get("/{user_id}/{location_id}")
def get_tasks(user_id: str, location_id: str):
    sb = get_supabase()
    result = sb.table("tasks").select("*").eq("user_id", user_id).eq("location_id", location_id).order("priority", desc=True).execute()
    return {"tasks": result.data}

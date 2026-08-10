from fastapi import APIRouter
from pydantic import BaseModel
from db_connection import get_supabase
import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

def generate_nudge_groq(trigger_type: str, tasks: list, location_name: str) -> str:
    first = tasks[0]["title"] if tasks else "your items"
    task_list = ", ".join([t["title"] for t in tasks[:3]])
    prompt = f"""You are a reminder assistant. Write ONE very short nudge (max 10 words).
Trigger: {trigger_type}
Store: {location_name}
Items: {task_list}
Be direct and urgent. Just the message."""

    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    print(f"Groq call: model={model} key={api_key[:8]}...")

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 50,
                "temperature": 0.7
            },
            timeout=10
        )
        print(f"Groq status: {response.status_code}")
        result = response.json()
        print(f"Groq result: {result}")
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Groq error: {e}")
        return generate_nudge_fallback(trigger_type, tasks, location_name)

def generate_nudge_fallback(trigger_type: str, tasks: list, location_name: str) -> str:
    count = len(tasks)
    first = tasks[0]["title"] if tasks else "your items"
    others = count - 1
    templates = {
        "arrival": [
            f"You have {count} item{'s' if count > 1 else ''} to pick up here.",
            f"Don't forget {first}{f' and {others} more' if others > 0 else ''}.",
        ],
        "dwell": [
            f"Still need {first}? You've been here a while.",
            f"Don't leave without {first}.",
        ],
        "exit": [
            f"Wait — {first} is still unchecked!",
            f"Leaving without {first}?",
        ]
    }
    return random.choice(templates.get(trigger_type, [f"Don't forget {first}!"]))

class NudgeRequest(BaseModel):
    user_id: str
    location_id: str
    trigger_type: str

@router.post("/generate")
def generate_nudge_endpoint(payload: NudgeRequest):
    sb = get_supabase()
    tasks_result = sb.table("tasks").select("id,title,description,locations(name)").eq("user_id", payload.user_id).eq("location_id", payload.location_id).eq("status", "pending").execute()

    if not tasks_result.data:
        return {"message": "All tasks completed!", "nudge": None}

    location_name = "the store"
    if tasks_result.data[0].get("locations"):
        location_name = tasks_result.data[0]["locations"].get("name", "the store")

    tasks = [{"id": t["id"], "title": t["title"]} for t in tasks_result.data]
    message = generate_nudge_groq(payload.trigger_type, tasks, location_name)

    sb.table("nudge_events").insert({
        "user_id": payload.user_id,
        "task_id": tasks[0]["id"],
        "trigger_type": payload.trigger_type,
        "message": message,
        "delivered": True
    }).execute()

    return {
        "nudge": message,
        "trigger_type": payload.trigger_type,
        "pending_tasks": tasks,
        "location": location_name
    }

@router.get("/history/{user_id}")
def nudge_history(user_id: str):
    sb = get_supabase()
    result = sb.table("nudge_events").select("*,tasks(title)").eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
    return {
        "history": [
            {
                "trigger": r["trigger_type"],
                "message": r["message"],
                "time": r["created_at"],
                "task": r.get("tasks", {}).get("title", "") if r.get("tasks") else ""
            }
            for r in result.data
        ]
    }
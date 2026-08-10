

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from api.routes import location, tasks, nudge, auth

app = FastAPI(title="Context Memory PWA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(location.router, prefix="/location", tags=["location"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(nudge.router, prefix="/nudge", tags=["nudge"])

@app.get("/health")
def health():
    return {"status": "ok", "version": "pwa-1.0"}

@app.get("/setup/ids")
def get_test_ids():
    from db_connection import get_supabase
    sb = get_supabase()
    user = sb.table("users").select("id").limit(1).execute()
    location = sb.table("locations").select("id").limit(1).execute()
    return {
        "user_id": user.data[0]["id"] if user.data else None,
        "location_id": location.data[0]["id"] if location.data else None
    }

@app.post("/reset")
def reset_demo():
    from db_connection import get_supabase
    sb = get_supabase()
    sb.table("nudge_events").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    sb.table("location_events").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    sb.table("task_completions").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    sb.table("tasks").update({"status": "pending", "completed_at": None}).neq("id", "00000000-0000-0000-0000-000000000000").execute()
    return {"status": "reset complete"}

@app.get("/")
def serve_ui():
    return FileResponse("frontend/index.html")

app.mount("/static", StaticFiles(directory="frontend"), name="static")

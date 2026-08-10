from fastapi import APIRouter
from pydantic import BaseModel
from db_connection import get_supabase

router = APIRouter()

class UserCreate(BaseModel):
    name: str
    email: str
    google_id: str
    caregiver_email: str = ""
    mode: str = "standard"

@router.post("/login")
def login_or_create(user: UserCreate):
    sb = get_supabase()
    existing = sb.table("users").select("*").eq("google_id", user.google_id).execute()
    if existing.data:
        return {"user": existing.data[0], "created": False}
    result = sb.table("users").insert({
        "name": user.name,
        "email": user.email,
        "google_id": user.google_id,
        "mode": user.mode,
        "caregiver_email": user.caregiver_email
    }).execute()
    return {"user": result.data[0], "created": True}

@router.get("/user/{google_id}")
def get_user(google_id: str):
    sb = get_supabase()
    result = sb.table("users").select("*").eq("google_id", google_id).execute()
    if not result.data:
        return {"user": None}
    return {"user": result.data[0]}

from fastapi import APIRouter
from pydantic import BaseModel
from db_connection import get_supabase

router = APIRouter()

class LocationEvent(BaseModel):
    user_id: str
    location_id: str
    event_type: str
    lat: float
    lng: float
    dwell_minutes: int = 0

class LocationCreate(BaseModel):
    user_id: str
    name: str
    lat: float
    lng: float
    radius_meters: int = 150
    address: str = ""

@router.post("/event")
def location_event(event: LocationEvent):
    sb = get_supabase()
    sb.table("location_events").insert({
        "user_id": event.user_id,
        "location_id": event.location_id,
        "event_type": event.event_type,
        "lat": event.lat,
        "lng": event.lng,
        "dwell_minutes": event.dwell_minutes
    }).execute()
    pending = sb.table("tasks").select("id,title,description").eq("user_id", event.user_id).eq("location_id", event.location_id).eq("status", "pending").execute()
    return {"event_type": event.event_type, "pending_tasks": pending.data}

@router.post("/add")
def add_location(loc: LocationCreate):
    sb = get_supabase()
    result = sb.table("locations").insert({
        "user_id": loc.user_id,
        "name": loc.name,
        "lat": loc.lat,
        "lng": loc.lng,
        "radius_meters": loc.radius_meters,
        "address": loc.address
    }).execute()
    return {"location": result.data[0]}


@router.get("/list/{user_id}")
def list_locations(user_id: str):
    sb = get_supabase()
    locations = sb.table("locations").select("*").eq("user_id", user_id).execute()
    result = []
    for loc in locations.data:
        tasks = sb.table("tasks").select("id,status").eq("location_id", loc["id"]).execute()
        total = len(tasks.data)
        pending = len([t for t in tasks.data if t["status"] == "pending"])
        result.append({**loc, "total_tasks": total, "pending_tasks": pending})
    return {"locations": result}
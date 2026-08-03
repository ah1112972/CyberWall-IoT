# backend/routers/traffic_stats.py
# Purpose: REST endpoints for recording and retrieving periodic network
# traffic snapshots. Maps to SRS FR-15 (live traffic statistics endpoint)
# and feeds the dashboard's live charts (FR-16).

from fastapi import APIRouter, Depends
from ..database import get_database
from ..models.traffic_stats import TrafficStats

router = APIRouter(prefix="/traffic-stats", tags=["traffic_stats"])


def stats_helper(entry) -> dict:
    entry["_id"] = str(entry["_id"])
    return entry


@router.get("/")
async def get_recent_stats(db=Depends(get_database), limit: int = 100):
    """
    GET /traffic-stats/ — returns the most recent traffic snapshots,
    newest first. The dashboard will call this repeatedly (e.g. every
    few seconds) to draw a live-updating chart.
    """
    cursor = db.traffic_stats.find().sort("timestamp", -1).limit(limit)
    stats = await cursor.to_list(length=limit)
    return [stats_helper(s) for s in stats]


@router.post("/")
async def record_stats(entry: TrafficStats, db=Depends(get_database)):
    """
    POST /traffic-stats/ — saves one new snapshot.
    This will be called periodically by the packet capture/feature
    extraction layer (e.g. once every few seconds), not by a human.
    """
    entry_dict = entry.model_dump(by_alias=True, exclude={"id"})
    result = await db.traffic_stats.insert_one(entry_dict)

    new_entry = await db.traffic_stats.find_one({"_id": result.inserted_id})
    return stats_helper(new_entry)
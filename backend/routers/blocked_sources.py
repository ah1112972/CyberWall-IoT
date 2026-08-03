# backend/routers/blocked_sources.py
# Purpose: REST endpoints for creating, viewing, and releasing blocked
# sources. Maps to SRS FR-11 (automated block), FR-12 (admin override),
# FR-18 (view/manage blocked sources).

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime
from ..database import get_database
from ..models.blocked_source import BlockedSource

router = APIRouter(prefix="/blocked-sources", tags=["blocked_sources"])


def blocked_helper(entry) -> dict:
    entry["_id"] = str(entry["_id"])
    return entry


@router.get("/")
async def list_blocked_sources(db=Depends(get_database), status: str | None = None):
    """
    GET /blocked-sources/ — shows currently blocked (or previously
    blocked) sources. Supports FR-18: "view and manage blocked sources."
    Default behavior (no filter) shows everything; ?status=active
    shows only sources that are currently blocked right now.
    """
    query = {}
    if status:
        query["status"] = status

    cursor = db.blocked_sources.find(query).sort("blocked_at", -1)
    entries = await cursor.to_list(length=1000)
    return [blocked_helper(e) for e in entries]


@router.post("/")
async def block_source(entry: BlockedSource, db=Depends(get_database)):
    """
    POST /blocked-sources/ — records a new block action.
    This is what the decision/response layer calls automatically when
    an alert's confidence score crosses the blocking threshold (FR-11).
    """
    entry_dict = entry.model_dump(by_alias=True, exclude={"id"})
    result = await db.blocked_sources.insert_one(entry_dict)

    new_entry = await db.blocked_sources.find_one({"_id": result.inserted_id})
    return blocked_helper(new_entry)


@router.patch("/{block_id}/release")
async def release_block(block_id: str, released_by: str, db=Depends(get_database)):
    """
    PATCH /blocked-sources/{block_id}/release — lets an administrator
    manually reverse an automated block. This is FR-12 in action:
    "allow an administrator to manually override or reverse an
    automated block."

    Notice this endpoint has its own dedicated URL ending in "/release"
    rather than a generic update — this makes the ACTION explicit and
    clear, rather than just changing a random field through a generic
    PATCH. Anyone reading your API's routes can immediately understand
    what this one specific endpoint does.
    """
    if not ObjectId.is_valid(block_id):
        raise HTTPException(status_code=400, detail="Invalid block ID format")

    result = await db.blocked_sources.update_one(
        {"_id": ObjectId(block_id)},
        {
            "$set": {
                "status": "released",
                "released_at": datetime.utcnow(),
                "released_by": released_by,
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Blocked source not found")

    updated_entry = await db.blocked_sources.find_one({"_id": ObjectId(block_id)})
    return blocked_helper(updated_entry)
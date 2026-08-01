# backend/routers/alerts.py
# Purpose: REST endpoints for creating, listing, and managing alerts.
# Maps to SRS FR-10 (generate alert), FR-14 (expose REST endpoints),
# FR-17 (view alert details including classification and features).

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime
from ..database import get_database
from ..models.alert import Alert

# APIRouter is like a separate, self-contained "module" of routes that
# gets plugged into the main FastAPI app later — similar to organizing
# related functions into their own namespace/header file in C++, rather
# than dumping every function into one giant main.cpp.
router = APIRouter(prefix="/alerts", tags=["alerts"])
# prefix="/alerts" means every route below is automatically reachable
# under /alerts/... (e.g. GET /alerts/, GET /alerts/{id}), so we don't
# have to repeat "/alerts" in every single route definition.


def alert_helper(alert) -> dict:
    """
    MongoDB documents come back with a special ObjectId type in the _id
    field, which isn't directly JSON-serializable (FastAPI wouldn't know
    how to send it back to the browser as-is). This function converts a
    raw MongoDB document into a plain dictionary with _id as a string —
    similar to writing a toJSON()/serialize() method on a C++ struct
    before sending it over a network.
    """
    alert["_id"] = str(alert["_id"])
    return alert


@router.get("/")
async def list_alerts(db=Depends(get_database), limit: int = 50, category: str | None = None):
    """
    GET /alerts/  — returns the most recent alerts.
    Supports FR-16 (dashboard shows real-time alerts) and FR-14 (REST
    endpoint for retrieving alerts).

    limit: how many alerts to return (default 50) — like a LIMIT clause
           in SQL, prevents accidentally returning millions of rows.
    category: optional filter, e.g. ?category=DDoS to see only DDoS alerts.
    """
    query = {}
    if category:
        query["category"] = category
    # In C++ terms, `query` here is like building up a filter struct
    # conditionally, only adding fields that were actually specified.

    # .find(query) returns a cursor (doesn't load everything into memory
    # immediately). .sort("timestamp", -1) sorts newest-first (-1 = descending).
    # .to_list(limit) actually pulls up to `limit` documents into a real list.
    cursor = db.alerts.find(query).sort("timestamp", -1).limit(limit)
    alerts = await cursor.to_list(length=limit)
    # `await` here means "pause this function until the database responds,
    # but let other requests be handled in the meantime" — this is the
    # async behavior we installed motor specifically to get.

    return [alert_helper(a) for a in alerts]


@router.get("/{alert_id}")
async def get_alert(alert_id: str, db=Depends(get_database)):
    """
    GET /alerts/{alert_id} — full details for ONE specific alert.
    Directly implements FR-17: "view details of a specific alert,
    including the classification and features that triggered it."
    """
    if not ObjectId.is_valid(alert_id):
        # Defensive check: if someone requests a garbage/malformed ID,
        # fail clearly and immediately rather than letting MongoDB error
        # out in a confusing way further down.
        raise HTTPException(status_code=400, detail="Invalid alert ID format")

    alert = await db.alerts.find_one({"_id": ObjectId(alert_id)})

    if alert is None:
        # HTTPException is FastAPI's way of returning a proper HTTP error
        # response (status code + message) instead of crashing the server —
        # similar to throwing a custom exception type in C++ that a caller
        # is expected to catch and handle gracefully.
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert_helper(alert)


@router.post("/")
async def create_alert(alert: Alert, db=Depends(get_database)):
    """
    POST /alerts/ — creates a new alert.
    This is what the ML detection engine (or decision/response layer)
    will call whenever it classifies traffic as malicious (FR-10).

    Notice the parameter type: `alert: Alert`. FastAPI sees this and
    automatically: (1) expects a JSON body matching our Alert Pydantic
    model's fields, (2) validates it automatically — reject the request
    with a clear error if, say, confidence_score is outside 0.0-1.0 —
    and (3) gives us a validated Python object to work with, no manual
    parsing required.
    """
    # .model_dump() converts our validated Pydantic object into a plain
    # dict, which is what motor/MongoDB actually expects to insert.
    # exclude={"id"} because MongoDB generates its own _id automatically —
    # we don't want to accidentally send a None id field into the insert.
    alert_dict = alert.model_dump(by_alias=True, exclude={"id"})

    result = await db.alerts.insert_one(alert_dict)
    # insert_one() returns metadata about the insert, including the new
    # document's generated _id — result.inserted_id.

    new_alert = await db.alerts.find_one({"_id": result.inserted_id})
    return alert_helper(new_alert)


@router.patch("/{alert_id}")
async def update_alert_status(alert_id: str, status: str, reviewed_by: str, db=Depends(get_database)):
    """
    PATCH /alerts/{alert_id} — updates JUST the status/reviewer of an
    existing alert, without needing to resend the entire document.
    Supports FR-12 (admin can override/reverse an automated decision) —
    an admin marking an alert as reviewed or overridden goes through here.

    Why PATCH and not PUT? PUT conventionally means "replace this entire
    resource," while PATCH means "update only these specific fields" —
    exactly what we want here, since we're only changing status/reviewer,
    not re-submitting the whole alert.
    """
    if not ObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="Invalid alert ID format")

    result = await db.alerts.update_one(
        {"_id": ObjectId(alert_id)},
        {"$set": {"status": status, "reviewed_by": reviewed_by}},
    )
    # $set is MongoDB's update operator meaning "change only these fields,
    # leave everything else in the document untouched."

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")

    updated_alert = await db.alerts.find_one({"_id": ObjectId(alert_id)})
    return alert_helper(updated_alert)
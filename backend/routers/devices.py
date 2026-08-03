# backend/routers/devices.py
# Purpose: REST endpoints for viewing and managing known devices on the
# network. Maps to SRS FR-13 (persist device records).

from fastapi import APIRouter, Depends, HTTPException
from ..database import get_database
from ..models.device import Device

# This creates a separate group of routes, all automatically starting
# with "/devices" — so we don't have to type "/devices" in front of
# every single route below.
router = APIRouter(prefix="/devices", tags=["devices"])


def device_helper(device) -> dict:
    """
    MongoDB stores devices using ip_address as the main identifier
    (not a generated _id like alerts), but Mongo still adds its own
    internal _id behind the scenes. This function just makes sure that
    _id is converted to a plain string so it can be sent back as JSON.
    """
    if "_id" in device:
        device["_id"] = str(device["_id"])
    return device


@router.get("/")
async def list_devices(db=Depends(get_database), status: str | None = None):
    """
    GET /devices/ — returns all known devices.
    Optional ?status=active or ?status=inactive to filter results.
    """
    query = {}
    if status:
        query["status"] = status

    cursor = db.devices.find(query)
    devices = await cursor.to_list(length=1000)
    return [device_helper(d) for d in devices]


@router.get("/{ip_address}")
async def get_device(ip_address: str, db=Depends(get_database)):
    """
    GET /devices/{ip_address} — look up ONE device by its IP.
    We search by ip_address here (not a generated _id), since that's
    the natural, unique way devices are identified in our schema.
    """
    device = await db.devices.find_one({"ip_address": ip_address})

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return device_helper(device)


@router.post("/")
async def create_or_update_device(device: Device, db=Depends(get_database)):
    """
    POST /devices/ — adds a new device, OR updates it if that IP
    already exists. This is called "upsert" (update + insert combined).

    Why upsert instead of a plain insert? Devices get "seen" repeatedly
    as traffic flows in — we don't want a new duplicate document every
    single time the same device sends a packet. Instead, we just update
    its last_seen timestamp if it already exists.
    """
    device_dict = device.model_dump(by_alias=True, exclude={"id"})

    # update_one() with upsert=True means: "if a device with this
    # ip_address already exists, update it. If not, create it."
    await db.devices.update_one(
        {"ip_address": device.ip_address},
        {"$set": device_dict},
        upsert=True,
    )

    updated_device = await db.devices.find_one({"ip_address": device.ip_address})
    return device_helper(updated_device)
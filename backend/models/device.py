# backend/models/device.py
# Purpose: Represents a known device/IP on the monitored network.
# Maps to SRS FR-13 (persist device records).

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Device(BaseModel):
    # Pydantic's BaseModel is similar to a C++ struct with built-in
    # validation — if you try to create a Device with the wrong type
    # for a field, it raises an error immediately instead of failing
    # silently somewhere downstream.

    ip_address: str = Field(..., description="Primary identifier for this device")
    mac_address: Optional[str] = None  # Optional[str] = "this can be a string OR None"
    hostname: Optional[str] = None

    # datetime, not str — lets MongoDB and our backend do proper date
    # comparisons/sorting later, rather than comparing raw text.
    first_seen: datetime
    last_seen: datetime

    # In C++, you might use an enum class for this. Pydantic can do the
    # same with Python's Literal type, restricting status to exactly
    # these two values — anything else gets rejected automatically.
    status: str = Field(default="active", description="'active' or 'inactive'")

    class Config:
        # Allows Pydantic to build this model directly from a MongoDB
        # document (which arrives as a plain dict), not just from JSON.
        populate_by_name = True
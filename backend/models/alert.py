# backend/models/alert.py
# Purpose: One document per detection event. The core record tying
# together the ML model's output with what the system decided to do.
# Maps to SRS FR-10, FR-13, FR-17.

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from .common import PyObjectId

class Alert(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    # alias="_id" — MongoDB always names its ID field "_id", but that's
    # an awkward Python attribute name (leading underscore has special
    # meaning). The alias lets us call it "id" in our own code while
    # still matching MongoDB's actual field name underneath.

    source_ip: str  # links back to a Device.ip_address
    category: str   # one of our 8 ML categories: "DDoS", "BruteForce", etc.
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    # ge=0.0, le=1.0 means "greater-or-equal to 0, less-or-equal to 1" —
    # Pydantic will reject a confidence score outside that range automatically,
    # same idea as an assert() in C++ but built into the type itself.

    timestamp: datetime

    # FR-17 requires showing "the features that triggered it" — we store
    # the actual feature vector used for this prediction, so an admin can
    # inspect exactly what data led to this alert.
    features: Optional[dict] = None

    action_taken: str = Field(default="alert_only", description="'alert_only', 'blocked', or 'overridden'")
    status: str = Field(default="active", description="'active', 'resolved', or 'overridden'")

    reviewed_by: Optional[str] = None  # admin username, if manually reviewed

    class Config:
        populate_by_name = True
# backend/models/blocked_source.py
# Purpose: Tracks an active or past automated block, separate from the
# alert that triggered it, since a block has its own lifecycle
# (can later be released by an admin). Maps to SRS FR-11, FR-12, FR-18.

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .common import PyObjectId

class BlockedSource(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    ip_address: str          # the blocked device's IP
    alert_id: str            # references the Alert that triggered this block

    blocked_at: datetime
    blocked_by: str = Field(default="system", description="'system' (automated) or an admin username")

    status: str = Field(default="active", description="'active' or 'released'")
    released_at: Optional[datetime] = None
    released_by: Optional[str] = None  # admin who manually reversed the block (FR-12)

    class Config:
        populate_by_name = True
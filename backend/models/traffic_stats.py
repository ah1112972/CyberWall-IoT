# backend/models/traffic_stats.py
# Purpose: Periodic snapshots of overall network activity, independent
# of any specific device or alert. Powers the live dashboard view.
# Maps to SRS FR-15.

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .common import PyObjectId

class TrafficStats(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    timestamp: datetime
    packets_per_second: int
    bytes_total: int
    top_protocol: Optional[str] = None  # e.g. "TCP", "UDP" — whichever dominated this snapshot

    class Config:
        populate_by_name = True
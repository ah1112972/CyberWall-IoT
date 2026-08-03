# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import alerts, devices, blocked_sources, traffic_stats

app = FastAPI(title="CyberWall IoT API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Each of these lines makes one router's endpoints live and reachable.
app.include_router(alerts.router)
app.include_router(devices.router)
app.include_router(blocked_sources.router)
app.include_router(traffic_stats.router)


@app.get("/")
async def root():
    return {"message": "CyberWall IoT API is running"}
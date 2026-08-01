# backend/main.py
# Purpose: The FastAPI application entry point — creates the app,
# enables CORS (so our React frontend can call this API later), and
# plugs in the alerts router.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import alerts

app = FastAPI(title="CyberWall IoT API", version="1.0")

# CORS = Cross-Origin Resource Sharing. Browsers block a webpage on one
# address (e.g. your React dashboard on localhost:3000) from calling an
# API on a different address (this backend, likely localhost:8000)
# UNLESS the API explicitly allows it. This middleware is that permission.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React's default dev server address
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plugs our alerts router into the main app — everything defined with
# @router.get/post/patch in alerts.py becomes live and reachable.
app.include_router(alerts.router)


@app.get("/")
async def root():
    return {"message": "CyberWall IoT API is running"}
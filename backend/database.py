# backend/database.py
# Purpose: Single, shared MongoDB connection used across the whole backend.
# Every route file will import get_database() from here, rather than each
# one opening its own separate connection — similar to a Singleton pattern
# in C++, where you want exactly one connection object shared everywhere.

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Reads the .env file we just created and loads its values as environment
# variables — like reading a config file at startup rather than hardcoding
# secrets directly in source code.
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

# AsyncIOMotorClient is the async equivalent of opening a database
# connection handle. Creating it here (once, at module load time) means
# every part of the app reuses this same client instead of reconnecting
# repeatedly — connections are relatively expensive to set up.
client = AsyncIOMotorClient(MONGO_URI)
database = client[MONGO_DB_NAME]


def get_database():
    """
    Returns the shared database object. Written as a function (rather than
    just importing `database` directly everywhere) so it can be used with
    FastAPI's dependency injection system — you'll see this pattern as
    `db = Depends(get_database)` in our route files next.
    """
    return database
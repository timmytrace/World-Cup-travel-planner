"""Shared MongoDB client configuration for local and Cloud Run runtimes."""

import os

import certifi
from pymongo import MongoClient


def create_mongo_client(uri: str | None = None, timeout_ms: int = 8_000) -> MongoClient:
    """Create a TLS-verified MongoDB client using certifi's CA bundle."""
    connection_uri = uri or os.getenv("MONGODB_URI", "")
    if not connection_uri:
        raise ValueError("MONGODB_URI is not configured")

    return MongoClient(
        connection_uri,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=timeout_ms,
        connectTimeoutMS=timeout_ms,
        socketTimeoutMS=20_000,
        retryWrites=True,
    )


def mongo_fallback_message() -> str:
    """Return a demo-safe message without exposing connection details."""
    return "Cloud trip memory is temporarily unavailable; local session fallback is active."

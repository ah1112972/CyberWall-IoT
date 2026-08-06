# capture/responder.py
# Purpose: Takes a detector's prediction and decides what to do about it —
# log only, create an alert, or create an alert AND block the source.
# Directly implements SRS FR-10, FR-11 (configurable confidence threshold).

import requests
from datetime import datetime, timezone

BACKEND_URL = "http://localhost:8000"

# Two separate thresholds, on purpose:
# - Anything above ALERT_THRESHOLD gets logged as an alert (for visibility)
# - Anything above the HIGHER BLOCK_THRESHOLD also gets auto-blocked
# This matches FR-11's "configurable confidence threshold" requirement,
# and avoids auto-blocking on borderline/uncertain predictions.
ALERT_THRESHOLD = 0.80
BLOCK_THRESHOLD = 0.90


def handle_prediction(source_ip: str, category: str, confidence: float, features: dict):
    """
    Called once per finished flow, right after the Detector has produced
    a prediction. Decides what action (if any) to take.
    """
    # Benign traffic, or anything below our alert threshold, is ignored —
    # this is what keeps the system from flooding alerts on uncertain
    # or genuinely normal traffic.
    if category == "Benign" or confidence < ALERT_THRESHOLD:
        return

    print(f"[ALERT] {source_ip} classified as {category} (confidence: {confidence:.2f})")

    action_taken = "alert_only"

    # --- Always create the alert record first ---
    alert_payload = {
        "source_ip": source_ip,
        "category": category,
        "confidence_score": confidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": features,
        "action_taken": action_taken,  # may get updated below
        "status": "active",
    }

    try:
        response = requests.post(f"{BACKEND_URL}/alerts/", json=alert_payload, timeout=5)
        response.raise_for_status()  # raises an error if the backend responded with a failure status
        created_alert = response.json()
        alert_id = created_alert["_id"]
        print(f"  -> Alert created (id: {alert_id})")
    except requests.exceptions.RequestException as e:
        # If the backend is down or unreachable, we don't want the whole
        # capture pipeline to crash — just log it and move on.
        print(f"  -> Failed to create alert: {e}")
        return

    # --- If confidence is high enough, also create a block ---
    if confidence >= BLOCK_THRESHOLD:
        block_payload = {
            "ip_address": source_ip,
            "alert_id": alert_id,
            "blocked_at": datetime.now(timezone.utc).isoformat(),
            "blocked_by": "system",
            "status": "active",
        }
        try:
            block_response = requests.post(f"{BACKEND_URL}/blocked-sources/", json=block_payload, timeout=5)
            block_response.raise_for_status()
            print(f"  -> Source {source_ip} automatically BLOCKED")

            # Update the alert to reflect that a block actually happened,
            # rather than leaving it saying "alert_only" when a block
            # occurred right afterward.
            requests.patch(
                f"{BACKEND_URL}/alerts/{alert_id}",
                params={"status": "active", "reviewed_by": "system"},
                timeout=5,
            )
        except requests.exceptions.RequestException as e:
            print(f"  -> Failed to create block: {e}")
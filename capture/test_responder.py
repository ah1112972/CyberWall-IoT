# capture/test_responder.py
# Purpose: Simulate a HIGH-confidence malicious prediction directly
# (bypassing the flow tracker/model for this specific test) to confirm
# the responder correctly talks to the real backend.

from responder import handle_prediction

# Manually simulate a confident DDoS detection, to test the alert +
# block logic without needing the model to naturally produce this
# exact result from fake data.
handle_prediction(
    source_ip="192.168.1.99",
    category="DDoS",
    confidence=0.95,  # above BLOCK_THRESHOLD, so this should trigger both an alert AND a block
    features={"Number": 500, "Rate": 300.5},  # a small sample, not the full 46 — fine for this test
)
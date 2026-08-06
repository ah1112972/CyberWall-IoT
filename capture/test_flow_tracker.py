# capture/test_flow_tracker.py
# Purpose: Quick standalone test — simulate a few packets, confirm
# features get computed reasonably, WITHOUT needing real network capture
# or the ML model yet.

from flow_tracker import FlowManager
import time

manager = FlowManager()

# Simulate 5 packets between two fake devices
manager.process_packet("192.168.1.10", "192.168.1.20", size=500, ttl=64, protocol="TCP", tcp_flags=["SYN"], port=80)
time.sleep(0.1)
manager.process_packet("192.168.1.20", "192.168.1.10", size=450, ttl=64, protocol="TCP", tcp_flags=["SYN", "ACK"], port=80)
time.sleep(0.1)
manager.process_packet("192.168.1.10", "192.168.1.20", size=600, ttl=64, protocol="TCP", tcp_flags=["ACK"], port=80)

print("Waiting for flow to time out...")
time.sleep(6)  # wait past FLOW_TIMEOUT_SECONDS

expired = manager.get_expired_flows()
for flow in expired:
    features = flow.compute_features()
    for key, value in features.items():
        print(f"{key}: {value}")
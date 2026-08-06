# capture/test_detector.py
# Purpose: Confirm the model correctly loads and produces a sane
# prediction from our flow tracker's output, before wiring in live
# packet capture or the backend API.

from flow_tracker import FlowManager
from detector import Detector
import time

manager = FlowManager()
detector = Detector(
    model_path="../ml/checkpoints_rf/rf_model.joblib",
    scaler_path="../ml/checkpoints_rf/scaler_rf.joblib",
)

# Same simulated flow as before
manager.process_packet("192.168.1.10", "192.168.1.20", size=500, ttl=64, protocol="TCP", tcp_flags=["SYN"], port=80)
time.sleep(0.1)
manager.process_packet("192.168.1.20", "192.168.1.10", size=450, ttl=64, protocol="TCP", tcp_flags=["SYN", "ACK"], port=80)
time.sleep(0.1)
manager.process_packet("192.168.1.10", "192.168.1.20", size=600, ttl=64, protocol="TCP", tcp_flags=["ACK"], port=80)

print("Waiting for flow to time out...")
time.sleep(6)

expired = manager.get_expired_flows()
for flow in expired:
    features = flow.compute_features()
    category, confidence = detector.predict(features)
    print(f"\nPredicted category: {category}")
    print(f"Confidence: {confidence:.4f}")
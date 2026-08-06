# capture/live_pipeline.py
# Purpose: The full live CyberWall IoT pipeline — captures real packets,
# tracks flows, classifies finished flows with the trained model, and
# automatically alerts/blocks through the backend. This is the actual
# "Decision & Response" layer from the architecture diagram, running live.

import threading
import time
from scapy.all import sniff, IP, TCP, UDP, ICMP

from flow_tracker import FlowManager
from detector import Detector
from responder import handle_prediction

manager = FlowManager()
detector = Detector(
    model_path="../ml/checkpoints_rf/rf_model.joblib",
    scaler_path="../ml/checkpoints_rf/scaler_rf.joblib",
)


def handle_packet(packet):
    """
    Runs once per captured packet — same role as your Phase 0
    handle_packet function, but now feeds the flow tracker instead of
    just classifying by size.
    """
    if IP not in packet:
        return

    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    size = len(packet)
    ttl = packet[IP].ttl

    protocol = "OTHER"
    tcp_flags = []
    port = None

    if TCP in packet:
        protocol = "TCP"
        port = packet[TCP].dport
        # Scapy exposes TCP flags as single-letter codes; we translate
        # them into the full names our flow tracker expects.
        flag_map = {"S": "SYN", "A": "ACK", "F": "FIN", "R": "RST", "U": "URG"}
        flags_str = str(packet[TCP].flags)
        tcp_flags = [flag_map[f] for f in flags_str if f in flag_map]
    elif UDP in packet:
        protocol = "UDP"
        port = packet[UDP].dport
    elif ICMP in packet:
        protocol = "ICMP"

    manager.process_packet(src_ip, dst_ip, size, ttl, protocol, tcp_flags, port)


# In live_pipeline.py, update check_expired_flows_loop() with this check:

# In live_pipeline.py, update check_expired_flows_loop() with this:

def check_expired_flows_loop():
    while True:
        time.sleep(2)
        expired_flows = manager.get_expired_flows()

        for flow in expired_flows:
            features = flow.compute_features()

            if features["Number"] < 4:
                continue

            category, confidence = detector.predict(features)

            # Debug visibility: print EVERY classified flow, not just
            # ones that trigger an alert — lets us confirm the pipeline
            # is genuinely working even when nothing is malicious enough
            # to alert on.
            print(f"[CHECK] {flow.ip_a} -> {flow.ip_b} | {category} ({confidence:.2f}) | packets={features['Number']}")

            handle_prediction(flow.ip_a, category, confidence, features)


def start_sniffing():
    print("CyberWall IoT live detection started...")
    sniff(
        iface="Intel(R) Wi-Fi 6 AX201 160MHz",
        filter="ip",
        prn=handle_packet,
        store=False,
    )


if __name__ == "__main__":
    print("=" * 60)
    print("   CyberWall IoT — Live Detection Pipeline")
    print("=" * 60)

    # Background thread 1: continuously capture packets
    sniff_thread = threading.Thread(target=start_sniffing)
    sniff_thread.daemon = True
    sniff_thread.start()

    # Background thread 2: continuously check for finished flows
    expiry_thread = threading.Thread(target=check_expired_flows_loop)
    expiry_thread.daemon = True
    expiry_thread.start()

    # Keep the main program alive, since both real threads are daemons
    print("Pipeline running. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping CyberWall IoT...")
        
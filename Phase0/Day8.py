import json                             # for JSON operations
import threading                        # for running Scapy and Flask simultaneously
import socket                           # for reverse DNS lookup
from flask import Flask, jsonify        # Flask web framework
from scapy.all import sniff, IP, TCP, UDP, ICMP     # Scapy packet capture


# ─── Flask app setup ──────────────────────────────────────────────────────────

app = Flask(__name__)                   # create Flask application


# ─── Shared data ──────────────────────────────────────────────────────────────

captured_packets = []                   # shared list — both Scapy and Flask access this
capture_stats = {                       # shared stats dictionary
    "total":   0,                       # total packets captured
    "threats": 0,                       # threat count
    "warnings": 0,                      # warning count
    "safe":    0                        # safe count
}


# ─── Packet classification ────────────────────────────────────────────────────

def classify(size):                     # classify packet based on size
    if size > 8000:
        return "THREAT"                 # large = threat
    elif size > 1000:
        return "WARNING"               # medium = warning
    else:
        return "SAFE"                  # small = safe


# ─── Scapy packet handler ─────────────────────────────────────────────────────

def handle_packet(packet):              # runs for every captured packet
    if IP in packet:                    # check if packet has IP layer
        src_ip   = packet[IP].src       # extract source IP
        dst_ip   = packet[IP].dst       # extract destination IP
        size     = len(packet)          # packet size in bytes
        protocol = "OTHER"              # default protocol label

        if TCP in packet:               # check for TCP layer
            protocol = "TCP"
        elif UDP in packet:             # check for UDP layer
            protocol = "UDP"
        elif ICMP in packet:            # check for ICMP layer
            protocol = "ICMP"

        try:
            hostname = socket.gethostbyaddr(dst_ip)[0]  # get domain name
        except socket.herror:           # no domain name found
            hostname = "unknown"

        status = classify(size)         # classify the packet

        # print to terminal so you can see live capture
        print(f"{status:8} | {src_ip:15} → {dst_ip:15} | {hostname:30} | {protocol:5} | {size} bytes")

        # build packet dictionary
        packet_dict = {
            "src_ip":   src_ip,         # source IP
            "dst_ip":   dst_ip,         # destination IP
            "hostname": hostname,       # domain name
            "protocol": protocol,       # protocol type
            "size":     size,           # packet size
            "status":   status          # classification result
        }

        captured_packets.append(packet_dict)    # add to shared list

        # update stats
        capture_stats["total"] += 1             # increment total count
        if status == "THREAT":
            capture_stats["threats"] += 1       # increment threat count
        elif status == "WARNING":
            capture_stats["warnings"] += 1      # increment warning count
        else:
            capture_stats["safe"] += 1          # increment safe count


# ─── Scapy capture function ───────────────────────────────────────────────────

def start_sniffing():                   # function that runs Scapy in background thread
    print("🔍 Scapy capture started in background...")
    sniff(
        iface="Intel(R) Wi-Fi 6 AX201 160MHz",     # your WiFi interface
        filter="ip",                                 # only IP packets
        prn=handle_packet,                           # call handle_packet for each packet
        store=False                                  # don't store in RAM
        # no count — runs forever until program stops
    )


# ─── Flask routes ─────────────────────────────────────────────────────────────

@app.route("/")                         # home route
def home():
    return "🔒 CyberWall IoT — Live Packet API is running!"


@app.route("/packets", methods=["GET"]) # get all captured packets
def get_packets():
    return jsonify(captured_packets)    # return entire captured list as JSON


@app.route("/threats", methods=["GET"]) # get only threat packets
def get_threats():
    threats = [p for p in captured_packets if p["status"] == "THREAT"]
    # filter only THREAT packets from the shared list
    return jsonify(threats)             # return filtered list


@app.route("/summary", methods=["GET"]) # get capture statistics
def get_summary():
    return jsonify(capture_stats)       # return stats dictionary


@app.route("/latest", methods=["GET"])  # get last 10 captured packets
def get_latest():
    latest = captured_packets[-10:]     # [-10:] slices last 10 items from list
    return jsonify(latest)              # return last 10 packets


@app.route("/clear", methods=["DELETE"])    # clear all captured packets
def clear_packets():
    captured_packets.clear()            # empty the shared list
    capture_stats["total"]    = 0       # reset all counters
    capture_stats["threats"]  = 0
    capture_stats["warnings"] = 0
    capture_stats["safe"]     = 0
    return jsonify({"message": "All packets cleared"})  # confirm to client

@app.route("/search/<ip>", methods=["GET"])     
def search_by_ip(ip):
    results = [p for p in captured_packets if p["src_ip"] == ip or p["dst_ip"] == ip]
    if len(results) == 0:               
        return jsonify({"message": "No packets found for this IP"})
    return jsonify(results)

# ─── Main — start both threads ────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("   CyberWall IoT — Live Packet API v0.1")
    print("=" * 60)

    # start Scapy in a background thread
    sniff_thread = threading.Thread(target=start_sniffing)  # create thread
    sniff_thread.daemon = True          # thread stops when main program exits
    sniff_thread.start()               # start the background thread

    # start Flask in main thread — runs forever
    app.run(debug=False, host="0.0.0.0", port=5000)
    # debug=False — because debug=True conflicts with threading
    # host="0.0.0.0" — accessible from any device on your network
    # port=5000 — standard Flask port
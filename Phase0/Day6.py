from flask import Flask, jsonify, request   # import Flask and helper functions
# Flask — the main web framework
# jsonify — converts Python dict to JSON response
# request — lets us read data sent by the client

app = Flask(__name__)   # create the Flask app — __name__ tells Flask where to find files


# ─── Route 1 — Home page ──────────────────────────────────────────────────────

@app.route("/")                     # decorator — defines the URL path
def home():                         # function that runs when this route is visited
    return "CyberWall IoT API is running!"  # plain text response


# ─── Route 2 — Get all packets ────────────────────────────────────────────────

@app.route("/packets", methods=["GET"])     # only accepts GET requests
def get_packets():                          # runs when someone visits /packets
    packets = [                             # sample data — hardcoded for now
        {"src_ip": "192.168.1.5", "dst_ip": "8.8.8.8",     "protocol": "UDP",  "size": 512,  "status": "SAFE"},
        {"src_ip": "192.168.1.6", "dst_ip": "192.168.1.1", "protocol": "TCP",  "size": 9500, "status": "THREAT"},
        {"src_ip": "192.168.1.7", "dst_ip": "142.250.1.1", "protocol": "TCP",  "size": 256,  "status": "SAFE"},
        {"src_ip": "10.0.0.1",    "dst_ip": "192.168.1.5", "protocol": "ICMP", "size": 8100, "status": "THREAT"},
    ]
    return jsonify(packets)                 # convert list to JSON and send back


# ─── Route 3 — Get threats only ───────────────────────────────────────────────

@app.route("/threats", methods=["GET"])     # only accepts GET requests
def get_threats():                          # runs when someone visits /threats
    packets = [                             # same sample data
        {"src_ip": "192.168.1.5", "dst_ip": "8.8.8.8",     "protocol": "UDP",  "size": 512,  "status": "SAFE"},
        {"src_ip": "192.168.1.6", "dst_ip": "192.168.1.1", "protocol": "TCP",  "size": 9500, "status": "THREAT"},
        {"src_ip": "192.168.1.7", "dst_ip": "142.250.1.1", "protocol": "TCP",  "size": 256,  "status": "SAFE"},
        {"src_ip": "10.0.0.1",    "dst_ip": "192.168.1.5", "protocol": "ICMP", "size": 8100, "status": "THREAT"},
    ]
    threats = [p for p in packets if p["status"] == "THREAT"]  # filter threats only
    return jsonify(threats)                 # send back only threats as JSON


# ─── Route 4 — Add a new packet (POST) ───────────────────────────────────────

@app.route("/packets", methods=["POST"])    # only accepts POST requests
def add_packet():                           # runs when someone sends data to /packets
    data = request.get_json()               # read JSON data sent by client

    if not data:                            # check if data was actually sent
        return jsonify({"error": "No data received"}), 400  # 400 = bad request

    # extract fields from received data — use .get() for safe access
    src_ip   = data.get("src_ip",   "unknown")  # get src_ip or "unknown" if missing
    dst_ip   = data.get("dst_ip",   "unknown")  # get dst_ip or "unknown" if missing
    protocol = data.get("protocol", "unknown")  # get protocol or "unknown"
    size     = data.get("size",     0)           # get size or 0 if missing

    # create response confirming what was received
    response = {
        "message":  "Packet received successfully",     # success message
        "src_ip":   src_ip,                             # echo back src_ip
        "dst_ip":   dst_ip,                             # echo back dst_ip
        "protocol": protocol,                           # echo back protocol
        "size":     size,                               # echo back size
        "status":   "THREAT" if size > 8000 else "SAFE"  # quick classification
    }
    return jsonify(response), 201           # 201 = created successfully


@app.route("/summary", methods=["GET"])     # new route for summary
def get_summary():                          # runs when someone visits /summary
    packets = [                             # same packets list
        {"src_ip": "192.168.1.5", "dst_ip": "8.8.8.8",     "protocol": "UDP",  "size": 512,  "status": "SAFE"},
        {"src_ip": "192.168.1.6", "dst_ip": "192.168.1.1", "protocol": "TCP",  "size": 9500, "status": "THREAT"},
        {"src_ip": "192.168.1.7", "dst_ip": "142.250.1.1", "protocol": "TCP",  "size": 256,  "status": "SAFE"},
        {"src_ip": "10.0.0.1",    "dst_ip": "192.168.1.5", "protocol": "ICMP", "size": 8100, "status": "THREAT"},
    ]

    total    = len(packets)                                                     # count all packets
    threats  = len([p for p in packets if p["status"] == "THREAT"])            # count threats
    safe     = len([p for p in packets if p["status"] == "SAFE"])              # count safe
    warning  = len([p for p in packets if p["status"] == "WARNING"])           # count warnings

    summary = {
        "total_packets": total,             # total count
        "threats":       threats,           # threat count
        "safe":          safe,              # safe count
        "warning":       warning            # warning count
    }
    return jsonify(summary)                 # send back as JSON




# ─── Start the server ─────────────────────────────────────────────────────────

if __name__ == "__main__":                  # only runs if this file is run directly
    app.run(debug=True)                     # start server — debug=True auto-restarts on changes
# capture/flow_tracker.py
# Purpose: Groups individual packets into "flows" (a conversation between
# two devices), and once a flow goes quiet for a few seconds, calculates
# an approximation of the 46 statistical features our trained model expects.
#
# IMPORTANT NOTE FOR THE REPORT: some of these features (Magnitude, Radius,
# Covariance, Weight) come from a specific formula used by the tool that
# built our original training dataset (CICFlowMeter), which isn't fully
# public. Here we use reasonable statistical approximations for those,
# clearly marked below — this is a deliberate, documented scoping decision,
# not an oversight.

import time
import statistics

# How long (in seconds) a flow can sit with no new packets before we
# consider it "finished" and calculate its final features.
FLOW_TIMEOUT_SECONDS = 5

MIN_PACKETS_FOR_CLASSIFICATION = 4

# Common ports used to guess which application-layer protocol is involved.
# Real traffic analysis tools do this the same way — by port number,
# since we're not deeply inspecting packet contents here.
PORT_TO_PROTOCOL = {
    80: "HTTP", 443: "HTTPS", 53: "DNS", 23: "Telnet",
    25: "SMTP", 22: "SSH", 194: "IRC", 67: "DHCP", 68: "DHCP",
}


class Flow:
    """
    Represents one ongoing conversation between two IP addresses.
    Every packet that belongs together (same two IPs, same protocol)
    gets added to the same Flow object, and we keep updating its
    statistics as new packets arrive.
    """

    def __init__(self, ip_a, ip_b, protocol):
        self.ip_a = ip_a          # the IP that sent the FIRST packet (the "source")
        self.ip_b = ip_b          # the other IP involved
        self.protocol = protocol  # "TCP", "UDP", "ICMP", etc.

        self.start_time = time.time()
        self.last_seen = time.time()

        # Separate lists for each direction, so we can calculate
        # source-rate vs destination-rate separately later.
        self.forward_sizes = []   # packets FROM ip_a TO ip_b
        self.backward_sizes = []  # packets FROM ip_b TO ip_a

        self.ttls = []            # Time-To-Live values seen (approximates "Duration")
        self.timestamps = []      # when each packet arrived (for IAT calculation)

        # Flag tracking: which TCP flags appeared, and how many times each did
        self.flags_seen = set()          # e.g. {"SYN", "ACK"} — for the *_flag_number fields
        self.flag_counts = {              # for the *_count fields
            "ACK": 0, "SYN": 0, "FIN": 0, "URG": 0, "RST": 0,
        }

        self.ports_seen = set()   # used to guess HTTP/HTTPS/DNS/etc.
        self.protocols_seen = set()  # e.g. {"TCP"}, used for TCP/UDP/ICMP indicator flags

    def add_packet(self, src_ip, size, ttl, tcp_flags=None, port=None, proto_name=None):
        """
        Called every time a new packet belonging to this flow arrives.
        Updates all our running statistics.
        """
        self.last_seen = time.time()
        self.timestamps.append(self.last_seen)
        self.ttls.append(ttl)

        if proto_name:
            self.protocols_seen.add(proto_name)

        if port and port in PORT_TO_PROTOCOL:
            self.ports_seen.add(PORT_TO_PROTOCOL[port])

        # Which direction is this packet going?
        if src_ip == self.ip_a:
            self.forward_sizes.append(size)
        else:
            self.backward_sizes.append(size)

        if tcp_flags:
            for flag in tcp_flags:
                self.flags_seen.add(flag)
                if flag in self.flag_counts:
                    self.flag_counts[flag] += 1

    def is_expired(self):
        """True if this flow has been quiet long enough to consider it done."""
        return (time.time() - self.last_seen) > FLOW_TIMEOUT_SECONDS

    def compute_features(self) -> dict:
        """
        Calculates the final 46-feature dictionary for this completed flow,
        in the SAME column order our model was trained on.
        """
        all_sizes = self.forward_sizes + self.backward_sizes
        number_of_packets = len(all_sizes)

        duration = self.last_seen - self.start_time
        duration = max(duration, 0.001)  # avoid dividing by zero for very short flows

        # --- Basic rate calculations ---
        rate = number_of_packets / duration
        srate = len(self.forward_sizes) / duration   # source -> destination rate
        drate = len(self.backward_sizes) / duration  # destination -> source rate

        # --- Inter-arrival time: average gap between consecutive packets ---
        if len(self.timestamps) > 1:
            gaps = [self.timestamps[i] - self.timestamps[i - 1] for i in range(1, len(self.timestamps))]
            iat = statistics.mean(gaps)
        else:
            iat = 0.0

        # --- Packet size statistics ---
        avg_size = statistics.mean(all_sizes) if all_sizes else 0
        std_size = statistics.pstdev(all_sizes) if len(all_sizes) > 1 else 0
        variance_size = statistics.pvariance(all_sizes) if len(all_sizes) > 1 else 0

        # --- APPROXIMATIONS for the complex CICFlowMeter-specific fields ---
        # Magnitude: original formula isn't public; we approximate as the
        # square root of the average packet size, a common way to express
        # "typical scale" of a flow's traffic.
        magnitude = avg_size ** 0.5

        # Radius: approximated as the square root of the size variance —
        # represents how "spread out" the packet sizes are.
        radius = variance_size ** 0.5

        # Covariance: how forward and backward packet sizes vary together.
        # If there's no two-way traffic, this is 0 (nothing to compare).
        if len(self.forward_sizes) > 1 and len(self.backward_sizes) > 1:
            n = min(len(self.forward_sizes), len(self.backward_sizes))
            try:
                covariance = statistics.covariance(self.forward_sizes[:n], self.backward_sizes[:n])
            except statistics.StatisticsError:
                covariance = 0.0
        else:
            covariance = 0.0

        # Weight: approximated as a simple function of packet count —
        # a rough proxy for "how substantial" this flow is.
        weight = number_of_packets ** 0.5 * 10

        protocol_number_map = {"TCP": 6, "UDP": 17, "ICMP": 1}

        features = {
            "flow_duration": duration,
            "Header_Length": 54.0,  # approximated as a typical header size (bytes)
            "Protocol Type": protocol_number_map.get(self.protocol, 0),
            "Duration": statistics.mean(self.ttls) if self.ttls else 64.0,  # approximates TTL
            "Rate": rate,
            "Srate": srate,
            "Drate": drate,
            "fin_flag_number": 1 if "FIN" in self.flags_seen else 0,
            "syn_flag_number": 1 if "SYN" in self.flags_seen else 0,
            "rst_flag_number": 1 if "RST" in self.flags_seen else 0,
            "psh_flag_number": 1 if "PSH" in self.flags_seen else 0,
            "ack_flag_number": 1 if "ACK" in self.flags_seen else 0,
            "ece_flag_number": 0,  # rarely used in practice; default to absent
            "cwr_flag_number": 0,
            "ack_count": self.flag_counts["ACK"],
            "syn_count": self.flag_counts["SYN"],
            "fin_count": self.flag_counts["FIN"],
            "urg_count": self.flag_counts["URG"],
            "rst_count": self.flag_counts["RST"],
            "HTTP": 1 if "HTTP" in self.ports_seen else 0,
            "HTTPS": 1 if "HTTPS" in self.ports_seen else 0,
            "DNS": 1 if "DNS" in self.ports_seen else 0,
            "Telnet": 1 if "Telnet" in self.ports_seen else 0,
            "SMTP": 1 if "SMTP" in self.ports_seen else 0,
            "SSH": 1 if "SSH" in self.ports_seen else 0,
            "IRC": 1 if "IRC" in self.ports_seen else 0,
            "TCP": 1 if "TCP" in self.protocols_seen else 0,
            "UDP": 1 if "UDP" in self.protocols_seen else 0,
            "DHCP": 1 if "DHCP" in self.ports_seen else 0,
            "ARP": 1 if "ARP" in self.protocols_seen else 0,
            "ICMP": 1 if "ICMP" in self.protocols_seen else 0,
            "IPv": 1,  # every flow we track has an IP layer by definition
            "LLC": 0,  # not applicable to standard IP traffic; default 0
            "Tot sum": sum(all_sizes),
            "Min": min(all_sizes) if all_sizes else 0,
            "Max": max(all_sizes) if all_sizes else 0,
            "AVG": avg_size,
            "Std": std_size,
            "Tot size": sum(all_sizes),
            "IAT": iat,
            "Number": number_of_packets,
            "Magnitue": magnitude,   # matches the (misspelled) column name in the original dataset
            "Radius": radius,
            "Covariance": covariance,
            "Variance": variance_size,
            "Weight": weight,
        }
        return features


class FlowManager:
    """
    Keeps track of ALL currently active flows at once. This is the object
    our Scapy packet handler will talk to directly.
    """

    def __init__(self):
        self.flows = {}  # key: (ip_a, ip_b, protocol) -> Flow object

    def _make_key(self, ip1, ip2, protocol):
        # Sorting the two IPs means (A, B) and (B, A) map to the SAME key,
        # so packets going in either direction land in the same flow.
        sorted_ips = tuple(sorted([ip1, ip2]))
        return (sorted_ips[0], sorted_ips[1], protocol)

    def process_packet(self, src_ip, dst_ip, size, ttl, protocol, tcp_flags=None, port=None):
        key = self._make_key(src_ip, dst_ip, protocol)

        if key not in self.flows:
            # First packet of a brand new flow — ip_a is whoever sent it first.
            self.flows[key] = Flow(src_ip, dst_ip, protocol)

        self.flows[key].add_packet(src_ip, size, ttl, tcp_flags, port, protocol)

    def get_expired_flows(self):
        """
        Returns a list of (key, Flow) pairs for flows that have gone quiet
        long enough to be considered finished, AND removes them from
        active tracking (so we don't process the same flow twice).
        """
        expired = []
        for key in list(self.flows.keys()):
            if self.flows[key].is_expired():
                expired.append(self.flows.pop(key))
        return expired
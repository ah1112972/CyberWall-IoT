import json

class NetworkPacket:
    def __init__(self, src_ip, dst_ip, protocol, size):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.protocol = protocol
        self.size = size

    def classify(self):
        if self.size > 8000:
            return "THREAT"
        elif self.size > 1000:
            return "Warning"
        else:
            return "Safe"  

    def to_dict(self):
        return {
            "src_ip":  self.src_ip,
            "dst_ip":  self.dst_ip,
            "protocol":  self.protocol,
            "size":  self.size,
            "status": self.classify()
        }

#save packets to json file

def save_logs(packets, filename):
    logs = []
    for packet in packets:
        logs.append(packet.to_dict())

    with open(filename, "w") as file:
        json.dump(logs, file, indent=4)
    print(f"\nsaved {len(logs)} packets to {filename}")

#load json file and error handling

def load_logs(filename):
    try:
        with open(filename, "r") as file:
            logs = json.load(file)
        print(f"loaded {len(logs)} packets from {filename}")
        return logs
    except FileNotFoundError:
        print("File {filename} Not Found")
        return[]
    except json.JSONDecodeError:
        print("File {filname} is corrupted!")
        return []


#Save the threats

def save_threats_only(filename):
    threats = []
    with open(filename, "r") as file:
        load_file = json.load(file)
        for entry in load_file:
            if entry["status"] == "THREAT":
                threats.append(entry)
           
        with open("threats_only.json", "w") as file:
            json.dump(threats, file, indent=4)
        print(f"Threats found: {len(threats)}")

        for entry in threats:
           print(f"{entry['status']:8} | {entry['src_ip']:15} -> {entry['dst_ip']:15} | {entry['protocol']:8} | {entry['size']} bytes")
        
        






# create packet objects — same as Day 2
p1 = NetworkPacket("192.168.1.5", "8.8.8.8",     "UDP",  512)
p2 = NetworkPacket("192.168.1.6", "192.168.1.1", "TCP",  9500)
p3 = NetworkPacket("192.168.1.7", "142.250.1.1", "TCP",  256)
p4 = NetworkPacket("10.0.0.1",    "192.168.1.5", "ICMP", 8100)

packets = [p1,p2,p3,p4]

save_logs(packets, "packet_logs.json")

print("\n Loading and displaying Saved logs")
print("=" * 50)

loaded = load_logs("packet_logs.json")
for entry in loaded:
    print(f"{entry["status"]:8} | {entry["src_ip"]:15} -> {entry["dst_ip"]:15} | {entry["protocol"]:8} | {entry["size"]} \n")

save_threats_only("packet_logs.json")

    


print("=" * 40)
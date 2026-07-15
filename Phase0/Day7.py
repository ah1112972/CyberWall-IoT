
import socket
import json
from scapy.all import sniff, IP, TCP, UDP, ICMP 

captured_packets = []



def handle_packets(packet):

    if IP in packet:

        src_ip = packet[IP].src
        dst_ip = packet[IP].src
        protocol = 'OTHER'
        size = len(packet)

        if TCP in packet:
            protocol = 'TCP'
        elif UDP in packet:
            protocol = 'UDP'
        elif ICMP in packet:
            protocol = 'ICMP'


        # reverse DNS lookup — find domain name for destination IP
        try:
            hostname = socket.gethostbyaddr(dst_ip)[0]  
        except socket.herror:               
            hostname = 'unknown'              



        if size > 8000:
            status = "🚨 THREAT"    # large packet is suspicious
        elif size > 1000:
            status = "⚠️  WARNING"  # medium packet gets warning
        else:
            status = "✅ SAFE"      # small packet is normal

        # print packet details in a clean format
        print(f"{status:15} | {src_ip:15} → {dst_ip:15} | {hostname:35} | {protocol:5} | {size} bytes")



        packet_dict = {
            "src_ip":   src_ip,         # source IP
            "dst_ip":   dst_ip,         # destination IP
            "hostname": hostname,       # domain name
            "protocol": protocol,       # protocol type
            "size":     size,           # packet size
            "status":   status          # classification
        }

        captured_packets.append(packet_dict) 







#Start capturating....

print("=" * 65)
print("   CyberWall IoT — Live Packet Capture v0.1")
print("=" * 65)
print("Starting capture... Press Ctrl+C to stop\n")

sniff(
    iface="Intel(R) Wi-Fi 6 AX201 160MHz",
    filter = 'ip',
    prn = handle_packets,
    store = False,
    count = 50
)


with open("live_capture.json", "w") as file:        
    json.dump(captured_packets, file, indent=4)      

print(f"\n✅ Saved {len(captured_packets)} packets to live_capture.json")
print("=" * 65)

print("\n" + "=" * 65)
print("Capture complete!")
print("=" * 65)
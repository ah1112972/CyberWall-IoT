class NetworkPacket:
    def __init__(self, src_ip, dst_ip, protocol, size):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.protocol = protocol
        self.size = size

    def classify(self):
        if self.size > 8000:
            return "Threat"
        elif self.size > 1000:
            return "Warning"
        else:
            return "Safe"

    def display(self):
        Status = self.classify()
        print(f"{Status:10} | {self.src_ip:15} -> {self.dst_ip:15} | {self.protocol} | {self.size} bytes")

    def is_internal(self):
        if self.src_ip.startswith('192.168'):
            return True
        else:
            return False
        

p1 = NetworkPacket("192.168.1.5", "8.8.8.8",      "UDP",  512)
p2 = NetworkPacket("192.168.1.6", "192.168.1.1",  "TCP",  9500)
p3 = NetworkPacket("192.168.1.7", "142.250.1.1",  "TCP",  256)
p4 = NetworkPacket("10.0.0.1",    "192.168.1.5",  "ICMP", 8100)

packets = [p1,p2,p3,p4]

print("=" * 50)
print("CyberWall IoT, Packet Analyzer v0.2")
print("=" * 50)

c_threats = 0
c_warning = 0
c_safe = 0

for packet in packets:

    packet.display()

    if packet.is_internal():
       print("   └─ Source: Internal 🏠")
    else:
        print("   └─ Source: External 🌐")


    status = packet.classify()

    if status == 'Threat':
        c_threats += 1
    if status == 'Warning':
        c_warning += 1
    if status == 'Safe':
        c_safe += 1
        
   

print('=' * 50)

print('Total packets:  ', len(packets))
print('Threats:        ', c_threats)
print('Warning:        ', c_warning)
print('Safe packets:   ', c_safe)
print('=' * 50)

name = "Altaf Hussain"
age = 24
city = "Lahore"
Cgpa = 3.50

print(name, age, city, Cgpa)
print(f"My name is",name,"And I am",age,"year old.")

Devices =  ["Camera", "router", "smart-TV", "thermostate"]
print(Devices[0])
print(Devices[-1])
print(len(Devices))
Devices.append ("Laptops")
print(Devices)
print("-----------------------------------------------------")
print()

#Mapping

packet = {
    "src_ip": "192.168.1.5",
    "dst_ip": "8.8.8.8",
    "protocol": "TCP",
    "size": "1024"
}

print(packet["src_ip"])
print(packet.get("port", 0))
print()

size = 1024
if size > 8000:
    print("Alert: Suspiciously large packet!")

if size > 1000:
    print("Warning: Large packet, Monitoring...")

else:
    print("Normal packet size")

print()

devices = ["camera", "router", "smart_tv", "thermostat", "laptop"]
for device in devices:
    print(f"Monitoring Device", device)
print()

for i, device in enumerate(devices):
    print(i, device)
print()

def classify_packet(size):
    if size>8000:
        return "🚨 Threat"
    
    elif size>1000:
        return "⚠️ Warning"
    else:
        return "✅ safe"
    input()

#size = int(input("Enter The Size of packet: "))
print(classify_packet(1024))
print()
print('=====================================================')
print()

packets = [
    {"src_ip": "192.168.1.5", "dst_ip": "8.8.8.8",     "size": 512,  "protocol": "UDP"},
    {"src_ip": "192.168.1.6", "dst_ip": "192.168.1.1",  "size": 9500, "protocol": "TCP"},
    {"src_ip": "192.168.1.7", "dst_ip": "142.250.1.1",  "size": 256,  "protocol": "TCP"},
    {"src_ip": "10.0.0.1",    "dst_ip": "192.168.1.5",  "size": 8100, "protocol": "ICMP"},
]


def classify_packet(size):
    if size>8000:
        return "Threat"
    
    elif size>1000:
        return "Warning"
    else:
        return "Safe"
    input()

print('=' * 50)
print('CyberWall IoT -Packet analyzer version v0.1')
print('=' * 50)

c_threats = 0
c_warning = 0
c_safe = 0

for packet in packets:
    status = classify_packet(packet['size'])
    print(f"{status:8} | {packet['src_ip']:15} → {packet['dst_ip']:15} | {packet['protocol']} | {packet['size']} bytes")
    if status == 'Threat':
        c_threats += 1
    elif status == 'Warning':
        c_warning += 1
    else:
        c_safe += 1

print("=" * 50)
print(f"Total packets analyzed: {len(packets)}")
print("Number of Threats: ", c_threats, "\nNumber of Warnings: ", c_warning, "\nNumber of Safe packets: ", c_safe)






    
    


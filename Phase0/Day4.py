#Mini CyberWall CLI App

import json

class NetworkPacket:
    def __init__(self, src_ip, dst_ip, protocol,size):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.protocol = protocol
        self.size = size

    def classify(self):
        if self.size > 8000:
            return "THREAT"
        elif self.size > 1000:
            return "WARNING"
        else:
            return "SAFE"
        
    def to_dict(self):
        return{
        "src_ip":    self.src_ip,
        "dst_ip":    self.dst_ip,
        "protocol":  self.protocol,
        "size":      self.size,
        "status":    self.classify()
    }


#Create file, read_fileand save json_file

def save_logs(packets, filename):
    logs = []
    for packet in packets:
        logs.append(packet.to_dict())

    with open(filename, "w") as file:
        json.dump(logs, file, indent=4)
    print(f"Saved {len(logs)} packets in {filename}")

#Load_json_file

def load_logs(filename):
    try:
        with open(filename, "r") as file:
            logs = json.load(file)
        print(f"{len(logs)} packets loaded")
        return logs
    except FileNotFoundError:
        print(f"{filename} not found!")
        return[]
    except json.JSONDecodeError:
        print(f"{filename} is corrupted!")
        return []
    


#Display all the packets table

def display(packets):
    if len(packets) == 0:
        print("No packet found")
        return 
    
    print('=' * 70)
    print(f"{'STATUS:':8} | {'SRC_IP':15} | {'DST_IP':15} | {'PROTOCOL':10} | {'SIZE':}")
    print('=' * 70)

    for p in packets:
        print(f"{p['status']:8} | {p['src_ip']:15} | {p['dst_ip']:15} | {p['protocol']:10} | {p['size']} Bytes")




#Add new packets

def add_packets(all_packets):
    print("\nAdd New Packet")
    src_ip = input("Enter Saurce IP: ")
    dst_ip = input("Enter Destination IP: ")
    protocol = input("Protocol")
    
    while True:
        try:
            size = int(input("Enter The Size of the Packet (Bytes): "))
            break 
        except ValueError:
            print("Invalid Size - Enter a number.")

    packet = NetworkPacket(src_ip, dst_ip, protocol, size)
    packet_dict = packet.to_dict()
    all_packets.append(packet_dict)

    save_logs(all_packets, "packet_logs.json")
    print(f"\n Packet added - Status: {packet_dict['status']}")
    return all_packets



def main():


    print('=' * 60)
    print("CyberWall IoT - Packet Monitoring v0.3")
    print('=' * 60)

    p1 = NetworkPacket("192.168.1.5", "8.8.8.8",     "UDP",  512)
    p2 = NetworkPacket("192.168.1.6", "192.168.1.1", "TCP",  9500)
    p3 = NetworkPacket("192.168.1.7", "142.250.1.1", "TCP",  256)
    p4 = NetworkPacket("10.0.0.1",    "192.168.1.5", "ICMP", 8100)
    packets = [p1,p2,p3,p4]
    save_logs(packets, "packet_logs.json")

    all_packets = load_logs("packet_logs.json")
    print(f"\nLoaded {len(all_packets)} existing packets from logs")


    while True:
        print("\n---Menu---\n")
        print("1 - Add a packet")
        print("2 - View all Packets")
        print("3 - View Threats only")
        print("4 - Clear all logs")
        print("5 - Exit")

        choice = input("\nEnter Your Choice (1-4): ")
        
        if choice == '1':
            all_packets = add_packets(all_packets)
        
        elif choice == '2':
            display(all_packets)
        
        elif choice == '3':
            threats = [p for p in all_packets if p["status"] == "THREAT"]
            display(threats)
            
        elif choice == '4':
            confirm = input("Are You Sure (y/n): ")
            if confirm == 'y':
                all_packets = []
                save_logs(all_packets, "packet_logs.json")
            elif confirm == 'n':
                print("ok")


                                        
        elif choice == '5':
            print("\n CyberWall IoT Shutting Down. Goodbye!")

        else:
            print("invalid choice! Enter 1, 2, 3, or 4 ")
main()
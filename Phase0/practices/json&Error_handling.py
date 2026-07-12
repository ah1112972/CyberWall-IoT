#Phase 0A — Day 3: File I/O, JSON & Error Handling
import json


with open("packets.txt", "w") as file:         #open file for writing
    file.write("Hello CyberWall\n")

with open("packets.txt", "r") as file:          #open file for read
    content = file.read()
    print(content)

# with open("packets.txt", "r") as file:    # open file for reading
#     for line in file:                      # loop through each line one by one
#         print(line.strip())                # strip() removes the \n at end of each line

print("=" * 50)

#json

packet_data = {
    "src_ip":   "192.168.1.6",         
    "dst_ip":   "192.168.1.1",         
    "protocol": "TCP",                  
    "size":     9500,                   
    "status":   "THREAT"              
}

with open("packet_log.json", "w") as file:
    json.dump(packet_data, file, indent=4)



with open("packet_log.json", "r") as file:
    loaded_data = json.load(file)
    
print(loaded_data)
print(loaded_data["src_ip"])
print(loaded_data["status"])   


#Error handling try/except

try:
    with open("packet_log.json", "r") as file:
        load = json.load(file)

except FileNotFoundError:
    print("Log file not found -starting fresh")

except json.JSONDecoderError:
    print("Log file is corrupted")

    


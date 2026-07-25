# label_mapping.py
# Purpose: Map the 34 fine-grained CICIoT2023 labels down to 8 broad
# categories (Benign + 7 attack types), fixing the severe class imbalance

import pandas as pd

# --- The mapping table ---

label_to_category = {
    # Benign
    "BenignTraffic": "Benign",

    # DDoS
    "DDoS-ICMP_Flood": "DDoS",
    "DDoS-UDP_Flood": "DDoS",
    "DDoS-TCP_Flood": "DDoS",
    "DDoS-PSHACK_Flood": "DDoS",
    "DDoS-SYN_Flood": "DDoS",
    "DDoS-RSTFINFlood": "DDoS",
    "DDoS-SynonymousIP_Flood": "DDoS",
    "DDoS-ICMP_Fragmentation": "DDoS",
    "DDoS-UDP_Fragmentation": "DDoS",
    "DDoS-ACK_Fragmentation": "DDoS",
    "DDoS-HTTP_Flood": "DDoS",
    "DDoS-SlowLoris": "DDoS",

    # DoS
    "DoS-UDP_Flood": "DoS",
    "DoS-TCP_Flood": "DoS",
    "DoS-SYN_Flood": "DoS",
    "DoS-HTTP_Flood": "DoS",

    # Mirai (botnet)
    "Mirai-greeth_flood": "Mirai",
    "Mirai-udpplain": "Mirai",
    "Mirai-greip_flood": "Mirai",

    # Recon (reconnaissance / scanning)
    "Recon-HostDiscovery": "Recon",
    "Recon-OSScan": "Recon",
    "Recon-PortScan": "Recon",
    "Recon-PingSweep": "Recon",
    "VulnerabilityScan": "Recon",

    # Spoofing
    "MITM-ArpSpoofing": "Spoofing",
    "DNS_Spoofing": "Spoofing",

    # Web-based attacks
    "BrowserHijacking": "Web",
    "SqlInjection": "Web",
    "CommandInjection": "Web",
    "Backdoor_Malware": "Web",
    "XSS": "Web",
    "Uploading_Attack": "Web",

    # Brute force
    "DictionaryBruteForce": "BruteForce",
}


def add_category_column(df: pd.DataFrame) -> pd.DataFrame:
  
    # .map() looks up each row's label in our dictionary and replaces it —
    # similar to calling my_map[label] for every element of a vector in C++.
    df["category"] = df["label"].map(label_to_category)

    # Safety check: if any label wasn't in our dictionary, .map() would have
    # produced NaN (missing value) instead of crashing.
    missing = df["category"].isna().sum()
    if missing > 0:
        unmapped_labels = df.loc[df["category"].isna(), "label"].unique()
        print(f"WARNING: {missing} rows had unmapped labels: {unmapped_labels}")

    return df


if __name__ == "__main__":
    
    df = pd.read_csv("data/raw/validation.csv")
    df = add_category_column(df)

    print("New category distribution:")
    print(df["category"].value_counts())

    print("\nNew category distribution (percentages):")
    print((df["category"].value_counts(normalize=True) * 100).round(2))
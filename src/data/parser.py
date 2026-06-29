import json
import os
from typing import Dict, Any, List

def parse_zeek_log(filepath: str) -> List[Dict[str, Any]]:
    """
    Parses a Zeek format log (e.g., conn.log, http.log, dns.log) into structured JSON.
    Format: {timestamp, src_ip, dst_ip, protocol, payload_snippet, ground_truth_technique_id}
    """
    parsed_logs = []
    
    if not os.path.exists(filepath):
        print(f"Warning: File {filepath} not found.")
        return parsed_logs

    # This is a stub implementation. Real Zeek parsing depends on the specific
    # tab-separated values format used by Zeek.
    # The OPTC dataset provides headers in the first few lines starting with #.
    
    with open(filepath, 'r') as f:
        headers = []
        for line in f:
            if line.startswith('#fields'):
                headers = line.strip().split('\t')[1:]
                continue
            if line.startswith('#'):
                continue
            
            parts = line.strip().split('\t')
            if len(parts) == len(headers):
                log_entry = dict(zip(headers, parts))
                
                # Extract requested fields (mapping Zeek fields to standard names)
                parsed_entry = {
                    "timestamp": log_entry.get("ts", ""),
                    "src_ip": log_entry.get("id.orig_h", ""),
                    "dst_ip": log_entry.get("id.resp_h", ""),
                    "protocol": log_entry.get("proto", ""),
                    "payload_snippet": "", # Extract from URI/query depending on log type
                    "ground_truth_technique_id": None # To be mapped based on OPTC scenario data
                }
                
                if "query" in log_entry: # DNS
                    parsed_entry["payload_snippet"] = log_entry["query"]
                elif "uri" in log_entry: # HTTP
                    parsed_entry["payload_snippet"] = log_entry["uri"]
                    
                parsed_logs.append(parsed_entry)
                
    return parsed_logs

if __name__ == "__main__":
    # Example usage (uncomment when testing with real data):
    # logs = parse_zeek_log("../../data/raw/dns.log")
    # with open("../../data/processed/parsed_logs.json", "w") as out:
    #     json.dump(logs, out, indent=2)
    pass

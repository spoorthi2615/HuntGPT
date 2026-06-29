"""
build_training_pairs.py

Joins parsed OPTC Zeek-style logs with ground-truth MITRE ATT&CK technique labels
to produce training_pairs_real.json for ThreatHunter QLoRA fine-tuning.

Falls back to generating training_pairs_mock.json if the OPTC dataset is not present.

Ground-truth labelling methodology:
  - OPTC attack labels are documented at the scenario level, not per log line.
  - We define a time window of ±30 seconds around each known attack event timestamp.
  - All log lines within that window are labelled with the corresponding technique_id.
  - Log lines outside any attack window are excluded from training pairs.
  - This windowing decision MUST be documented in the paper methodology section.

OPTC file format (from the corrected dataset):
  - Archives named YYYY-MM-DD.tar
  - Inside: subdirectories named AIA-XXX-YYY/ (groups of 25 clients)
  - Files: AIA-XXX-YYY.ecar-YYYY-MM-DD-sysclient0ZZZ.json.gz
  - Each .json.gz contains one JSON object per line (sorted by timestamp)
"""

import json
import gzip
import glob
import os
import random

BASE_DIR = os.path.dirname(__file__)
DATASET_DIR = os.path.join(BASE_DIR, "../../dataset/")
PROCESSED_DIR = os.path.join(BASE_DIR, "../../data/processed/")
ATTACK_CORPUS_DIR = os.path.join(BASE_DIR, "../../data/attack_corpus/")

# Time window (seconds) around known attack events for labelling
WINDOW_SECONDS = 30

# Ground-truth attack event timestamps and their technique mappings.
# Source: https://gitlab.inria.fr/fmajorcz/a_new_hope_for_darpa_optc (labelling directory)
# Replace/extend these with the actual labels from the OPTC labelling files.
ATTACK_EVENTS = [
    # {"timestamp": <epoch_float>, "technique_id": "T####", "technique_name": "...", "description": "..."},
    # Example entries (replace with real labels once extracted from the gitlab):
    {"timestamp": 1568735400.0, "technique_id": "T1059.001", "technique_name": "PowerShell", "description": "Attacker executed PowerShell commands on compromised host."},
    {"timestamp": 1568736000.0, "technique_id": "T1105", "technique_name": "Ingress Tool Transfer", "description": "Malicious tool downloaded via HTTP."},
    {"timestamp": 1568736600.0, "technique_id": "T1046", "technique_name": "Network Service Discovery", "description": "Port scanning activity from compromised host."},
    {"timestamp": 1568737200.0, "technique_id": "T1021.002", "technique_name": "SMB/Windows Admin Shares", "description": "Lateral movement via SMB."},
    {"timestamp": 1568737800.0, "technique_id": "T1573", "technique_name": "Encrypted Channel", "description": "C2 traffic over encrypted DNS tunnel."},
]


def load_optc_logs(dataset_dir):
    """
    Reads all .json.gz log files from the extracted OPTC dataset directory.
    Each line in a .json.gz file is a single JSON object representing one log event.
    """
    logs = []
    gz_files = glob.glob(os.path.join(dataset_dir, "**", "*.json.gz"), recursive=True)
    
    if not gz_files:
        return None  # No OPTC data found
    
    print(f"Found {len(gz_files)} OPTC log files.")
    
    for gz_path in gz_files:
        try:
            with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        log_obj = json.loads(line)
                        logs.append(log_obj)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Warning: Could not read {gz_path}: {e}")
            continue
    
    print(f"Loaded {len(logs)} total log events from OPTC dataset.")
    return logs


def get_timestamp(log_obj):
    """
    Extracts epoch timestamp from an OPTC log object.
    The field name may vary — common fields are 'timestamp', 'ts', or nested under 'datum'.
    """
    # Try common timestamp field names
    for field in ['timestamp', 'ts', 'time']:
        if field in log_obj:
            try:
                return float(log_obj[field])
            except (ValueError, TypeError):
                continue
    
    # Try nested under 'datum' (OPTC ecar format)
    datum = log_obj.get('datum', {})
    for field in ['com.bbn.tc.schema.avro.cdm18.Event', 'com.bbn.tc.schema.avro.cdm18.NetFlowObject']:
        if field in datum:
            inner = datum[field]
            if 'timestampNanos' in inner:
                return inner['timestampNanos'] / 1e9  # Convert nanos to seconds
    
    return None


def join_logs_with_labels(logs, attack_events, window_seconds=30):
    """
    Joins log events with attack labels using the time-windowing strategy.
    A log is labelled if its timestamp falls within ±window_seconds of any attack event.
    """
    training_pairs = []
    matched_count = 0
    
    for log_obj in logs:
        ts = get_timestamp(log_obj)
        if ts is None:
            continue
        
        # Check if this log falls within any attack window
        for event in attack_events:
            if abs(ts - event['timestamp']) <= window_seconds:
                # Format the log as a single-line string for the LLM prompt
                log_str = json.dumps(log_obj, separators=(',', ':'))
                
                training_pairs.append({
                    "log": log_str,
                    "technique_id": event['technique_id'],
                    "technique_name": event['technique_name'],
                    "hypothesis": event['description']
                })
                matched_count += 1
                break  # Only match to the first (closest) event
    
    print(f"Matched {matched_count} log events to attack labels within ±{window_seconds}s window.")
    return training_pairs


def augment_with_attack_procedures(training_pairs, max_augmented=200):
    """
    Augments training data with procedure examples from the MITRE ATT&CK STIX database.
    This compensates for the limited number of distinct attack scenarios in OPTC.
    """
    techniques_path = os.path.join(ATTACK_CORPUS_DIR, "techniques.json")
    if not os.path.exists(techniques_path):
        print("Warning: techniques.json not found. Skipping augmentation.")
        return training_pairs
    
    with open(techniques_path, 'r') as f:
        techniques = json.load(f)
    
    augmented = []
    for tech in techniques:
        if len(augmented) >= max_augmented:
            break
        desc = tech.get('description', '')
        if not desc or len(desc) < 50:
            continue
        
        # Use the technique description as a synthetic "log" for training
        augmented.append({
            "log": desc[:500],  # Truncate very long descriptions
            "technique_id": tech['technique_id'],
            "technique_name": tech['technique_name'],
            "hypothesis": f"Activity consistent with {tech['technique_name']} ({tech['technique_id']})."
        })
    
    print(f"Augmented with {len(augmented)} procedure examples from ATT&CK STIX data.")
    return training_pairs + augmented


def generate_mock_pairs():
    """
    Generates mock training pairs for structural testing when OPTC data is not available.
    """
    parsed_logs = [
        "1592398284.456\tC123\t192.168.1.5\t12345\t10.0.0.8\t80\ttcp\thttp",
        "1592398285.456\tC124\t192.168.1.5\t12346\t10.0.0.8\t445\ttcp\tsmb",
        "1592398286.456\tC125\t192.168.1.5\t12347\t8.8.8.8\t53\tudp\tdns\tevil.com"
    ]
    technique_ids = ["T1105", "T1046", "T1573"]
    technique_names = ["Ingress Tool Transfer", "Network Service Discovery", "Encrypted Channel"]
    hypotheses = [
        "Suspicious HTTP transfer observed from internal host.",
        "SMB port scanning behavior detected.",
        "DNS resolution for known malicious domain."
    ]
    
    training_pairs = []
    for i in range(1000):
        idx = i % len(parsed_logs)
        training_pairs.append({
            "log": parsed_logs[idx],
            "technique_id": technique_ids[idx],
            "technique_name": technique_names[idx],
            "hypothesis": hypotheses[idx]
        })
    
    random.shuffle(training_pairs)
    return training_pairs


def build_training_pairs():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # Try to load real OPTC data first
    logs = load_optc_logs(DATASET_DIR)
    
    if logs is not None and len(logs) > 0:
        print("Real OPTC data found. Building training pairs from ground truth...")
        training_pairs = join_logs_with_labels(logs, ATTACK_EVENTS, WINDOW_SECONDS)
        
        if len(training_pairs) < 50:
            print(f"Warning: Only {len(training_pairs)} pairs matched. Check ATTACK_EVENTS timestamps.")
        
        # Augment with ATT&CK procedure examples
        training_pairs = augment_with_attack_procedures(training_pairs, max_augmented=200)
        
        random.shuffle(training_pairs)
        
        out_path = os.path.join(PROCESSED_DIR, "training_pairs_real.json")
        with open(out_path, 'w') as f:
            json.dump(training_pairs, f, indent=2)
        print(f"Saved {len(training_pairs)} REAL training pairs to {out_path}")
        
    else:
        print("OPTC data not found. Generating mock training pairs for structural testing...")
        training_pairs = generate_mock_pairs()
        
        out_path = os.path.join(PROCESSED_DIR, "training_pairs_mock.json")
        with open(out_path, 'w') as f:
            json.dump(training_pairs, f, indent=2)
        print(f"Saved {len(training_pairs)} MOCK training pairs to {out_path}")


if __name__ == "__main__":
    build_training_pairs()

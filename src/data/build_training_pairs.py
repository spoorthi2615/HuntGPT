import json
import os
import random

PROCESSED_DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/processed/")

def build_training_pairs():
    """
    Simulates reading parsed Zeek logs and joining them with OPTC ground-truth labels.
    In reality, this would join actual parsed OPTC logs with their provided technique IDs.
    """
    
    # Example raw inputs
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
    
    # Generate mock training pairs for Colab
    training_pairs = []
    
    for i in range(1000): # Simulating 1000 rows
        idx = i % len(parsed_logs)
        training_pairs.append({
            "log": parsed_logs[idx],
            "technique_id": technique_ids[idx],
            "technique_name": technique_names[idx],
            "hypothesis": hypotheses[idx]
        })
        
    random.shuffle(training_pairs)
    
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    out_path = os.path.join(PROCESSED_DATA_DIR, "training_pairs.json")
    
    with open(out_path, 'w') as f:
        json.dump(training_pairs, f, indent=2)
        
    print(f"Generated {len(training_pairs)} training pairs and saved to {out_path}")

if __name__ == "__main__":
    build_training_pairs()

import json
import urllib.request
import os

ATTACK_STIX_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../../data/attack_corpus/techniques.json")

def fetch_and_parse_attack_data():
    print(f"Fetching MITRE ATT&CK data from {ATTACK_STIX_URL}...")
    try:
        with urllib.request.urlopen(ATTACK_STIX_URL) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    techniques = []
    
    # Parse STIX 2.1 JSON
    for obj in data.get("objects", []):
        if obj.get("type") == "attack-pattern":
            # Extract technique ID
            external_references = obj.get("external_references", [])
            technique_id = None
            for ref in external_references:
                if ref.get("source_name") == "mitre-attack":
                    technique_id = ref.get("external_id")
                    break
            
            kill_chain_phases = obj.get("kill_chain_phases", [])
            tactics = [phase.get("phase_name") for phase in kill_chain_phases if phase.get("kill_chain_name") == "mitre-attack"]
            
            if technique_id:
                techniques.append({
                    "technique_id": technique_id,
                    "technique_name": obj.get("name", ""),
                    "description": obj.get("description", ""),
                    "tactics": tactics,
                    "procedure_examples": [] # Could be enriched from relationship objects if needed
                })

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(techniques, f, indent=2)
        
    print(f"Successfully extracted {len(techniques)} techniques to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_and_parse_attack_data()

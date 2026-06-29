import os
import json
import time
import torch
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import warnings

warnings.filterwarnings("ignore")

CORPUS_PATH = os.path.join(os.path.dirname(__file__), "../../data/injection_corpus/test.json")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "../../models/promptguard/")

def load_test_data():
    if not os.path.exists(CORPUS_PATH):
        raise FileNotFoundError(f"Injection corpus not found at {CORPUS_PATH}")
    with open(CORPUS_PATH, 'r') as f:
        data = json.load(f)
    return data

def eval_keyword_baseline(test_data):
    keywords = ["ignore", "previous", "instructions", "system prompt", "override"]
    preds = []
    labels = []
    
    start = time.perf_counter()
    for item in test_data:
        text = item['log'].lower()
        pred = 1 if any(k in text for k in keywords) else 0
        preds.append(pred)
        labels.append(item['label'])
    elapsed = (time.perf_counter() - start) / len(test_data) * 1000
    
    return compute_metrics(labels, preds, elapsed, "Keyword Baseline")

def eval_regex_baseline(test_data):
    # Slightly more complex regex mimicking security filters
    pattern = re.compile(r"(ignore.*instructions)|(system\s+prompt)|(bypass.*security)", re.IGNORECASE)
    preds = []
    labels = []
    
    start = time.perf_counter()
    for item in test_data:
        pred = 1 if pattern.search(item['log']) else 0
        preds.append(pred)
        labels.append(item['label'])
    elapsed = (time.perf_counter() - start) / len(test_data) * 1000
    
    return compute_metrics(labels, preds, elapsed, "Regex Baseline")

def eval_promptguard(test_data):
    if not os.path.exists(MODEL_DIR):
        print("PromptGuard model not found. Skipping evaluation.")
        return None
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    
    preds = []
    labels = []
    
    # Process in batches for realistic latency
    batch_size = 16
    total_time = 0
    
    with torch.no_grad():
        for i in range(0, len(test_data), batch_size):
            batch = test_data[i:i+batch_size]
            texts = [item['log'] for item in batch]
            batch_labels = [item['label'] for item in batch]
            
            start = time.perf_counter()
            inputs = tokenizer(texts, padding=True, truncation=True, max_length=256, return_tensors="pt").to(device)
            outputs = model(**inputs)
            logits = outputs.logits
            batch_preds = torch.argmax(logits, dim=1).cpu().numpy().tolist()
            elapsed = time.perf_counter() - start
            total_time += elapsed
            
            preds.extend(batch_preds)
            labels.extend(batch_labels)
            
    avg_latency = (total_time / len(test_data)) * 1000
    return compute_metrics(labels, preds, avg_latency, "PromptGuard")

def compute_metrics(labels, preds, latency_ms, name):
    p = precision_score(labels, preds, zero_division=0)
    r = recall_score(labels, preds, zero_division=0)
    f1 = f1_score(labels, preds, zero_division=0)
    
    tn, fp, fn, tp = confusion_matrix(labels, preds).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    return {
        "name": name,
        "precision": p,
        "recall": r,
        "f1": f1,
        "fpr": fpr,
        "latency": latency_ms
    }

def print_table(results):
    print(f"\n{'Model':<20} | {'Precision':<10} | {'Recall':<10} | {'F1':<10} | {'FPR':<10} | {'Latency/batch (ms)':<15}")
    print("-" * 85)
    for res in results:
        if res:
            print(f"{res['name']:<20} | {res['precision']:.4f}     | {res['recall']:.4f}     | {res['f1']:.4f}     | {res['fpr']:.4f}     | {res['latency']:.2f}")
    print()

if __name__ == "__main__":
    print("Loading test data...")
    test_data = load_test_data()
    print(f"Loaded {len(test_data)} test samples.\n")
    
    res_kw = eval_keyword_baseline(test_data)
    res_rx = eval_regex_baseline(test_data)
    res_pg = eval_promptguard(test_data)
    
    results = [res_pg, res_kw, res_rx]
    print_table(results)

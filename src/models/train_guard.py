import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from accelerate import Accelerator
import numpy as np

MODEL_NAME = "microsoft/deberta-v3-small"
CORPUS_DIR = os.path.join(os.path.dirname(__file__), "../../data/injection_corpus/")
SAVE_DIR = os.path.join(os.path.dirname(__file__), "../../models/promptguard/")

class PromptInjectionDataset(Dataset):
    def __init__(self, data, tokenizer, max_length=256):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = item['log']
        label = item['label']
        
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def load_data():
    train_path = os.path.join(CORPUS_DIR, "train.json")
    val_path = os.path.join(CORPUS_DIR, "val.json")
    
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Injection corpus not found at {train_path}")
        
    with open(train_path, 'r') as f:
        train_data = json.load(f)
    with open(val_path, 'r') as f:
        val_data = json.load(f)
        
    return train_data, val_data

def compute_class_weights_and_sampler(train_data):
    labels = [d['label'] for d in train_data]
    class_counts = np.bincount(labels)
    class_weights = 1. / class_counts
    sample_weights = np.array([class_weights[l] for l in labels])
    
    sampler = WeightedRandomSampler(
        weights=torch.from_numpy(sample_weights).double(),
        num_samples=len(sample_weights),
        replacement=True
    )
    return sampler

def train():
    accelerator = Accelerator()
    
    # Initialize tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
    
    train_data, val_data = load_data()
    
    train_dataset = PromptInjectionDataset(train_data, tokenizer)
    val_dataset = PromptInjectionDataset(val_data, tokenizer)
    
    # Handle class imbalance
    sampler = compute_class_weights_and_sampler(train_data)
    
    train_dataloader = DataLoader(train_dataset, batch_size=16, sampler=sampler)
    val_dataloader = DataLoader(val_dataset, batch_size=16, shuffle=False)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    
    # Prepare with accelerate
    model, optimizer, train_dataloader, val_dataloader = accelerator.prepare(
        model, optimizer, train_dataloader, val_dataloader
    )
    
    epochs = 3
    
    print("Starting PromptGuard Training...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for step, batch in enumerate(train_dataloader):
            optimizer.zero_grad()
            outputs = model(**batch)
            loss = outputs.loss
            accelerator.backward(loss)
            optimizer.step()
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{epochs} | Loss: {total_loss/len(train_dataloader):.4f}")
        
    print("Training complete. Saving checkpoint...")
    
    # Unwrap and save model and tokenizer
    unwrapped_model = accelerator.unwrap_model(model)
    os.makedirs(SAVE_DIR, exist_ok=True)
    unwrapped_model.save_pretrained(SAVE_DIR)
    tokenizer.save_pretrained(SAVE_DIR)
    
    print(f"PromptGuard model and tokenizer saved to {SAVE_DIR}")

if __name__ == "__main__":
    train()

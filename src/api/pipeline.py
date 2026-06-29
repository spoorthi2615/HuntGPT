import os
import json
import logging
import requests
import torch
from typing import List
from .schemas import AnalysisResult
from ..models.scorer import get_majority_vote_and_confidence

logger = logging.getLogger(__name__)

USE_FINETUNED = os.getenv("USE_FINETUNED_MODEL", "false").lower() == "true"

# Global model variables
model = None
tokenizer = None

if USE_FINETUNED:
    logger.info("Loading fine-tuned LoRA adapter...")
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    
    bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
    base = AutoModelForCausalLM.from_pretrained(
        "mistralai/Mistral-7B-Instruct-v0.2",
        quantization_config=bnb_config, 
        device_map="auto"
    )
    
    adapter_path = os.path.join(os.path.dirname(__file__), "../../models/threathunter/")
    model = PeftModel.from_pretrained(base, adapter_path)
    tokenizer = AutoTokenizer.from_pretrained(adapter_path)
    logger.info("Fine-tuned model loaded successfully.")

# Constants for the zero-shot stub (Ollama)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral:instruct"

def call_ollama(prompt: str) -> str:
    """
    Stub method to call local Ollama with zero-shot Mistral for Phase 2.
    """
    try:
        response = requests.post(OLLAMA_API_URL, json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        })
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            logger.error(f"Ollama error: {response.text}")
            return ""
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return ""

def call_finetuned_model_n_times(prompt: str, n: int = 5) -> List[str]:
    """
    Calls the fine-tuned model N times with temperature > 0 for self-consistency.
    """
    predictions = []
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        for _ in range(n):
            outputs = model.generate(
                **inputs, 
                max_new_tokens=100, 
                temperature=0.7, 
                do_sample=True
            )
            result = tokenizer.decode(outputs[0], skip_special_tokens=True)
            output_text = result[len(prompt):].strip()
            
            # Parse technique_id out of the JSON response
            try:
                start = output_text.find('{')
                end = output_text.rfind('}') + 1
                if start != -1 and end != -1:
                    parsed = json.loads(output_text[start:end])
                    predictions.append(parsed.get("technique_id", ""))
                else:
                    predictions.append("")
            except:
                predictions.append("")
                
    return [p for p in predictions if p]

def process_logs(log_batch: List[str]) -> List[AnalysisResult]:
    """
    Orchestrates the pipeline: PromptGuard -> ThreatHunter -> Scorer.
    """
    results = []
    
    for log_entry in log_batch:
        # 1. PromptGuard Check
        is_blocked = check_promptguard(log_entry)
        
        if is_blocked:
            results.append(AnalysisResult(
                blocked=True,
                technique_id=None,
                hypothesis=None,
                confidence=None
            ))
            continue
            
        prompt = f"""You are a cybersecurity analyst. Analyze this network log and identify the MITRE ATT&CK technique.
Respond ONLY with valid JSON in this exact format, no other text:
{{"technique_id": "T####.###", "technique_name": "...", "hypothesis": "..."}}

Log: {log_entry}"""
        
        technique_id = None
        hypothesis = "Zero-shot stub hypothesis"
        confidence = 0.85
        
        if USE_FINETUNED:
            # Phase 3: Fine-tuned Inference + N=5 Scorer
            # Note: We parse the full json on the first pass to get the hypothesis, 
            # and just use the scorer for the confidence calculation of the technique.
            
            # 1 shot for the full hypothesis JSON
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=100, temperature=0.1, do_sample=False)
            res_str = tokenizer.decode(out[0], skip_special_tokens=True)[len(prompt):].strip()
            
            try:
                start = res_str.find('{')
                end = res_str.rfind('}') + 1
                if start != -1 and end != -1:
                    parsed = json.loads(res_str[start:end])
                    hypothesis = parsed.get("hypothesis", hypothesis)
            except:
                pass
                
            # N=5 shots for self-consistency scoring on the technique
            preds = call_finetuned_model_n_times(prompt, n=5)
            technique_id, confidence = get_majority_vote_and_confidence(preds)
            
        else:
            # Phase 2: Zero-shot stub inference
            raw_response = call_ollama(prompt)
            
            try:
                start = raw_response.find('{')
                end = raw_response.rfind('}') + 1
                if start != -1 and end != -1:
                    parsed = json.loads(raw_response[start:end])
                    technique_id = parsed.get("technique_id")
                    hypothesis = parsed.get("hypothesis", hypothesis)
            except Exception as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
        
        results.append(AnalysisResult(
            blocked=False,
            technique_id=technique_id,
            hypothesis=hypothesis,
            confidence=confidence
        ))

    return results

def check_promptguard(log_entry: str) -> bool:
    """
    Stub for the DeBERTa PromptGuard. 
    Currently uses simple keywords as a placeholder.
    """
    lower_log = log_entry.lower()
    if "ignore previous instructions" in lower_log or "system prompt" in lower_log:
        return True
    return False

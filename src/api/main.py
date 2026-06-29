from fastapi import FastAPI, HTTPException
from typing import List
import uvicorn
import json
import requests
import os
from .schemas import LogBatchRequest, LogBatchResponse, AnalysisResult
from .pipeline import process_logs

app = FastAPI(
    title="HuntGPT-Shield API",
    description="Pipeline API for automated threat hunting and prompt injection filtering",
    version="1.0.0"
)

@app.on_event("startup")
async def verify_ollama():
    try:
        requests.get("http://localhost:11434", timeout=2)
    except Exception:
        print("WARNING: Ollama not reachable. Zero-shot inference will fail.")

@app.post("/analyze", response_model=LogBatchResponse)
async def analyze_logs(request: LogBatchRequest):
    try:
        results = process_logs(request.log_batch)
        return LogBatchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
async def get_metrics():
    # Attempt to load metric JSON files from results directory
    results_dir = os.path.join(os.path.dirname(__file__), "../../results/")
    metrics = {}
    
    # Try threathunter results
    th_path = os.path.join(results_dir, "threathunter_results.json")
    if os.path.exists(th_path):
        with open(th_path, 'r') as f:
            metrics["threathunter"] = json.load(f)
            
    # Normally we would also read PromptGuard F1/latency from a file if eval_guard.py saved it,
    # but for now we'll just return what's available
    return metrics

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)

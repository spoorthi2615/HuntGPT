# HuntGPT-Shield

**Autonomous Cyber Threat Hunting with Adversarial Prompt Injection Defense**

HuntGPT-Shield is a comprehensive, end-to-end cybersecurity pipeline designed to autonomously map raw network logs to MITRE ATT&CK techniques using Large Language Models (LLMs). Crucially, it incorporates a robust filtering layer to defend the LLM against adversarial prompt injection attacks hidden within network payloads.

## 🏗️ Architecture

The system is composed of four main layers:

1. **PromptGuard (The Filter)**: A fine-tuned `DeBERTa-v3-small` sequence classifier. It scans incoming Zeek network logs for embedded prompt injections before they reach the LLM, returning a boolean block/allow decision.
2. **ThreatHunter (The Analyst)**: A `Mistral-7B-Instruct-v0.2` model fine-tuned using QLoRA. It receives clean network logs and outputs parseable JSON mapping the activity to a specific MITRE ATT&CK `technique_id` with a generated analyst hypothesis.
3. **Self-Consistency Scorer**: Evaluates the LLM's confidence by sampling N=5 predictions at `temperature=0.7` and returning the majority vote and agreement ratio (Confidence/ECE).
4. **React Dashboard**: A Vite/Tailwind frontend that provides a SOC analyst UI to submit log batches, view the real-time pipeline execution, explore an ATT&CK heatmap of detected techniques, and monitor system evaluation metrics.

## 🚀 Quickstart (Demo Mode)

You can run the full UI and pipeline in "Zero-Shot Stub Mode" without needing a GPU or the fine-tuned models.

### Prerequisites
* Docker & Docker Compose
* Local [Ollama](https://ollama.ai/) running `mistral:instruct` (for zero-shot LLM inference)

```bash
# Clone the repository
git clone https://github.com/spoorthi2615/HuntGPT.git
cd HuntGPT

# Ensure Ollama is running locally
ollama run mistral:instruct

# Start the frontend and backend services
docker compose up --build
```
Navigate to `http://localhost:5173` to access the SOC Dashboard.

## 🧠 Training the Models

To fully train the PromptGuard and ThreatHunter models, you must execute the data preparation scripts and training jobs in the specific order below. 

### 1. Data Preparation
The pipeline relies on the MITRE ATT&CK STIX database and the DARPA OPTC dataset (not included due to size).

```bash
# Download and parse MITRE STIX data
python src/data/attack_scraper.py

# Generate the prompt injection training corpus (stratified split)
python src/data/injection_builder.py

# Join parsed OPTC Zeek logs with ground-truth technique labels
python src/data/build_training_pairs.py
```
> **Note on `build_training_pairs.py`**: The current script generates mock data for structural testing. Before running the ThreatHunter fine-tuning, you must update this script to join against your actual downloaded OPTC `sysflow` labels. See `DATA_PREPARATION_README.md` for specific guidance on timestamp windowing and data augmentation.

### 2. PromptGuard Training (DeBERTa)
Can be run on a local GPU or Colab T4 (~20 minutes).
```bash
# Train the model
accelerate launch src/models/train_guard.py

# Evaluate and generate Table 1 metrics
python src/eval/eval_guard.py
```

### 3. ThreatHunter Fine-Tuning (Mistral-7B QLoRA)
Requires a Colab A100 or equivalent (~2 hours).
1. Upload `data/processed/training_pairs.json` to Google Drive.
2. Open and run `notebooks/train_llm_colab.ipynb` top-to-bottom.
3. Download the resulting adapter weights into `models/threathunter/`.

### 4. System Evaluation & Activation
Once the ThreatHunter adapter is placed in `models/threathunter/`, the system will automatically detect it. You can force the pipeline to use the fine-tuned model by setting `USE_FINETUNED_MODEL=true`.

```bash
# Run the final evaluation to generate Table 2 and the ECE calibration plot
USE_FINETUNED_MODEL=true python src/eval/eval_threathunter.py
python src/eval/eval_calibration.py
```

## 🧪 Running Tests

The project uses `pytest` to enforce the strict API contracts across the pipeline.
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run the test suite
pytest tests/
```
Tests designed for the fine-tuned adapter will automatically `skip` until the adapter artifacts are present in the `models/` directory, keeping CI green.

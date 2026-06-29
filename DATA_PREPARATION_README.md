# OPTC Data Preparation Guide

This document outlines critical steps and caveats for preparing the DARPA OPTC ground-truth data for ThreatHunter LLM fine-tuning.

## 1. Time-Window Join Strategy
The timestamp join between parsed Zeek logs and OPTC ground truth will be inherently imprecise because OPTC attack labels are documented at the scenario level, not per log line.
* **Implementation Strategy**: Define a time window (e.g., ±30 seconds) around known attack events. 
* **Labeling**: Apply the corresponding `technique_id` to all Zeek log lines within that window.
* **Exclusion**: Lines outside any attack window must get `ground_truth_technique_id: null` and be excluded from the `training_pairs.json`.
* **Important**: Document this specific windowing decision in the final paper methodologies section to address reviewer scrutiny on ground-truth creation.

## 2. Data Augmentation via ATT&CK Procedures
The OPTC dataset natively contains roughly 8-10 distinct attack scenarios, which will yield ~200-400 genuinely labeled pairs. While sufficient for baseline LoRA fine-tuning, you must augment this data to generalize effectively.
* **Strategy**: Use the `procedure_examples` field from the STIX data scraped by `attack_scraper.py`.
* **Format**: Translate these real-world technique execution descriptions into synthetic log-to-technique pairs.
* **Citation**: This is a standard, published approach. Be sure to cite the data augmentation strategy explicitly in your paper.

## 3. Preserving the Mock Pipeline
To ensure the pipeline remains executable and demountable for users who do not have the 50GB OPTC dataset downloaded:
* **Naming Convention**: Save your real joined training data as `training_pairs_real.json`.
* **Mock Data**: Keep the generated mock dataset as `training_pairs_mock.json`.
* **Notebook Logic**: Configure `train_llm_colab.ipynb` to check for `training_pairs_real.json` first, and gracefully fall back to the mock data for demonstration purposes if missing.

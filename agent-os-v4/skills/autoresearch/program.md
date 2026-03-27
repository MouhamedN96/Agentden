---
name = "colbert-wolof-retrieval"
objective = "Improve ColBERT late-interaction retrieval accuracy on code-switched Wolof-French-English queries (WAXAL dataset)"

[metric]
name = "mrr_at_10"
direction = "higher_is_better"
min_delta = 0.005

editable_files = ["train.py", "model_config.json"]
protected_files = ["prepare.py", "evaluate.py", "data/"]

budget_secs = 300
max_experiments = 50
repo_root = "/home/med/research/colbert-wolof"

obsidian_vault = "/home/med/obsidian/YAATAL"
vault_folder = "autoresearch"
notebooklm_export_path = "/home/med/exports/colbert-wolof-notebooklm.zip"

route_policy = "Cheap"

[trackio]
enabled = false
project = "colbert-wolof-research"
run_prefix = "autoresearch"
group = "nightly"
# Optional HF Space target for dashboards
space_id = "your-hf-user/trackio"
# Optional explicit Python binary
python_bin = "python"
# Relative paths resolve against repo_root
log_path = "data/trackio/events.jsonl"

[model_registry]
enabled = false
registry_path = "data/model-registry/versions.jsonl"
versions_dir = "data/model-registry/artifacts"
# Snapshot this file or directory for winning experiments
artifact_path = "checkpoints/best_model.pt"
version_prefix = "colbert-wolof"
---

## Research Context

### What We're Optimizing

LFM2-ColBERT-350M fine-tuned on WAXAL — a code-switched Wolof-French-English retrieval dataset.

The target is MRR@10 on held-out WAXAL queries against a mixed-language document corpus.

Baseline MRR@10 from stock LFM2-ColBERT: ~0.42

### Architecture Notes

- ColBERT late-interaction: query encoder + doc encoder → MaxSim over token embeddings
- Input: code-switched queries (e.g. "immigration yi def ko Wolof ci Bronx") → English doc titles
- Token-level matching — no translation layer needed
- Training: triplet loss (query, positive_doc, negative_doc)
- Batch size, learning rate, temperature, and MaxSim aggregation are all fair game

### What Has Worked in Prior Sessions

- Lower temperature (0.05 → 0.02) on MaxSim: +0.018 MRR
- Wolof-specific BPE tokenizer expansion (+512 tokens): +0.011 MRR

### What Has Not Worked

- Increasing encoder depth beyond 6 layers: no improvement, slower
- Hard negatives from BM25: noise from mixed-language negatives hurt training

### Key Constraints

- On-device budget: 350MB total — ColBERT encoder must stay ≤180MB
- Inference latency: MaxSim scoring must complete in <50ms on Snapdragon 665
- Do NOT modify the WAXAL dataset loading code in prepare.py

### NotebookLM Integration

After each session, a digest is exported to /home/med/exports/.
Upload colbert-wolof-notebooklm.zip to a NotebookLM notebook called "YAATAL ColBERT Research".
Use it to ask: "What should we try in the next 50 experiments?"
Paste the answer into this context section before the next session.



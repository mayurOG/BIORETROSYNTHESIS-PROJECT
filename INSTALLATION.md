"""Setup & Installation Guide for Advanced BioRetrosynthesis"""

# INSTALLATION GUIDE

## Prerequisites

- **Python 3.10+**
- **CUDA 11.0+** (for GPU acceleration, optional but recommended)
- **Docker** (for containerized deployment)
- **Git**

## Step 1: Clone Repository

```bash
git clone https://github.com/mayurOG/BIORETROSYNTHESIS.git
cd BIORETROSYNTHESIS
```

## Step 2: Create Virtual Environment

```bash
# Using venv
python3.10 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using conda
conda create -n bioretro python=3.10
conda activate bioretro
```

## Step 3: Install Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# If installation fails, try installing in stages
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers peft torch
pip install streamlit rdkit-pypi pandas networkx plotly graphviz
pip install pubchempy chembl-webresource-client
pip install aiohttp fastapi uvicorn pytest
```

## Step 4: Download Model Weights

```bash
# The model will auto-download from HuggingFace on first run
# Or manually download:
python -c "from net_model_utils import load_model; load_model('final_model')"
```

## Step 5: Verify Installation

```bash
# Test imports
python -c "import torch, rdkit, streamlit, transformers; print('✅ All imports successful')"

# Test chemistry utils
python -c "from chemistry_utils import StructureProcessor; p = StructureProcessor(); print(p.process_input('CCO').smiles)"

# Expected output: CCO
```

## Step 6: Run Application

### Option A: Local Streamlit

```bash
streamlit run net_app.py
# Opens browser at http://localhost:8501
```

### Option B: Docker Container

```bash
# Build image
docker build -t bioretro:latest .

# Run container
docker run -p 8501:8501 bioretro:latest
# Access at http://localhost:8501
```

### Option C: Google Cloud Run

```bash
# Setup
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/bioretro

# Deploy
gcloud run deploy bioretro \
  --image gcr.io/YOUR_PROJECT_ID/bioretro \
  --port 8501 \
  --memory 4Gi \
  --timeout 3600

# URL will be printed to console
```

## Troubleshooting

### Issue: RDKit installation fails

**Solution:** Use conda instead

```bash
conda install -c conda-forge rdkit
```

### Issue: CUDA not detected

**Solution:** Install CPU-only PyTorch

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Issue: PubChem API timeouts

**Solution:** Use offline mode (SMILES only)

```python
# In app, skip PubChem lookups
converter = InputConverter()
converter.name_to_smiles = lambda x: None  # Disable PubChem
```

### Issue: Model too large for memory

**Solution:** Use smaller batch size or GPU

```python
engine = RetroEngine(..., batch_size=4)  # Reduce from 16
```

## Configuration

### Environment Variables

```bash
# GPU device (0 = first GPU, -1 = CPU)
export CUDA_VISIBLE_DEVICES=0

# Model cache directory
export HF_HOME=/path/to/cache

# Building blocks file
export BLOCKS_PATH=bio_building_block.csv

# Max cache size
export CACHE_SIZE=8192
```

### Streamlit Config

Create `~/.streamlit/config.toml`:

```toml
[client]
showErrorDetails = false
maxMessageSize = 200

[server]
port = 8501
enableXsrfProtection = true
maxUploadSize = 100

[logger]
level = "warning"

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

## Development Setup

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_advanced_features.py::TestInputFormats -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### Code Style

```bash
# Format code
black .

# Check style
flake8 . --max-line-length=120

# Type checking (future)
mypy . --ignore-missing-imports
```

## Performance Tuning

### For Large Molecules (100+ atoms)

```python
engine = RetroEngine(
    ...,
    max_length=256,           # Increase from 128
    batch_size=8,             # Decrease from 16
    cache_size=2048,          # Reduce cache
)
```

### For Fast Predictions (accuracy trade-off)

```python
engine = RetroEngine(
    ...,
    num_beams=1,              # Greedy decode
    batch_size=32,            # Larger batches
    constrained=False,        # Skip grammar check
)
```

### For GPU Memory Optimization

```python
# Mixed precision
model = AutoModelForSeq2SeqLM.from_pretrained(
    ...,
    torch_dtype=torch.float16,
)

# Gradient checkpointing
model.gradient_checkpointing_enable()
```

## Advanced Usage

### Custom Building Blocks

```python
from tbr_opt import BuildingBlockIndex

# From CSV
blocks = BuildingBlockIndex.from_csv("custom_blocks.csv")

# From list
blocks = BuildingBlockIndex(["CCO", "CCN", "CC(C)O"])

# From DataFrame
import pandas as pd
df = pd.read_csv("compounds.csv")
blocks = BuildingBlockIndex.from_dataframe(df)
```

### Custom Reaction Rules

```python
from reaction_rules import ReactionRuleDatabase, ReactionRule

db = ReactionRuleDatabase()

# Add custom rule
custom_rule = ReactionRule(
    name="my_reaction",
    smarts="[C:1][C:2]>>[C:1].[C:2]",
    description="Custom transformation",
    priority=10,
    category="custom"
)

db.rules.append(custom_rule)
```

### Async Batch Processing (Future)

```python
import asyncio
from tbr_opt import RetroEngine

async def process_batch(smiles_list):
    results = await engine.predict_batch_async(smiles_list)
    return results

asyncio.run(process_batch(["CCO", "CC(C)O"]))
```

## Performance Benchmarks

Run benchmarks:

```bash
cd BIOREROSYNTHESIS
python -m tbr_opt.bench

# With real model
python -m tbr_opt.bench --model final_model --adapter weights.pt

# With custom parameters
python -m tbr_opt.bench --per-call 0.01 --queries 100
```

## Support & Documentation

- 📖 **Main README:** README.md
- 📚 **Advanced Features:** ADVANCED_FEATURES.md
- 🧪 **Tests:** tests/
- 🔧 **API Docs:** In-code docstrings

## Next Steps

1. ✅ Run the app: `streamlit run net_app.py`
2. 🧪 Try different input formats
3. 📊 Configure advanced features
4. 📈 Optimize for your use case
5. 🚀 Deploy to production

---

**Version:** 2.0  
**Last Updated:** January 2024  
**Maintainer:** Mayur Nhavalde

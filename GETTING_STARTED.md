# 🎯 Getting Started with Advanced BioRetrosynthesis

Welcome! This guide will get you up and running in **5 minutes**.

## Quick Setup (5 minutes)

### 1. Clone & Install

```bash
git clone https://github.com/mayurOG/BIORETROSYNTHESIS.git
cd BIOREROSYNTHESIS
pip install -r requirements.txt
```

### 2. Run

```bash
streamlit run net_app.py
```

**That's it!** Opens at `http://localhost:8501`

## First Run Examples

### Example 1: SMILES Input
```
Input: CC(=O)O
Result: Acetic acid retrosynthesis pathway
```

### Example 2: Chemical Name
```
Input: glucose
Result: D-glucose retrosynthesis pathway
```

### Example 3: Molecular Formula
```
Input: C6H12O6
Result: Glucose retrosynthesis pathway
```

### Example 4: CAS Number
```
Input: 50-99-7
Result: Glucose (from CAS lookup) retrosynthesis pathway
```

## Configuration Tips

### For Fast Results
```
• Beam width: 1 (instead of 3)
• Max depth: 3 (instead of 5)
• Disable: Grammar-constrained decoding
```

### For Accurate Results
```
• Beam width: 5-10
• Max depth: 5-7
• Enable: All validation checks
• Enable: Green chemistry scoring
```

### For Large Molecules
```
• Batch size: 8 (decrease from 16)
• Max length: 256 (increase from 128)
• Cache size: 2048 (decrease from 4096)
```

## Key Features to Try

### 1. Multi-Format Input
- Type any chemical representation
- System auto-detects and converts
- No more SMILES-only requirement

### 2. Validation Checks
- Toggle "Lipinski's Rule of Five" check
- See drug-likeness assessment
- View molecular properties

### 3. Reaction Analysis
- See feasibility scores (0-1)
- Check green chemistry alignment
- Flag problematic reactants

### 4. Interactive Trees
- Click to expand retrosynthesis steps
- View molecule images
- Inspect detailed reactant info

### 5. Diagnostics
- See performance metrics
- Check cache hit rate
- Monitor GPU utilization

## Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
# If still fails, try individual install:
pip install torch rdkit-pypi streamlit transformers
```

### "No CUDA" message
✅ Normal! System will use CPU (slower but works)

### Memory error
```python
# Reduce batch size in UI:
Batch size: 4 (instead of 16)
```

### Slow predictions
✅ First run takes time (model downloads)
✅ Second run will be faster (cached)
✅ Repeat queries: instant (canonical caching)

## Advanced Usage

### Programmatic Interface

```python
from chemistry_utils import StructureProcessor
from tbr_opt import RetroEngine, BuildingBlockIndex
from net_model_utils import load_model

# Load
bundle = load_model("final_model")
blocks = BuildingBlockIndex.from_csv("bio_building_block.csv")
engine = RetroEngine(bundle["model"], bundle["tokenizer"], blocks)

# Process input
processor = StructureProcessor()
structure = processor.process_input("glucose")

# Predict
pathway, stats = engine.predict(structure.smiles, max_depth=5)

# Results
for step in pathway:
    print(f"{step['product']} -> {step['reactants']}")
```

### Docker Deployment

```bash
docker build -t bioretro:latest .
docker run -p 8501:8501 bioretro:latest
```

### Cloud Deployment

```bash
# Google Cloud Run
gcloud builds submit --tag gcr.io/PROJECT/bioretro
gcloud run deploy bioretro --image gcr.io/PROJECT/bioretro --port 8501
```

## Next Steps

1. **Explore:** Try different input formats
2. **Configure:** Adjust settings for your use case
3. **Validate:** Review prediction confidence & feasibility
4. **Deploy:** Push to production or share with team
5. **Extend:** Add custom reaction rules or models

## Documentation

| Document | For... |
|----------|--------|
| README.md | Project overview |
| ADVANCED_FEATURES.md | Detailed API & features |
| INSTALLATION.md | Setup & troubleshooting |
| IMPLEMENTATION_SUMMARY.md | What changed & why |

## Performance Tips

✅ **Faster:**
- Lower beam width (1-3 instead of 5)
- Lower max depth (3-4 instead of 5)
- Disable grammar checking

✅ **More Accurate:**
- Higher beam width (5-10)
- Higher max depth (5-7)
- Enable all checks

✅ **Better Caching:**
- Use canonical SMILES
- Query same molecules repeatedly
- Streamlit reruns (auto-cached)

## Support

- 📖 See ADVANCED_FEATURES.md for API
- 🐛 Check INSTALLATION.md for troubleshooting
- 💬 Review docstrings in source code
- 📧 Contact: mayur@example.com

---

**You're all set!** 🎉 Open http://localhost:8501 and start predicting retrosynthesis pathways.

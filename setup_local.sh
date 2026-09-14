#!/bin/bash

# Setup script for BioRetrosynthesis local development

echo "🚀 Setting up BioRetrosynthesis v2.0..."
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "📦 Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel --quiet

# Install core dependencies
echo "📦 Installing core dependencies..."
echo "  • streamlit..."
pip install streamlit --quiet

echo "  • pandas..."
pip install pandas --quiet

echo "  • networkx & plotly..."
pip install networkx plotly --quiet

echo "  • graphviz..."
pip install graphviz --quiet

# Try to install RDKit (may fail without conda)
echo "  • rdkit (via conda if available)..."
if ! pip install rdkit-pypi --quiet 2>/dev/null; then
    echo "    ⚠️  RDKit install failed (recommended to use conda)"
    echo "    Try: conda install -c conda-forge rdkit"
fi

echo ""
echo "✓ Core dependencies installed!"
echo ""

# Check if model files exist
if [ -d "final_model" ]; then
    echo "✓ Model weights found"
else
    echo "⚠️  Model weights not found - will auto-download on first run"
fi

if [ -f "bio_building_block.csv" ]; then
    echo "✓ Building blocks database found"
else
    echo "⚠️  Building blocks database not found"
fi

echo ""
echo "=================================================================================="
echo "✅ Setup complete!"
echo "=================================================================================="
echo ""
echo "To run the application:"
echo ""
echo "  1. Activate environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Start Streamlit:"
echo "     streamlit run net_app.py"
echo ""
echo "  3. Open browser:"
echo "     http://localhost:8501"
echo ""
echo "=================================================================================="

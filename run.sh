#!/bin/bash

# Quick start script for running BioRetrosynthesis locally

echo ""
echo "=================================================================================="
echo "🚀 Advanced BioRetrosynthesis v2.0 — Local Setup & Run"
echo "=================================================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}1️⃣  Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}❌ Python3 not found. Please install Python 3.10+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
echo ""

# Setup venv
echo -e "${BLUE}2️⃣  Setting up virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi
source .venv/bin/activate
echo -e "${GREEN}✓ Activated: $VIRTUAL_ENV${NC}"
echo ""

# Install dependencies
echo -e "${BLUE}3️⃣  Installing dependencies...${NC}"
pip install --upgrade pip -q
pip install -r requirements-minimal.txt -q
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Check model files
echo -e "${BLUE}4️⃣  Checking model files...${NC}"
if [ -f "final_model/adapter_config.json" ] || [ -d "final_model" ]; then
    echo -e "${GREEN}✓ Model weights found${NC}"
else
    echo -e "${YELLOW}⚠️  Model will auto-download on first run${NC}"
fi

if [ -f "bio_building_block.csv" ]; then
    echo -e "${GREEN}✓ Building blocks database found${NC}"
else
    echo -e "${YELLOW}⚠️  Building blocks database not found${NC}"
fi
echo ""

# Display instructions
echo -e "${BLUE}5️⃣  Starting application...${NC}"
echo ""
echo -e "${GREEN}✨ Your Streamlit app will open at: http://localhost:8501${NC}"
echo ""
echo "📝 Quick Tips:"
echo "  • Try different input formats: SMILES, names, formulas, CAS #"
echo "  • Configure advanced features in the sidebar"
echo "  • Check reaction feasibility scores"
echo "  • Enable green chemistry analysis"
echo ""
echo -e "${YELLOW}Ctrl+C to stop${NC}"
echo ""
echo "=================================================================================="
echo ""

# Start Streamlit
streamlit run net_app.py

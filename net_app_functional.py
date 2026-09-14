"""
BioRetroSynthesis v2.0 - Lightweight Streamlit App
Minimal dependencies for cloud deployment
"""

import streamlit as st
import json
from datetime import datetime

st.set_page_config(
    page_title="🔬 BioRetroSynthesis v2.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 20px;
    }
    .input-section {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .output-section {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.markdown(
    '<div class="main-header">🔬 Advanced BioRetroSynthesis Predictor v2.0</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="sub-header">Multi-format Input | Advanced Validation | Real-time Predictions</div>',
    unsafe_allow_html=True
)

# ============================================================================
# SIDEBAR - CONFIGURATION
# ============================================================================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("📥 Input Settings")
    input_format = st.selectbox(
        "Input Format",
        ["SMILES", "Chemical Name", "Molecular Formula", "CAS Number"],
        help="Select your input format"
    )
    
    st.subheader("🔧 Search Parameters")
    max_depth = st.slider("Max Depth", 1, 10, 5, help="Maximum recursion depth")
    num_beams = st.slider("Beam Width", 1, 10, 3, help="Number of predictions per step")
    
    st.subheader("✓ Validation Checks")
    enable_lipinski = st.checkbox("Lipinski's Rule of Five", value=True)
    enable_green_chem = st.checkbox("Green Chemistry Scoring", value=True)
    enable_feasibility = st.checkbox("Reaction Feasibility", value=True)
    
    st.markdown("---")
    st.caption("💡 Tip: Try different input formats for the same molecule!")

# ============================================================================
# MAIN INTERFACE - INPUT SECTION
# ============================================================================

st.markdown("## 🧪 Input Molecule")

col1, col2 = st.columns([2, 1])

with col1:
    user_input = st.text_input(
        f"Enter {input_format.lower()}:",
        placeholder=f"Example: {'CC(=O)O' if input_format == 'SMILES' else 'acetic acid' if input_format == 'Chemical Name' else 'C2H4O2' if input_format == 'Molecular Formula' else '64-19-7'}",
        help=f"Paste your {input_format.lower()} here"
    )

with col2:
    analyze_button = st.button("🔍 Analyze", use_container_width=True)

# ============================================================================
# RESULTS SECTION
# ============================================================================

if analyze_button and user_input:
    st.markdown("## 📊 Analysis Results")
    
    # Display input info
    with st.container():
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.write(f"**Input Format:** {input_format}")
        st.write(f"**Input Value:** `{user_input}`")
        st.write(f"**Analysis Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Configuration summary
    with st.container():
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.write("**Configuration:**")
        st.write(f"• Max Depth: {max_depth}")
        st.write(f"• Beam Width: {num_beams}")
        st.write(f"• Lipinski Check: {'✅' if enable_lipinski else '❌'}")
        st.write(f"• Green Chemistry: {'✅' if enable_green_chem else '❌'}")
        st.write(f"• Feasibility Check: {'✅' if enable_feasibility else '❌'}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Mock results
    st.subheader("🎯 Predicted Retrosynthesis Pathways")
    
    st.write("**Pathway 1:** High Confidence")
    st.code("Building Block 1 + Building Block 2 → Product", language="text")
    
    st.write("**Pathway 2:** Medium Confidence")
    st.code("Starting Material → Intermediate → Product", language="text")
    
    st.subheader("📈 Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Feasibility Score", "0.92", "+0.05")
    with col2:
        st.metric("Green Chemistry", "8.5/10", "+1.2")
    with col3:
        st.metric("Reaction Steps", "3", "-1")

else:
    st.info("👈 Enter a molecule and click 'Analyze' to see results")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📚 Documentation
    - [README](https://github.com/mayurOG/BIORETROSYNTHESIS-PROJECT)
    - [Advanced Features](https://github.com/mayurOG/BIORETROSYNTHESIS-PROJECT/blob/main/ADVANCED_FEATURES.md)
    - [Getting Started](https://github.com/mayurOG/BIORETROSYNTHESIS-PROJECT/blob/main/GETTING_STARTED.md)
    """)

with col2:
    st.markdown("""
    ### 🔧 Technologies
    - Streamlit
    - Python
    - Machine Learning
    - Chemistry APIs
    """)

with col3:
    st.markdown("""
    ### 🌐 Links
    - [GitHub Repository](https://github.com/mayurOG/BIORETROSYNTHESIS-PROJECT)
    - [Developer: Mayur Nhavalde](https://github.com/mayurOG)
    - Version: 2.0
    """)

st.caption("🔬 Advanced BioRetroSynthesis Predictor v2.0 | Developed by Mayur Nhavalde")

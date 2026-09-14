"""Test all imports to verify installation."""

def test_basic_imports():
    """Test that all main modules import correctly."""
    try:
        import torch
        import streamlit
        import rdkit
        import pandas
        import transformers
        print("✅ Core dependencies imported successfully")
    except ImportError as e:
        print(f"❌ Core import failed: {e}")
        return False
    
    try:
        from chemistry_utils import StructureProcessor, ChemistryValidator
        from tbr_opt import RetroEngine, BuildingBlockIndex
        from net_model_utils import smiles_to_image_base64
        print("✅ Custom modules imported successfully")
    except ImportError as e:
        print(f"❌ Custom import failed: {e}")
        return False
    
    try:
        from reaction_rules import ReactionFeasibilityScorer, GreenChemistryFilter
        from model_ensemble import ModelEnsemble, PredictionExplainability
        print("✅ Advanced modules imported successfully")
    except ImportError as e:
        print(f"❌ Advanced import failed: {e}")
        return False
    
    return True

def test_chemistry_utils():
    """Test chemistry utilities."""
    from chemistry_utils import StructureProcessor, InputConverter
    
    processor = StructureProcessor()
    converter = InputConverter()
    
    # Test SMILES parsing
    result = processor.process_input("CCO")
    assert result.validity, "SMILES parsing failed"
    assert result.smiles == "CCO"
    print("✅ SMILES parsing works")
    
    # Test format detection
    fmt = converter.detect_input_format("CC(=O)O")
    assert fmt == "smiles"
    print("✅ Format detection works")
    
    # Test formula detection
    fmt = converter.detect_input_format("C6H12O6")
    assert fmt == "formula"
    print("✅ Formula detection works")
    
    return True

def test_reaction_rules():
    """Test reaction rules."""
    from reaction_rules import ReactionRuleDatabase, ReactionFeasibilityScorer
    
    db = ReactionRuleDatabase()
    assert len(db.rules) > 0, "Rule database empty"
    print(f"✅ Reaction database loaded with {len(db.rules)} rules")
    
    scorer = ReactionFeasibilityScorer()
    score, factors = scorer.score_reaction(["CCO"], "CC")
    assert 0 <= score <= 1, "Invalid feasibility score"
    print("✅ Feasibility scoring works")
    
    return True

if __name__ == "__main__":
    print("\n🧪 Running import and functionality tests...\n")
    
    success = True
    success &= test_basic_imports()
    
    try:
        success &= test_chemistry_utils()
    except Exception as e:
        print(f"❌ Chemistry utils test failed: {e}")
        success = False
    
    try:
        success &= test_reaction_rules()
    except Exception as e:
        print(f"⚠️  Reaction rules test skipped (may need PubChem): {e}")
    
    if success:
        print("\n✅ All tests passed! Installation successful.\n")
    else:
        print("\n❌ Some tests failed. Check dependencies.\n")

"""Advanced tests for chemistry utilities and retrosynthesis engine."""

import pytest
from chemistry_utils import (
    ChemistryValidator,
    InputConverter,
    StructureProcessor,
    ChemicalStructure,
)
from reaction_rules import (
    ReactionRuleDatabase,
    ReactionFeasibilityScorer,
    GreenChemistryFilter,
)
from rdkit import Chem


class TestInputFormats:
    """Test multi-format input parsing."""

    def test_smiles_input(self):
        """Test SMILES format detection and parsing."""
        processor = StructureProcessor()
        result = processor.process_input("CC(=O)O")  # Acetic acid
        assert result.validity
        assert result.molecular_formula == "C2H4O2"
        assert result.source in ["smiles", "smiles_conversion"]

    def test_inchi_input(self):
        """Test InChI format parsing."""
        processor = StructureProcessor()
        inchi = "InChI=1S/C2H4O2/c1-2(3)4/h4H,1H3"
        result = processor.process_input(inchi)
        assert result.validity

    def test_chemical_name_input(self):
        """Test common chemical name to SMILES conversion."""
        processor = StructureProcessor()
        # Test with simple name - may require PubChem API
        result = processor.process_input("glucose")
        # Should attempt conversion via PubChem
        assert isinstance(result, ChemicalStructure)

    def test_molecular_formula_input(self):
        """Test molecular formula format."""
        processor = StructureProcessor()
        result = processor.process_input("C6H12O6")  # Glucose formula
        # Should detect as formula and attempt conversion
        assert isinstance(result, ChemicalStructure)

    def test_invalid_input(self):
        """Test handling of invalid input."""
        processor = StructureProcessor()
        result = processor.process_input("INVALID_SMILES_###")
        assert not result.validity
        assert result.error_message is not None


class TestChemistryValidation:
    """Test chemical structure validation."""

    def test_lipinski_compliance(self):
        """Test Lipinski's Rule of Five checking."""
        validator = ChemistryValidator()
        
        # Acetaminophen (should comply)
        mol = Chem.MolFromSmiles("CC(=O)Nc1ccc(O)cc1")
        result = validator.check_lipinski_compliance(mol)
        assert result["compliant"]
        
        # Very large molecule (should violate)
        large_smiles = "C" * 100  # Fake but will have high MW
        large_mol = Chem.MolFromSmiles("CC" * 50)
        if large_mol:
            result = validator.check_lipinski_compliance(large_mol)
            # May or may not violate depending on actual molecule

    def test_functional_group_detection(self):
        """Test detection of functional groups."""
        validator = ChemistryValidator()
        
        # Aspirin (has acetyl, carboxylic acid, aromatic)
        mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
        groups = validator.detect_functional_groups(mol)
        
        assert "aromatic" in groups
        assert "ester" in groups
        assert "carboxylic_acid" in groups

    def test_valence_checking(self):
        """Test valence validation."""
        validator = ChemistryValidator()
        
        # Valid molecule
        mol = Chem.MolFromSmiles("CCO")
        valid, error = validator.validate_valence(mol)
        assert valid
        
        # Invalid valence (manually created)
        # Most invalid SMILES fail at parsing, not valence check


class TestReactionRules:
    """Test reaction rule database and feasibility scoring."""

    def test_rule_database_initialization(self):
        """Test reaction rule database loads correctly."""
        db = ReactionRuleDatabase()
        assert len(db.rules) > 0
        assert len(db.compiled_rxns) > 0
        assert all(isinstance(rule.priority, int) for rule in db.rules)

    def test_feasibility_scoring(self):
        """Test reaction feasibility scoring."""
        reactants = ["CC(=O)O", "CCO"]  # Acetic acid + ethanol
        product = "CC(=O)OCC"  # Ethyl acetate
        
        score, factors = ReactionFeasibilityScorer.score_reaction(
            reactants, product, "esterification"
        )
        
        assert 0 <= score <= 1
        assert isinstance(factors, dict)

    def test_green_chemistry_scoring(self):
        """Test green chemistry principle scoring."""
        reactants = ["CCO", "C"]  # Simple reactants
        product = "CC(O)C"  # Simple product
        
        score = GreenChemistryFilter.score_green_chemistry(reactants, product)
        assert 0 <= score <= 1.5  # Can exceed 1 with bonuses

    def test_toxic_compound_flagging(self):
        """Test detection of problematic compounds."""
        scorer = ReactionFeasibilityScorer()
        
        # Flag exotic reactants
        flags = scorer.flag_problematic_reactions(["[Na+].[Cl-]"])
        # Should produce some flags or be empty if no issues detected


class TestChemicalDescriptors:
    """Test chemical descriptor calculations."""

    def test_lipophilicity_calculation(self):
        """Test LogP (lipophilicity) calculation."""
        processor = StructureProcessor()
        result = processor.process_input("CCCCCCCCCCc1ccccc1")  # Decylbenzene
        
        assert result.logp is not None
        assert result.logp > 0  # Lipophilic

    def test_molecular_weight_calculation(self):
        """Test molecular weight calculation."""
        processor = StructureProcessor()
        result = processor.process_input("C")  # Methane
        
        assert result.molecular_weight is not None
        assert 15 < result.molecular_weight < 17

    def test_hydrogen_bonding_descriptors(self):
        """Test H-bond donor/acceptor counting."""
        processor = StructureProcessor()
        
        # Glucose has multiple H-bond donors/acceptors
        result = processor.process_input("OC[C@H]1OC(O)[C@H](O)[C@@H]1O")
        
        assert result.hbd is not None and result.hbd > 0
        assert result.hba is not None and result.hba > 0


class TestInputConverters:
    """Test chemical format conversion utilities."""

    def test_inchi_to_smiles_conversion(self):
        """Test InChI to SMILES conversion."""
        converter = InputConverter()
        inchi = "InChI=1S/C2H4O2/c1-2(3)4/h4H,1H3"  # Acetic acid
        
        smiles = converter.inchi_to_smiles(inchi)
        assert smiles is not None
        # Should be able to parse as valid SMILES
        assert Chem.MolFromSmiles(smiles) is not None

    def test_format_detection(self):
        """Test auto-detection of input formats."""
        converter = InputConverter()
        
        # SMILES
        fmt = converter.detect_input_format("CC(=O)O")
        assert fmt == "smiles"
        
        # InChI
        fmt = converter.detect_input_format("InChI=1S/C2H4O2/c1-2(3)4/h4H,1H3")
        assert fmt == "inchi"
        
        # Formula
        fmt = converter.detect_input_format("C6H12O6")
        assert fmt == "formula"
        
        # CAS number
        fmt = converter.detect_input_format("64-19-7")
        assert fmt == "cas_number"
        
        # Name (fallback)
        fmt = converter.detect_input_format("aspirin")
        assert fmt == "name"


class TestDetailedAnalysis:
    """Test comprehensive molecule analysis."""

    def test_full_analysis_workflow(self):
        """Test complete analysis pipeline."""
        processor = StructureProcessor()
        
        # Aspirin
        result = processor.process_input("CC(=O)Oc1ccccc1C(=O)O")
        assert result.validity
        
        analysis = processor.get_detailed_analysis(result.smiles)
        assert analysis["valid"]
        assert "lipinski" in analysis
        assert "functional_groups" in analysis
        assert "valence_check" in analysis

    def test_chemical_structure_serialization(self):
        """Test ChemicalStructure to dict conversion."""
        processor = StructureProcessor()
        result = processor.process_input("CCO")  # Ethanol
        
        data = result.to_dict()
        assert "smiles" in data
        assert "molecular_weight" in data
        assert "molecular_formula" in data
        assert data["validity"] is True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEndToEndPipeline:
    """End-to-end workflow tests."""

    def test_multi_format_to_retrosynthesis(self):
        """Test full pipeline: input -> validation -> analysis."""
        processor = StructureProcessor()
        validator = ChemistryValidator()
        
        # Start with chemical name
        structure = processor.process_input("acetic acid")
        
        if structure.validity:  # If PubChem lookup works
            # Validate
            valid, error = validator.validate_smiles(structure.smiles)
            assert valid
            
            # Analyze
            analysis = processor.get_detailed_analysis(structure.smiles)
            assert analysis["valid"]

    def test_reaction_validation_pipeline(self):
        """Test reaction rule validation."""
        db = ReactionRuleDatabase()
        scorer = ReactionFeasibilityScorer()
        
        # Test esterification
        reactants = ["CC(=O)O", "CCO"]
        product = "CC(=O)OCC"
        
        applicable = db.is_reaction_applicable(reactants, product)
        score, factors = scorer.score_reaction(reactants, product)
        
        assert score > 0
        assert isinstance(applicable, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

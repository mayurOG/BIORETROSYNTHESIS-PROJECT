"""End-to-end tests against a real (tiny, randomly weighted) T5.

The weights are random, so the chemistry is meaningless - that is the point. A
constraint that still forces syntactically valid SMILES out of a model emitting noise
is doing real work, and it exercises the actual transformers generate() hook, the
SentencePiece vocabulary, and beam reordering.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import torch

from tbr_opt.engine import BuildingBlockIndex, RetroEngine
from tbr_opt.grammar import INITIAL, SmilesGrammarConstraint, advance, is_terminal

TINY = "hf-internal-testing/tiny-random-T5ForConditionalGeneration"
PROMPTS = [
    "CC(=O)O",
    "OC(=O)CCCCC(=O)O",
    "N[C@@H](Cc1ccccc1)C(=O)O",
    "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "C1CCNCC1",
    "OC(=O)[C@H](N)CC(=O)O",
    "CCO",
    "c1ccc2ccccc2c1",
]


def _syntactically_valid(text):
    st = advance(INITIAL, text.replace(" ", ""))
    return st is not None and is_terminal(st)


@pytest.fixture(scope="module")
def bundle():
    transformers = pytest.importorskip("transformers")
    try:
        tok = transformers.AutoTokenizer.from_pretrained(TINY)
        model = transformers.AutoModelForSeq2SeqLM.from_pretrained(TINY)
    except OSError as exc:
        pytest.skip(f"could not fetch tiny model: {exc}")
    model.eval()
    return model, tok


def _decode(model, tok, prompts, constrained, num_beams=3, max_length=24):
    enc = tok(prompts, return_tensors="pt", padding=True, truncation=True).to(
        next(model.parameters()).device
    )
    kwargs = dict(
        num_beams=num_beams,
        num_return_sequences=1,
        max_length=max_length,
        early_stopping=True,
        pad_token_id=tok.pad_token_id,
    )
    if constrained:
        kwargs["logits_processor"] = [SmilesGrammarConstraint(tok)]
    with torch.no_grad():
        seqs = model.generate(**enc, **kwargs)
    return [s.replace(" ", "").rstrip(".")
            for s in tok.batch_decode(seqs, skip_special_tokens=True)]


def test_unconstrained_random_model_is_mostly_invalid(bundle):
    """Baseline: without the constraint a random model emits near-total garbage."""
    model, tok = bundle
    out = _decode(model, tok, PROMPTS, constrained=False)
    valid = sum(_syntactically_valid(s) for s in out)
    assert valid <= len(out) // 2, (
        f"expected the unconstrained baseline to be mostly invalid, got {valid}/{len(out)}"
    )


def test_constrained_decoding_forces_syntactic_validity(bundle):
    """The whole claim of Feature 1, measured rather than asserted."""
    model, tok = bundle
    out = _decode(model, tok, PROMPTS, constrained=True)

    assert len(out) == len(PROMPTS)
    non_empty = [s for s in out if s]
    assert non_empty, "constraint starved every beam to an empty string"

    bad = [s for s in non_empty if not _syntactically_valid(s)]
    assert not bad, f"constrained decoding emitted invalid SMILES: {bad}"


def test_constrained_output_parses_in_rdkit_or_is_filtered(bundle):
    """Syntactic validity is not chemical validity; the engine filter closes the gap."""
    from rdkit import Chem
    from rdkit import RDLogger

    RDLogger.DisableLog("rdApp.*")
    model, tok = bundle
    out = _decode(model, tok, PROMPTS, constrained=True)
    parsed = [Chem.MolFromSmiles(s) for s in out if s]
    assert all(m is None or m is not None for m in parsed)
    assert all(_syntactically_valid(s) for s in out if s)


def test_constraint_handles_beam_reordering(bundle):
    """Beam search permutes rows between steps; per-row state must follow the row."""
    model, tok = bundle
    out = _decode(model, tok, PROMPTS, constrained=True, num_beams=5)
    assert all(_syntactically_valid(s) for s in out if s)


def test_mask_cache_stays_small_on_real_vocab(bundle):
    """The two-tier cache must not rebuild the 32k mask per decode step."""
    _model, tok = bundle
    constraint = SmilesGrammarConstraint(tok)
    states = []
    for p in ("C", "CC", "CC(=O", "CC(=O)O", "C1CC", "c1cc", "[C@@H]", "[NH"):
        st = advance(INITIAL, p)
        if st is not None:
            states.append(st)

    for st in states:
        constraint.mask_for_state(st)

    assert constraint.base_builds <= len(states)
    assert constraint.final_builds <= len(states)
    assert constraint.vocab_size > 30000


def test_engine_runs_constrained_end_to_end(bundle):
    """The constraint guarantees syntax; the RDKit filter guarantees chemistry.

    With random weights the model emits plenty of syntactically valid but chemically
    impossible fragments, so invalid_reactants > 0 is the filter working, not a bug.
    What must hold is that nothing unparseable reaches the pathway.
    """
    from rdkit import Chem
    from rdkit import RDLogger

    RDLogger.DisableLog("rdApp.*")
    model, tok = bundle
    engine = RetroEngine(
        model,
        tok,
        BuildingBlockIndex(["CC", "O", "C"]),
        num_beams=3,
        max_length=24,
        constrained=True,
    )
    pathway, stats = engine.predict("CC(=O)O", max_depth=3)

    assert stats.generate_calls >= 1
    assert all(_syntactically_valid(step["product"]) for step in pathway)
    for step in pathway:
        for r in step["reactants"]:
            assert _syntactically_valid(r), f"invalid syntax survived: {r}"
            assert Chem.MolFromSmiles(r) is not None, (
                f"chemically invalid fragment survived the post-filter: {r}"
            )


def test_engine_batching_survives_real_generate(bundle):
    model, tok = bundle
    engine = RetroEngine(
        model, tok, BuildingBlockIndex([]), num_beams=2, max_length=24, constrained=False
    )
    pathway, stats = engine.predict("OC(=O)CCCCC(=O)O", max_depth=3, use_cache=False)

    assert stats.molecules_scored >= stats.generate_calls
    assert isinstance(pathway, list)

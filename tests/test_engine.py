import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import torch

from tbr_opt.engine import (
    BuildingBlockIndex,
    LRUCache,
    RetroEngine,
    canonicalize_smiles,
)

TINY = "hf-internal-testing/tiny-random-T5ForConditionalGeneration"


class FakeSeq2Seq:
    """Stand-in for the PEFT model that records how generate() was batched."""

    def __init__(self, tokenizer, mapping, default="CC.O"):
        self.tokenizer = tokenizer
        self.mapping = mapping
        self.default = default
        self.calls = []
        self._param = torch.zeros(1)

    def parameters(self):
        return iter([self._param])

    def generate(self, input_ids=None, attention_mask=None, **kwargs):
        texts = [t.replace(" ", "") for t in
                 self.tokenizer.batch_decode(input_ids, skip_special_tokens=True)]
        self.calls.append(texts)
        outs = [self.mapping.get(t, self.default) for t in texts]
        return self.tokenizer(outs, return_tensors="pt", padding=True).input_ids


@pytest.fixture(scope="module")
def tokenizer():
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(TINY)


def _engine(tokenizer, mapping, blocks=(), **kwargs):
    model = FakeSeq2Seq(tokenizer, mapping)
    kwargs.setdefault("constrained", False)
    eng = RetroEngine(model, tokenizer, BuildingBlockIndex(blocks), **kwargs)
    return eng, model


def test_canonicalize_unifies_equivalent_inputs():
    assert canonicalize_smiles("OC(C)=O") == canonicalize_smiles("CC(=O)O")
    assert canonicalize_smiles("C(C)O") == canonicalize_smiles("CCO")
    assert canonicalize_smiles("not a smiles") == "not a smiles"
    assert canonicalize_smiles("") == ""


def test_building_block_index_matches_raw_and_canonical():
    idx = BuildingBlockIndex(["CC(=O)O", "N=C(N)NCCC[C@H](N)C(=O)O"])
    assert "CC(=O)O" in idx
    assert "OC(C)=O" in idx, "canonical form of an indexed block must match"
    assert "CCO" not in idx
    assert len(idx) == 2


def test_building_block_index_from_csv():
    path = os.path.join(os.path.dirname(__file__), "..", "bio_building_block.csv")
    idx = BuildingBlockIndex.from_csv(path)
    assert len(idx) > 300
    assert "N=C(N)NCCC[C@H](N)C(=O)O" in idx


def test_lru_cache_evicts_oldest():
    cache = LRUCache(maxsize=2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert cache.get("b") is None, "b was the least recently used"
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert len(cache) == 2


def test_same_depth_nodes_are_batched_into_one_call(tokenizer):
    """Three siblings must be scored in a single generate() call, not three."""
    mapping = {
        "CCCC": "CCC.CCO.CC",
        "CCC": "CC.C",
        "CCO": "CC.O",
        "CC": "C.C",
    }
    eng, model = _engine(tokenizer, mapping, blocks=["C", "O"])
    pathway, stats = eng.predict("CCCC", max_depth=4)

    assert model.calls[0] == ["CCCC"]
    assert sorted(model.calls[1]) == sorted(["CCC", "CCO", "CC"]), (
        f"siblings were not batched together: {model.calls[1]}"
    )
    assert stats.molecules_scored == 4
    assert stats.generate_calls == 2
    assert stats.as_dict()["avg_batch_size"] == 2.0
    assert pathway[0]["product"] == "CCCC"
    assert pathway[0]["depth"] == 1


def test_shared_intermediate_is_scored_once(tokenizer):
    """A diamond dependency must not score the shared node twice.

    Within one search this is the `expanded` set doing the work; the LRU cache is what
    carries the saving across separate queries (see test_cache_serves_a_repeat_query).
    """
    mapping = {"CCCC": "CCC.CCO", "CCC": "CCO", "CCO": "CC.O"}
    eng, model = _engine(tokenizer, mapping, blocks=["CC", "O"])
    _pathway, stats = eng.predict("CCCC", max_depth=5)

    scored = [m for call in model.calls for m in call]
    assert scored.count("CCO") == 1, f"CCO was recomputed: {scored}"
    assert stats.duplicates_pruned >= 1, "shared node was not recognised as a repeat"
    assert stats.molecules_scored == 3


def test_cache_serves_a_repeat_query_for_free(tokenizer):
    mapping = {"CCCC": "CC.CC", "CC": "C.C"}
    eng, model = _engine(tokenizer, mapping, blocks=["C"])
    eng.predict("CCCC", max_depth=3)
    calls_first = len(model.calls)

    _pathway, stats = eng.predict("CCCC", max_depth=3)
    assert len(model.calls) == calls_first, "second query hit the model again"
    assert stats.generate_calls == 0
    assert stats.cache_hits > 0


def test_cache_key_is_canonical(tokenizer):
    mapping = {"CC(=O)O": "CC.O"}
    eng, model = _engine(tokenizer, mapping, blocks=["CC", "O"])
    eng.predict("CC(=O)O", max_depth=2)
    calls = len(model.calls)

    _pathway, stats = eng.predict("OC(C)=O", max_depth=2)
    assert len(model.calls) == calls
    assert stats.cache_hits == 1


def test_cache_can_be_disabled(tokenizer):
    mapping = {"CCCC": "CC.CC", "CC": "C.C"}
    eng, model = _engine(tokenizer, mapping, blocks=["C"])
    eng.predict("CCCC", max_depth=3)
    calls = len(model.calls)
    eng.predict("CCCC", max_depth=3, use_cache=False)
    assert len(model.calls) > calls


def test_building_block_halts_expansion(tokenizer):
    mapping = {"CCCC": "CC.CC", "CC": "C.C"}
    eng, model = _engine(tokenizer, mapping, blocks=["CC"])
    pathway, _stats = eng.predict("CCCC", max_depth=5)

    assert len(pathway) == 1, f"building block was expanded: {pathway}"
    assert [m for call in model.calls for m in call] == ["CCCC"]


def test_invalid_reactants_are_dropped_not_forwarded(tokenizer):
    """Unparseable fragments must never reach the UI, where st.image(None) raises."""
    mapping = {"CCCC": "CC.notavalidsmiles.C(O"}
    eng, _model = _engine(tokenizer, mapping, blocks=["CC"])
    pathway, stats = eng.predict("CCCC", max_depth=2)

    assert pathway[0]["reactants"] == ["CC"]
    assert stats.invalid_reactants == 2


def test_cycle_terminates(tokenizer):
    mapping = {"CC": "CCO", "CCO": "CC"}
    eng, _model = _engine(tokenizer, mapping, blocks=[])
    pathway, stats = eng.predict("CC", max_depth=10)

    assert len(pathway) == 2, f"cycle was not broken: {pathway}"
    assert stats.duplicates_pruned >= 1


def test_max_depth_is_respected(tokenizer):
    mapping = {"C" * n: "C" * (n - 1) for n in range(2, 40)}
    eng, model = _engine(tokenizer, mapping, blocks=[])
    pathway, _stats = eng.predict("C" * 20, max_depth=3)

    assert len(pathway) == 3
    assert len(model.calls) == 3
    assert max(step["depth"] for step in pathway) == 3


def test_pathway_shape_matches_legacy_contract(tokenizer):
    mapping = {"CCCC": "CC.CC"}
    eng, _model = _engine(tokenizer, mapping, blocks=["CC"])
    pathway, _stats = eng.predict("CCCC", max_depth=2)

    step = pathway[0]
    assert set(step) == {"product", "reactants", "depth"}
    assert isinstance(step["reactants"], list)
    assert all(isinstance(r, str) for r in step["reactants"])


def test_batch_size_splits_large_frontiers(tokenizer):
    """Six distinct siblings with batch_size=4 must split into calls of 4 then 2."""
    siblings = ["CCC", "CCO", "CCN", "CCS", "CCCl", "CCBr"]
    mapping = {"CCCCCCCC": ".".join(siblings)}
    mapping.update({s: "CC.O" for s in siblings})
    eng, model = _engine(
        tokenizer,
        mapping,
        blocks=["CC", "O", "C"],
        batch_size=4,
    )
    _pathway, stats = eng.predict("CCCCCCCC", max_depth=3)

    sizes = [len(c) for c in model.calls]
    assert sizes == [1, 4, 2], f"unexpected batch split: {sizes}"
    assert max(sizes) <= 4
    assert stats.generate_calls == 3
    assert stats.molecules_scored == 7


def test_empty_and_whitespace_input(tokenizer):
    eng, model = _engine(tokenizer, {}, blocks=[])
    pathway, stats = eng.predict("   ", max_depth=3)
    assert pathway == []
    assert model.calls == []
    assert stats.generate_calls == 0


def test_package_exports_the_names_the_app_imports():
    """net_app.py imports from the package root, not the submodules.

    A missing re-export here is invisible to py_compile and to tests that import
    tbr_opt.engine directly, so the app breaks only at runtime.
    """
    import tbr_opt

    required = ["RetroEngine", "BuildingBlockIndex", "SmilesGrammarConstraint",
                "canonicalize_smiles", "LRUCache", "SmilesStateMachine"]
    missing = [n for n in required if not hasattr(tbr_opt, n)]
    assert not missing, f"not re-exported from tbr_opt: {missing}"
    assert set(required) <= set(tbr_opt.__all__)

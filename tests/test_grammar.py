import csv
import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rdkit import Chem
from rdkit import RDLogger

from tbr_opt.grammar import (
    INITIAL,
    SmilesGrammarConstraint,
    SmilesStateMachine,
    advance,
    base_key,
    is_terminal,
)

RDLogger.DisableLog("rdApp.*")

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "bio_building_block.csv")


def _load_blocks():
    with open(CSV_PATH, newline="") as fh:
        return [row[0].strip() for row in csv.reader(fh) if row and row[0].strip()]


def _accepts(text):
    st = advance(INITIAL, text)
    return st is not None and is_terminal(st)


VALID_EXTRA = [
    "CC(=O)O",
    "O=C(O)c1ccccc1",
    "C1CC1",
    "C%10CC%10",
    "c1ccc2ccccc2c1",
    "CC.O",
    "CC(=O)O.CCO",
    "c1cc[nH]c1",
    "C/C=C/C",
    "*C",
    "[NH3+][C@@H](C)C(=O)[O-]",
    "[13CH4]",
    "[C@@H]1CCCC[NH+]1",
    "O=[N+]([O-])c1ccccc1",
    "CC(C)(C)OC(=O)N",
    "F/C(F)=C/F",
    "[H]C([H])([H])O",
    "C#N",
    "OS(=O)(=O)O",
    "[Se]",
    "[as]",
    "CN1CCC[C@H]1c1cccnc1",
    "C1CC(C1)C",
    "C1(O)CCC1",
    "C1CC1",
    "[C@TH1]",
    "[C@SP3]",
    "[C@TB1]",
    "[C@AL1]",
    "[C@OH1]",
    "C12CCC1CC2",
]

INVALID = [
    "",
    "C((O)",
    "C)",
    "C1CC",
    "[C",
    ")C",
    "C..",
    ".C",
    ".",
    "1CC",
    "=",
    "=C",
    "C=",
    "Xy",
    "C(H",
    "[]",
    "[%]",
    "[C@@HH]",
    "C(C",
    "(C)",
    "C()",
    "CC(=O))",
    "[Na",
    "C%1",
    "%CC",
    "C-",
    "c1ccc",
    "C11",
    "c11",
    "C1=N1",
    "OCC1(O)[C@@H]1O",
    "O=(CO)C",
    "B5=5",
    "[C@SH]",
    "[C@CH]",
    "[C@HB]",
    "[C@n@H]",
    "[C:@H]",
]


def test_accepts_every_parseable_building_block():
    blocks = _load_blocks()
    assert len(blocks) > 300, f"expected a real CSV, got {len(blocks)} rows"
    parseable = [b for b in blocks if Chem.MolFromSmiles(b) is not None]
    assert len(parseable) > 300
    bad = [b for b in parseable if not _accepts(b)]
    assert not bad, f"grammar rejected {len(bad)} RDKit-valid building blocks: {bad[:10]}"


def test_matches_rdkit_on_dataset_placeholders():
    """The CSV uses "[CoA]" as a coenzyme-A pseudo-atom placeholder.

    RDKit cannot parse those rows, so the grammar must reject them too. If this count
    changes, the dataset changed.
    """
    blocks = _load_blocks()
    unparseable = [b for b in blocks if Chem.MolFromSmiles(b) is None]
    assert len(unparseable) == 32, f"expected 32 placeholders, got {len(unparseable)}"
    assert all("[CoA]" in b for b in unparseable)
    assert not any(_accepts(b) for b in unparseable)


def test_valid_extra():
    bad = [s for s in VALID_EXTRA if not _accepts(s)]
    assert not bad, f"grammar rejected valid SMILES: {bad}"


def test_invalid_rejected():
    good = [s for s in INVALID if _accepts(s)]
    assert not good, f"grammar accepted invalid SMILES: {good}"


_ADJACENT_RINGS = re.compile(r"(\d)(\d)")


def _is_duplicate_ring_path(s):
    """Two ring ids opened on one atom and closed on one atom.

    "n23cnc32" bonds the same atom pair twice. Deciding that needs graph traversal, not
    a token-stream grammar, so it is the one syntactic case left to the RDKit filter.
    """
    pairs = [frozenset(m) for m in _ADJACENT_RINGS.findall(s)]
    return any(pairs.count(p) >= 2 for p in pairs)


def test_no_syntactic_false_positives_against_rdkit():
    """Grammar acceptance must imply RDKit can parse the syntax.

    Compared against sanitize=False because valence and aromaticity perception are not
    decidable from a token stream - those are caught by the engine's RDKit post-filter.
    Mutations of real building blocks give near-miss malformed strings, which is exactly
    the distribution a constrained decoder has to reject.
    """
    rng = random.Random(1234)
    blocks = _load_blocks()
    alphabet = "()[]%.=-#:123456789CNOSFClBr*abcnops"

    known_limitation = []
    unexpected = []
    checked = 0
    for _ in range(4000):
        base = rng.choice(blocks)
        mode = rng.randrange(4)
        if mode == 0:
            i = rng.randrange(len(base) + 1)
            cand = base[:i] + rng.choice(alphabet) + base[i:]
        elif mode == 1 and base:
            i = rng.randrange(len(base))
            cand = base[:i] + base[i + 1 :]
        elif mode == 2 and len(base) > 1:
            i, j = sorted(rng.sample(range(len(base)), 2))
            cand = base[:i] + base[j:]
        else:
            cand = "".join(rng.choice(alphabet) for _ in range(rng.randrange(1, 24)))

        checked += 1
        if _accepts(cand) and Chem.MolFromSmiles(cand, sanitize=False) is None:
            if _is_duplicate_ring_path(cand):
                known_limitation.append(cand)
            else:
                unexpected.append(cand)

    assert checked > 3000
    assert not unexpected, (
        f"{len(unexpected)} strings accepted by grammar but syntactically rejected by "
        f"RDKit, outside the documented duplicate-ring-path limitation: {unexpected[:15]}"
    )
    assert len(known_limitation) <= 5, (
        f"duplicate-ring-path leakage grew to {len(known_limitation)}; the grammar may "
        f"have regressed elsewhere: {known_limitation[:10]}"
    )


def test_known_limitation_duplicate_ring_path():
    """Pins down the one syntactic case the grammar cannot decide.

    Detected by RDKit in engine._split_valid, so the pipeline as a whole is still safe -
    the constraint just does not spend beam slots avoiding it.
    """
    s = "n23cnc32"
    assert _accepts(s), "grammar is expected to pass this"
    assert Chem.MolFromSmiles(s, sanitize=False) is None
    assert _is_duplicate_ring_path(s)


def test_chemical_validity_is_the_post_filter_job():
    """The two layers are complementary, not redundant.

    An aromatic five-carbon ring is syntactically fine but chemically impossible when
    neutral, so the grammar accepts it and sanitization must not.
    """
    s = "O=C(O)c1cccc1C(=O)O"
    assert _accepts(s), "grammar should pass syntax"
    assert Chem.MolFromSmiles(s, sanitize=False) is not None
    assert Chem.MolFromSmiles(s) is None, "sanitizing parse should reject valence"


def test_state_machine_is_incremental():
    """Feeding a SMILES in arbitrary chunks must equal feeding it whole."""
    rng = random.Random(7)
    for s in _load_blocks()[:60]:
        whole = advance(INITIAL, s)
        sm = SmilesStateMachine()
        i = 0
        while i < len(s):
            step = rng.randrange(1, 4)
            sm.feed(s[i : i + step])
            i += step
        assert sm.state == whole, f"chunked state diverged for {s}"


class FakeTokenizer:
    """Minimal tokenizer surface so the constraint is testable without a model."""

    def __init__(self, pieces):
        self._vocab = {p: i for i, p in enumerate(pieces)}
        self.eos_token_id = self._vocab["</s>"]
        self.pad_token_id = self._vocab["<pad>"]
        self.unk_token_id = self._vocab["<unk>"]
        self.bos_token_id = None

    def get_vocab(self):
        return dict(self._vocab)

    def batch_decode(self, ids, skip_special_tokens=True):
        inv = {i: t for t, i in self._vocab.items()}
        special = {self.eos_token_id, self.pad_token_id, self.unk_token_id}
        out = []
        for row in ids:
            toks = [inv[int(x)] for x in row]
            if skip_special_tokens:
                toks = [t for i, t in zip(row, toks) if int(i) not in special]
            out.append("".join(toks))
        return out


_PIECES = [
    "</s>", "<pad>", "<unk>",
    "C", "N", "O", "S", "Cl", "Br", "c", "n", "o", "s", "*",
    "(", ")", "[", "]", ".", "=", "-", "#", ":", "/", "\\", "%",
    "1", "2", "3", "0", "9",
    "C1", "C2", "c1", "1C", "=O", "(O)", "(=O)", "O)", "[C@@H]", "[nH]", "[NH",
    "@@", "H]", "C(=O)O", "cc", "%10", "%1", "C%10", "Oc1", "1)", "[O-]", "[N+]",
    "CC", "CN", "OC", "12", "C12", "H", "@", "+",
]


def _reachable_states(rng, count):
    alphabet = "CNOS()[]=.123%*-cno"
    states = []
    for _ in range(count * 12):
        if len(states) >= count:
            break
        s = "".join(rng.choice(alphabet) for _ in range(rng.randrange(1, 16)))
        st = advance(INITIAL, s)
        if st is not None:
            states.append((st, s))
    return states


def test_mask_matches_brute_force():
    """The two-tier mask cache must be exactly equivalent to per-token evaluation.

    If this drifts, constrained decoding silently admits invalid molecules or starves
    the beam to all-masked and emits nothing.
    """
    import torch

    tok = FakeTokenizer(_PIECES)
    constraint = SmilesGrammarConstraint(tok)
    strs = constraint.token_strs
    specials = constraint._special
    eos = constraint.eos_id

    rng = random.Random(4242)
    states = _reachable_states(rng, 400)
    assert len(states) > 200, "failed to generate enough reachable states"

    seen_ring_states = 0
    for st, _ in states:
        if st[2]:
            seen_ring_states += 1
        mask = constraint.mask_for_state(st)
        terminal = is_terminal(st)
        for idx in range(constraint.vocab_size):
            if idx == eos:
                expected = terminal
            elif idx in specials or not strs[idx]:
                expected = False
            else:
                expected = advance(st, strs[idx]) is not None
            assert bool(mask[idx]) is expected, (
                f"mask disagrees at token {strs[idx]!r} for state {st}"
            )

    assert seen_ring_states > 0, "test never exercised an open-ring state"
    assert constraint.base_builds < len(states), "base mask cache did not dedupe"
    assert isinstance(mask, torch.Tensor)


def test_mask_cache_reused_across_ring_configs():
    """Ring state must not force a full-vocabulary rebuild."""
    tok = FakeTokenizer(_PIECES)
    constraint = SmilesGrammarConstraint(tok)
    # Age caps at 2, so "C1CC" and "C1CCC" are the same state; use an immature ring
    # against a mature one to get differing ring state under an identical base key.
    s_young = advance(INITIAL, "C1C")
    s_mature = advance(INITIAL, "C1CCC")
    assert s_young[2] and s_mature[2]
    assert s_young[2] != s_mature[2]
    assert base_key(s_young) == base_key(s_mature), "base key should ignore ring contents"

    constraint.mask_for_state(s_young)
    builds_after_first = constraint.base_builds
    constraint.mask_for_state(s_mature)
    assert constraint.base_builds == builds_after_first, "base mask was rebuilt"
    assert not constraint.mask_for_state(s_young).equal(constraint.mask_for_state(s_mature))


def test_eos_only_when_terminal():
    assert is_terminal(advance(INITIAL, "CC(=O)O"))
    assert not is_terminal(advance(INITIAL, "CC(=O"))
    assert not is_terminal(advance(INITIAL, "C1CC"))
    assert not is_terminal(advance(INITIAL, "CC."))

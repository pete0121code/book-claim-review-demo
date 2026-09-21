#!/usr/bin/env python3
"""
Regenerate the synthetic engine blocks in claims.json.

WHY THIS EXISTS
---------------
The first version of this demo gave every engine the same 90-character string:
"Placeholder reasoning for the demo." Across 141 cards that is not a demo, it is
a wireframe. A designer sizing a card for real content cannot see that a real
suggestion runs three or four sentences, that two engines write to different
lengths, or that the card has to survive one engine citing nothing at all.

⛔ WHAT THIS DELIBERATELY DOES NOT DO
------------------------------------
It never writes a medical assertion. Not one line here says what a drug does,
what a rate is, or what a study found. That is not squeamishness -- it is what
the real reviewer output actually looks like. A claim reviewer is not asked
"is this true"; it is asked "is this sentence carrying its evidence honestly".
So the reasoning talks about attribution, population, study phase, hedging and
overreach. All of that is real reviewer work and none of it requires inventing
a fact about a real drug that appears in an invented sentence.

The sentences in this corpus name real substances. If this file wrote
"published estimates run 5-10%" next to one of them, that number would be
fabricated, attached to a real drug, and sitting in a public repository looking
exactly like a finding. The shape is what design needs; the claims are not.
"""

import json
import pathlib
import random

HERE = pathlib.Path(__file__).resolve().parent

# Deterministic: the same corpus must rebuild byte-identical, or the build gate
# in build_site.py cannot tell a real change from reshuffled noise.
SEED = 20260921

# ---------------------------------------------------------------------------
# Reasoning, keyed by verdict. Several variants each so no two cards read alike.
# Every variant is about how the sentence handles evidence -- never about the
# underlying subject matter.
# ---------------------------------------------------------------------------
REASONING = {
    "ok": [
        "The sentence stays inside what its source supports. It names the effect, does not "
        "quantify it, and does not extend it to a group the underlying work did not study. "
        "Nothing here needs to change.",
        "This is carefully hedged. The verb does the work the evidence can carry, and the "
        "sentence stops before the point where it would need a number to stand up.",
        "Checked against the citation and the surrounding paragraph. The claim and the source "
        "agree on scope, and the sentence does not borrow authority from the paragraph above it.",
    ],
    "source": [
        "The figure is stated without attribution. Nothing in the paragraph points to where it "
        "came from, so a reader cannot check it and a fact-checker cannot confirm it. Either a "
        "citation goes in or the number comes out.",
        "No source is offered for the specific quantity. The general claim around it is "
        "supportable, but the number is the part a reader will remember and repeat, and it is "
        "the part with nothing behind it.",
        "The sentence cites nothing. That may be fine in a passage that is clearly framed as "
        "background, but this one reads as a finding, and a finding needs a reference.",
    ],
    "population": [
        "The work behind this looked at a narrower group than the sentence implies. Written this "
        "way a reader applies it to themselves regardless of whether they resemble the people "
        "studied. Naming the group would fix it without weakening the point.",
        "The sentence generalises past its evidence. What was observed in a defined cohort is "
        "stated here as though it holds broadly. The distinction matters most to exactly the "
        "reader who is deciding whether it applies to them.",
        "Scope mismatch between claim and source. The underlying population is specific; the "
        "sentence is not. Adding the qualifier costs six words.",
    ],
    "preclinical": [
        "The evidence behind this is preclinical and the sentence does not say so. A reader has "
        "no way to tell from the text that this has not been shown in people, and the phrasing "
        "does not signal it.",
        "This describes laboratory work in language usually reserved for clinical findings. The "
        "result may be real and still not mean what a reader will take it to mean. Label the "
        "stage.",
        "Stage is unmarked. Everything in the sentence is consistent with the source, but the "
        "source is early-stage and the sentence reads as settled.",
    ],
    "misleading": [
        "Each clause is defensible and the sentence as a whole is not. Placing them together "
        "implies a causal link that neither half establishes. This is the failure mode worth "
        "catching, because nothing in it is technically false.",
        "Literally accurate, directionally wrong. The framing invites a conclusion the evidence "
        "does not reach, and a reader will take the conclusion rather than the qualifier.",
        "The sentence is true and the impression it leaves is not. Reordering it, or moving the "
        "qualifier out of the subordinate clause, would resolve it.",
    ],
    "disputed": [
        "This is contested in the literature and the sentence presents it as settled. Reporting "
        "the disagreement is legitimate; resolving it in one direction without saying so is not.",
        "Sources conflict on this point. The sentence picks a side silently. A reader cannot tell "
        "that an alternative reading exists, which is the part that needs fixing.",
        "There is a genuine dispute here. The sentence is defensible as one position among "
        "several but is not written as a position -- it is written as a fact.",
    ],
    "rewrite": [
        "The underlying point is supportable but the sentence cannot be repaired by adding a "
        "citation. The structure is what causes the problem, so this needs rewriting rather "
        "than annotating.",
        "Several issues at once: unattributed quantity, scope broader than the source, and a "
        "verb stronger than the evidence. Fixing them one at a time will produce an awkward "
        "sentence; recasting it will not.",
        "This should be rewritten. As written it carries more certainty than any single source "
        "behind it, and trimming will leave the sentence unbalanced.",
    ],
    "notclaim": [
        "This is not a factual claim. It is a transition and carries no assertion to check. "
        "Flagged only because it sits next to a sentence that does.",
        "Nothing here to verify. The sentence sets up the paragraph rather than asserting "
        "anything about the world.",
        "Narrative rather than claim. No source is required and none is missing.",
    ],
}

# Riffs appended for particular claim kinds, so a dose claim and a narrative claim
# do not read identically even under the same verdict.
KIND_RIFF = {
    "dose": "Because this is a dose, the tolerance for imprecision is lower than elsewhere in "
            "the chapter -- a reader may act on it directly.",
    "product": "This names a product, so the sentence carries commercial weight whether or not "
               "it intends to.",
    "number": "The number is the load-bearing part of this sentence; everything else around it "
              "is qualifier.",
    "regulatory": "Regulatory status changes by jurisdiction and over time, so an unqualified "
                  "statement here dates badly.",
    "safety": "This is a safety statement, which raises the bar: an omission here is not "
              "symmetrical with an overstatement.",
    "outcome": "Patient outcomes are the claims a reader is most likely to repeat to their own "
               "clinician.",
    "mechanism": "A mechanistic explanation reads as established even when it is a hypothesis.",
    "advice": "Phrased as guidance, which shifts it from description to recommendation.",
}

CONFIDENCE = ["low", "medium", "high"]


def synth_source(rng, verdict):
    """Synthetic identifiers only. 00000001-00000025 and NCT00000001-style ids are
    reserved demo values -- they do not resolve to a real record, which is the point.
    Some blocks return "" so the card's no-source state is exercised in the demo."""
    if verdict in ("notclaim",):
        return ""
    roll = rng.random()
    if roll < 0.18:
        return ""                                    # exercise the "cited nothing" path
    if roll < 0.30:
        return f"NCT{rng.randint(1, 25):08d}"
    if roll < 0.45:                                  # two sources, exercises the stacked row
        a, b = rng.sample(range(1, 26), 2)
        return f"PMID {a:08d}; PMID {b:08d}"
    return f"PMID {rng.randint(1, 25):08d}"


def build_why(rng, verdict, kinds):
    body = rng.choice(REASONING.get(verdict, REASONING["ok"]))
    for k in kinds or []:
        if k in KIND_RIFF and rng.random() < 0.55:
            return body + " " + KIND_RIFF[k]
    return body


def main():
    path = HERE / "claims.json"
    data = json.loads(path.read_text())
    claims = data["claims"] if isinstance(data, dict) and "claims" in data else data

    rng = random.Random(SEED)
    touched = 0
    for c in claims:
        eng = c.get("engines")
        if not eng:
            continue
        for name, block in eng.items():
            verdict = block.get("verdict", "ok")
            block["why"] = build_why(rng, verdict, c.get("kinds"))
            block["confidence"] = rng.choice(CONFIDENCE)
            block["source"] = synth_source(rng, verdict)
            touched += 1

    path.write_text(json.dumps(data, ensure_ascii=False, indent=1))

    lens = [len(b["why"]) for c in claims if c.get("engines") for b in c["engines"].values()]
    print(f"rewrote {touched} engine blocks across {sum(1 for c in claims if c.get('engines'))} claims")
    print(f"reasoning length: min {min(lens)}, median {sorted(lens)[len(lens)//2]}, max {max(lens)} chars")
    print(f"(was 118 chars on every single one)")
    blank = sum(1 for c in claims if c.get("engines")
                for b in c["engines"].values() if not b["source"])
    print(f"blocks citing nothing: {blank} — the no-source card state is exercised")


if __name__ == "__main__":
    main()

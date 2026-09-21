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

# ---------------------------------------------------------------------------
# CITATIONS WITH THEIR RATIONALE.
#
# ⛔ A BARE IDENTIFIER IS NOT A CITATION. "PMID 00000023" tells a reviewing
# physician nothing they can act on. The real tool already showed title,
# journal, year, study design and a "Shows:" line -- and a first pass at
# simplifying this replaced all of that with "paper 1 · paper 2", which was a
# regression dressed up as clarity. Simplify the LANGUAGE, never the EVIDENCE.
#
# Each citation therefore carries four things, and the fourth is the one that
# is usually missing everywhere:
#   design  what kind of study it is, so its weight is visible
#   shows   what the paper itself reported
#   why     what it has to do with THIS sentence
# "why" is the documentation the project owner asked for: not just which paper, but why
# that paper was thought relevant here. Without it a reader cannot tell a
# well-matched citation from a keyword collision -- and keyword collisions are
# exactly how a paper about the wrong subject ends up attached to a drug claim.
#
# Every field below describes a SYNTHETIC paper. No real title, no real
# finding, no real author. The shapes are real; the content is invented.
# ---------------------------------------------------------------------------
DESIGNS = [
    ("Systematic review", "pooled across the published trials"),
    ("Randomised controlled trial", "the strongest single design here"),
    ("Cohort study", "observational, so association rather than cause"),
    ("Case series", "a small number of patients, no comparison group"),
    ("Laboratory study", "cells or tissue, not people"),
    ("Animal study", "not yet shown in humans"),
    ("Narrative review", "a summary, not new data"),
]

SHOWS = [
    "an effect in the direction the sentence describes, with wide confidence intervals",
    "no difference between the groups on the primary outcome",
    "a benefit confined to the subgroup that had already failed first-line treatment",
    "a smaller effect than earlier reports, which the authors attribute to blinding",
    "the mechanism the sentence assumes, but only in cell culture",
    "an association that did not survive adjustment for confounders",
    "improvement on a surrogate marker, with no outcome data",
    "harms at the dose range the sentence mentions",
]

WHY = {
    "ok":          "Cited as the direct support for the claim. Scope and population match.",
    "source":      "The closest published estimate to the figure in the sentence — offered as the "
                   "citation the sentence is missing, not as confirmation the figure is right.",
    "population":  "Cited because it defines the population the finding actually came from, which "
                   "is narrower than the sentence implies.",
    "preclinical": "Cited to show the stage of the evidence: this is where the claim originates, "
                   "and it is not a human study.",
    "misleading":  "Cited because it reports the qualifier the sentence leaves out.",
    "disputed":    "Cited as the opposing result — it is why this point cannot be stated as settled.",
    "rewrite":     "Cited to show the gap between what the source supports and what the sentence says.",
    "notclaim":    "Attached for context only; there is no claim here to support.",
}

TITLE_A = ["Outcomes", "Response rates", "Tolerability", "Long-term follow-up", "Dose-finding",
           "Comparative effectiveness", "Mechanistic evaluation", "Safety profile"]
TITLE_B = ["in previously treated patients", "in a community setting", "after first-line failure",
           "in an unselected population", "in a preclinical model", "across three centres",
           "in older adults", "at standard dosing"]
JOURNALS = ["J. Sample Oncology", "Demo Clinical Research", "Review of Invented Medicine",
            "Synthetic Trials Quarterly", "Journal of Placeholder Studies"]


def rich_sources(rng, verdict):
    """Zero, one or two fully-documented synthetic citations."""
    if verdict == "notclaim" or rng.random() < 0.18:
        return []                       # exercises the no-source state
    n = 2 if rng.random() < 0.35 else 1
    out = []
    for _ in range(n):
        design, weight = rng.choice(DESIGNS)
        out.append({
            "pmid":    "%08d" % rng.randint(1, 25),
            "title":   "%s %s" % (rng.choice(TITLE_A), rng.choice(TITLE_B)),
            "journal": rng.choice(JOURNALS),
            "year":    str(rng.randint(2009, 2025)),
            "design":  "%s — %s" % (design, weight),
            "shows":   rng.choice(SHOWS),
            "why":     WHY.get(verdict, WHY["ok"]),
        })
    return out

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
            block["resolved"] = rich_sources(rng, verdict)
            # e.source is the engine's own prose citation string. It is shown even when
            # something resolved -- see the comment on researchRows in build_site.py.
            block["source"] = "" if block["resolved"] else synth_source(rng, verdict)
            touched += 1

    path.write_text(json.dumps(data, ensure_ascii=False, indent=1))

    lens = [len(b["why"]) for c in claims if c.get("engines") for b in c["engines"].values()]
    print(f"rewrote {touched} engine blocks across {sum(1 for c in claims if c.get('engines'))} claims")
    print(f"reasoning length: min {min(lens)}, median {sorted(lens)[len(lens)//2]}, max {max(lens)} chars")
    print(f"(was 118 chars on every single one)")
    # ⛔ COUNT WHAT YOU MEAN. The first version of this line tested `not b["source"]`,
    # but a block with rich resolved[] citations deliberately has an EMPTY source
    # string -- so every well-cited block was counted as uncited and the number
    # jumped from 52 to 158. The statistic was wrong, not the data.
    blank = sum(1 for c in claims if c.get("engines")
                for b in c["engines"].values() if not b["resolved"] and not b["source"])
    rich = sum(1 for c in claims if c.get("engines")
               for b in c["engines"].values() if b["resolved"])
    two = sum(1 for c in claims if c.get("engines")
              for b in c["engines"].values() if len(b["resolved"]) > 1)
    print(f"blocks with documented citations: {rich} ({two} carry two)")
    print(f"blocks citing nothing: {blank} — the no-source card state is exercised")


if __name__ == "__main__":
    main()

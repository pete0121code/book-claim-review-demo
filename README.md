# Book claim review — design demo

A reviewing tool for fact-checking a long manuscript **sentence by sentence**. This
repository is a **synthetic copy** built for design work: the interface is the real
one, every sentence in it is invented.

## What the real tool does

A physician has to work through a book-length manuscript and decide, claim by claim,
what is safe to print. The real register holds **5,095 sentences**; **1,634** carry a
verdict from one or more automated reviewers. The tool's job is to make that survivable:
find the claims that matter, show the evidence beside each one, and record a decision.

Each card carries, in this order:

1. **The sentence**, with its chapter, paragraph and a link to it in the manuscript
2. **Why it was flagged** — dose, named drug, patient outcome, regulatory status, and so on
3. **A known factual error** where a human reviewer has already identified one, with the proposed replacement
4. **Engine review** — one or more automated verdicts, labelled by engine, with sources. Where engines disagree the card is marked so the human reads it themselves
5. **Prior work** — where the organisation has already adjudicated the same topic elsewhere, with the study design and what it actually showed
6. **Eight verdict buttons** the reviewer chooses from, plus a note and a source field

## What needs design help

The tool is honest and dense. It is **not** pleasant to spend an afternoon in, and an
afternoon is exactly what it asks for.

- **Density** — a single card can carry six stacked blocks. Everything on it earns its
  place, but the hierarchy is flat: a fabricated-citation warning looks much like a
  routine note.
- **Progress and orientation** — a reviewer has no sense of where they are in 1,634
  claims, what they have done, or what remains. The footer shows a bare count.
- **The verdict row** — eight buttons of equal weight. The common choices and the rare,
  consequential ones are indistinguishable.
- **Reading rhythm** — reviewing is long, repetitive work. Nothing in the layout supports
  a rhythm or makes finishing a chapter feel like anything.
- **Disagreement** — when two reviewers conflict, that is the most valuable card in the
  set. It currently gets an amber border.
- **Mobile** — it works, but it was designed at desk width.

## Constraints that are not negotiable

- **No verdict may be implied by styling.** A card must never look decided when it is not.
- **Uncertainty has to survive the redesign.** "Engines disagree", "animals only",
  "true but misleading" are the point, not noise to tidy away.
- **Single HTML file, no build step, no framework.** It is served behind a password gate
  as static files, and must stay legible to whoever inherits it.
- **Works offline and in dark mode.**

## Run it

```
cd site && python3 -m http.server 8000 --bind 127.0.0.1
```
Then open http://127.0.0.1:8000/

`site/index.html` is the whole application. `site/claims.json` is the synthetic data.

## What is NOT here

The manuscript, the real claims, the real citations, the reviewers' verdicts, and the
password-gated deployment. This repository contains none of them by design.

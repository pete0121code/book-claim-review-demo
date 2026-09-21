# Book claim review — design demo

A reviewing tool for fact-checking a long manuscript **sentence by sentence**. This
repository is a **synthetic copy** built for design work: the interface is the real
one, every sentence in it is invented.

## What the real tool does

A physician has to work through a book-length manuscript and decide, claim by claim,
what is safe to print. The tool's job is to make that survivable: find the claims that
matter, show the evidence beside each one, and record a decision.

**This demo** holds **454 invented sentences**, **141** of which carry an automated-reviewer
block. None carries a decision — the verdict buttons start empty so you can click them.

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
- **Progress and orientation** — a reviewer has no sense of where they are in the
  claim list, what they have done, or what remains. The footer shows a bare count.
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
deployment they live in. This repository contains none of them by design.

## What is in here (updated 2026-09-20 — now the WHOLE site, not one page)

This mirrors **every template** in the real reviewing tool, built by the **real generators** running
against synthetic data. Restyle any of these and the change ports straight back.

| Page | Template | What it is |
|---|---|---|
| `site/index.html` | the reviewer desk | the main surface — one card per sentence, 8 verdict buttons, engine block, prior-review block, correction block |
| `site/text/index.html` | chapter index | jump list into the manuscript |
| `site/text/ch-01..06.html` | chapter page | the text itself, every sentence anchored, priority sentences underlined |
| `site/sources.html` | citation table | every identifier an engine cited |
| `site/questions.html` | author questions | sentences whose numbers trace to nothing |
| `site/corrections/index.html` | corrections sheet | the factual-error list, linked back into the review |

**The generators ship too** — `build_site.py`, `build_book.py`, `build_corrections.py`. You asked
where a restyle should land so it does not get overwritten: it lands in these three files, which
emit the HTML and hold the CSS. Editing a generated `.html` alone would be wiped on the next build.

## What is real and what is not

- **Real:** every template, all the CSS, the DOM structure, the interaction model, the generators.
- **Synthetic:** all 454 sentences across 6 invented chapters, all citations, all corrections, all
  author questions. Names are `A. Author` / `B. Author`; the manuscript is `Sample Manuscript`.
- **Verified before hand-off** (whole repo, 19 files, not just the page): 0 real manuscript
  sentences, 0 occurrences of the real title, either author, the institute, or the internal
  hostnames; 0 real citation identifiers. The check runs with a positive control, so a silently
  broken scan cannot pass.

The design work needs the templates, not the text — so this repository ships the templates
and a synthetic manuscript to fill them.

# Scoring model

The local scorer in `scripts/score_text.py` is a **synthetic-risk heuristic**, not a claim that text is AI-generated.

Its job is narrower:
- identify explainable patterns that often make prose look templated, detector-flagged, or insufficiently grounded
- give the agent concrete rewrite targets
- provide a stable before/after loop inside the skill

## Why the model focuses on these features

These dimensions are grounded in public detector documentation and stylometry research:

- **Predictability / burstiness / generic style**
  - GPTZero says detectors look at predictability, sentence-length variation, and whether tone/style is overly generic or repetitive.
  - Source: [GPTZero AI Vocabulary FAQ](https://gptzero.me/ai-vocabulary)

- **False positives in generic intros and conclusions**
  - Turnitin says it saw more false positives in the first and last few sentences when they were written in a generic way.
  - Source: [Turnitin AI writing detection model notes](https://guides.turnitin.com/hc/en-us/articles/28294949544717-AI-writing-detection-model)

- **Stylometric and readability features**
  - Lightweight detection work explicitly uses stylometric and readability features rather than only large neural models.
  - Sources:
    - [A Lightweight Approach to Detection of AI-Generated Texts Using Stylometric Features](https://arxiv.org/abs/2511.21744)
    - [Distinguishing AI-Generated and Human-Written Text Through Psycholinguistic Analysis](https://arxiv.org/abs/2505.01800)
    - [Distinguishing ChatGPT-generated and human-written papers through stylometric analysis](https://arxiv.org/abs/2304.05534)
    - [Stylometry overview](https://en.wikipedia.org/wiki/Stylometry)

## What the script scores

The script currently focuses on:

- slogan-style or binary thesis openings
- rhetorical question batteries
- sentence-length regularity
- paragraph-length regularity
- back-to-back short declarative lines
- abstraction-heavy vocabulary without enough grounding
- scarcity of concrete anchors
- repeated contrast templates
- trailing `-ing` clause overuse
- clusters of frequently flagged AI vocabulary
- manifesto-style endings
- opinion-heavy writing with little personal or operational anchoring

## What the script does not claim

- It does **not** estimate GPTZero, Turnitin, or any other detector’s actual probability.
- It does **not** prove authorship.
- It does **not** decide whether a piece was human-written.
- It will produce false positives on some terse op-eds, manifestos, landing-page copy, and intentionally minimalist prose.

## Practical use

Use the score to guide rewrites, not to optimize blindly.

Good pattern:
1. score the draft
2. fix the top 3 to 5 findings
3. score again
4. stop after 2 to 3 passes or once the gains flatten

Bad pattern:
- chasing a lower score after the writing has already become flatter or less truthful

## Known failure mode

The scorer can return a low risk score for text that still feels synthetic to a human reader.

The most common case is clean category writing: the draft avoids obvious detector tells, but it still sounds like product positioning or polished essay copy because it lacks a live operating problem, a grounded irritation, or a concrete consequence.

When that happens, do not keep sanding the prose down. Treat the score as "good enough for diagnostics" and fix the real issue in the draft itself.

Another common case is mechanical precision: the draft is clear and specific, but the sentences are too uniformly grammatical, list-like, and well-behaved to feel naturally authored.

When that happens, the fix is not more detail. The fix is more texture: one worked example, looser rhythm, less taxonomic listing, and fewer sentences that sound like guided explanation.

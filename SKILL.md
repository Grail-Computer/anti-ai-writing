---
name: anti-ai-writing
description: Rewrite drafts so they sound more natural, specific, personal, and author-driven without changing the core meaning. Use when the user asks to humanize writing, make prose sound less robotic or AI-ish, rewrite an article, essay, blog post, thread, note, memo, or landing-page copy in their own voice, reduce generic or templated phrasing, run an anti-slop editorial pass, or adapt a draft using high-level traits of another writer without imitating that writer's exact voice.
---

# anti-ai-writing

Rewrite the user's text so it feels authored rather than templated. Preserve the thesis, facts, and genuine viewpoint. Increase specificity, texture, rhythm, and ownership.

When available, anchor the rewrite in the user's own materials: prior posts, notes, rough bullets, transcripts, or earlier drafts. Use those as the voice source instead of inventing one.

## Workflow

### 1. Extract the voice anchors

- Identify the thesis, the key facts, the user's real angle, and the intended audience.
- Identify what must not change: claims, chronology, examples, names, numbers, and level of confidence.
- If the user supplied past writing or notes, infer voice from that material first.
- If no voice reference exists, stay close to the source draft rather than forcing personality onto it.

### 2. Lock the non-negotiables

- Preserve the core argument, chronology, and factual claims.
- Preserve the user's actual level of confidence. Do not make the writing sound more certain than the source.
- Preserve first-person details only when the user actually supplied them.
- If the draft depends on missing facts or examples, ask for them only when necessary. Otherwise rewrite with the available material.

### 3. Check for grounding before rewriting

- If the piece is a thesis, opinion, or category argument, check whether it contains at least one grounded element:
  - a real observation
  - a concrete workflow
  - an operational detail
  - a failure case
  - a named artifact, product, or decision
- If none exist, do not invent one.
- Either ask the user for one concrete anchor or preserve the abstraction and note that pure concept writing often reads synthetic even when every sentence is individually good.

### 4. Run the local scorer when the repo is available

If the local repository includes `scripts/score_text.py`, run it before rewriting and after each significant pass.

Recommended commands:

```bash
uv run ./scripts/score_text.py --input draft.txt --format summary
uv run ./scripts/score_text.py --input draft.txt --format json --pretty
```

When the user pasted text directly into the prompt, write it to a temporary file first or pipe it over stdin:

```bash
cat <<'EOF' >/tmp/anti-ai-draft.txt
...text...
EOF
uv run ./scripts/score_text.py --input /tmp/anti-ai-draft.txt --format json --pretty
```

Use the output as a rewrite planner:
- focus on the top 3 to 5 findings
- rewrite against those findings
- re-score
- stop after 2 to 3 passes or when the score barely improves

Do not optimize the score blindly. If lowering the score makes the prose flatter or less truthful, keep the better prose.
If the score is already low but the draft still sounds like category copy, stop iterating on the scorer and fix the actual prose problem: missing stake, missing operating detail, missing tension, or overly clean pacing.

For rationale and caveats, load [scoring-model.md](./references/scoring-model.md).

### 5. Rewrite in focused passes

Run these passes in order. Multiple focused passes beat one unfocused rewrite.

#### Pass A: Lead and structure

- Start from the user's real observation, memory, objection, or tension when one exists.
- Do not bury the lead.
- Prefer a specific opening over a universal opener.
- If the draft sounds like positioning copy, start closer to the irritation, recurring failure, or operating problem that produced the opinion.
- Remove paragraphs that only summarize what the next paragraph will say.

#### Pass B: Mechanism and specificity

- Replace abstract setup with mechanism, objects, actions, and stakes.
- Replace category labels with concrete nouns.
- Replace vague claims with examples, timeframes, numbers, or clearer qualifiers when available.
- Delete filler that cannot be made more specific.

#### Pass C: Voice and stake

- Let the writer sound like someone who cares about the argument.
- Preserve opinions, uncertainty, and mixed feelings when they are present.
- Vary sentence length and paragraph length.
- Keep some asymmetry and roughness instead of polishing every sentence to the same cadence.
- Break up ladders of short, emphatic sentences if too many appear in a row.
- Convert some rhetorical questions, binaries, or parallel constructions into ordinary prose when they start sounding slogan-like.
- If the draft is still reading as "mechanically precise," loosen the texture before you add more precision:
  - combine one literal sentence with one looser or more colloquial one
  - replace some itemized category lists with a worked example
  - allow an occasional fragment, aside, or informal turn of phrase if it fits the user's tone
  - prefer a thought unfolding over a sequence of perfectly shaped claims

#### Pass D: Concision and cleanup

- Cut restatements, throat-clearing, and transition filler.
- Prefer active verbs and plain words.
- Omit needless words.
- Merge repetitive sentences instead of synonym-cycling them.

#### Pass E: Final synthetic-tell pass

- Ask: "What still sounds generic, inflated, symmetrical, or pre-packaged?"
- Revise the remaining tells without changing the meaning.
- Ask a second question for thesis pieces: "What feels too clean, too evenly paced, or too abstract to have been written from lived experience?"

For a detailed checklist, load [anti-patterns.md](./references/anti-patterns.md).

### 6. Remove generic AI texture

- Cut broad thesis openers unless they are unusually sharp.
- Cut balanced contrast lines that sound pre-packaged.
- Remove vague filler such as "in today's world," "this shows that," or "what's interesting is."
- Replace abstract summary nouns with mechanisms, objects, actions, or stakes.
- Prefer one strong sentence over two sentences that restate each other.
- Do not let every paragraph resolve into a neat takeaway.

### 7. Add authorial texture

- Start from the user's real angle, memory, objection, or observation when one exists.
- Prefer concrete nouns over category labels.
- Keep some asymmetry and roughness. Do not smooth every sentence into the same cadence.
- Vary paragraph length and sentence length.
- Let the writer sound like a person with a stake in the argument, not a neutral explainer.
- In thesis pieces, trade at least one polished abstraction for a concrete example or operational detail when the source supports it.
- If the argument is about how companies buy or use software, include the actual operational test whenever the source supports it: the queue, the review path, the escalation point, the cleanup burden, or the failure mode.

### 8. Keep the writing honest

- Do not imitate a specific living writer's exact voice.
- If the user references a writer, extract only high-level traits such as simplicity, first-principles reasoning, directness, or use of examples.
- Do not invent personal anecdotes, uncertainty, research, or lived experience.
- Do not add unsupported facts to make the text seem more "human."
- If the user mentions AI detectors, treat that as a cue to improve specificity and authenticity, not to game a detector.

## Editing heuristics

- Replace abstract setup with concrete setup.
- Replace general commentary with actual mechanism.
- Replace polished summary lines with direct claims.
- Replace repetitive transitions with paragraph breaks.
- Replace vague praise or skepticism with the reason behind it.
- Keep length roughly similar unless the user asks to compress or expand.
- Lead with the "why" before the "what" when the draft is explanatory.
- Prefer one paragraph per idea.
- Put the most emphatic or surprising words near the end of the sentence when it helps clarity.
- Avoid turning the whole piece into a sequence of quotable lines.
- In category writing, keep one or two lines sharp and let the rest do real explanatory work.
- If the writing is technically correct but still feels synthetic, the problem may be over-control rather than lack of clarity.
- In that case, trade some neat precision for conversational movement, uneven emphasis, and one or two sentences that feel spoken rather than assembled.

## Voice sourcing

- If the user gives 1 to 3 samples of their prior writing, read them before rewriting.
- Infer only high-level tendencies: sentence length, directness, level of formality, use of first person, tolerance for rough edges, favorite transitions, and how strongly they state opinions.
- Do not parrot distinctive phrases unless they already appear in the draft.
- If the draft is for a new channel, adapt format but keep the author's center of gravity.

## Modes

Choose the lightest mode that solves the request.

- Light pass: Keep structure, tighten wording, remove obvious AI texture.
- Standard pass: Rewrite paragraph by paragraph with clearer lead, more specificity, and stronger voice.
- Deep pass: Rebuild structure, opening, and ending while preserving the same argument and facts.
- Diagnostic pass: Explain why a draft still reads synthetic and point to the exact high-level patterns causing it.

## Output shape

- Return the clean rewrite first.
- Do not preface it with meta commentary.
- If the changes are substantial or the user asks, add a short note after the rewrite explaining what changed.
- For articles and essays, preserve the argument while tightening the opening and ending.
- For X posts and threads, shorten paragraphs, front-load the point, and keep the cadence punchier.
- If a piece stays too abstract because the source material is abstract, say so plainly after the rewrite instead of pretending the problem is solved.
- If you used the scorer, include the before and after scores briefly after the rewrite.
- If you used the local scorer, include the before and after scores briefly after the rewrite.
- Do not present a low score as proof that the piece now sounds good. The score is only a rewrite aid.

## Reference prompts

- "Use $anti-ai-writing to rewrite this article so it sounds more like something I would actually say. Keep the argument, but make it less polished and more concrete."
- "Use $anti-ai-writing on this thread draft. Cut generic framing, sharpen the viewpoint, and keep the tone direct."
- "Use $anti-ai-writing to rewrite this essay using the same ideas but with simpler language, more specific nouns, and fewer AI-sounding transitions."

## Core stance

The goal is not to make text "look human" through tricks. The goal is to make it more truthful to the writer: more specific, more situated, less generic, and less dependent on stock essay phrasing.

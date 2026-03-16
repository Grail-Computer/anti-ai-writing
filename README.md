# Anti-AI Writing

`anti-ai-writing` is a single installable agent skill for rewriting drafts so they sound more specific, grounded, and author-driven.

The skill is designed for the open agent skills ecosystem and is installable with [`npx skills`](https://skills.sh/). The repo is intentionally structured as a single-skill repository with a root `SKILL.md`, which the `skills` CLI discovers directly.

## What It Does

- removes generic, templated, "AI-ish" phrasing
- preserves the actual thesis, facts, and confidence level
- uses the author's own writing samples as voice reference when available
- rewrites in focused editorial sweeps instead of one vague "humanize this" pass
- runs a final anti-slop pass against a concrete synthetic-tell checklist

This is an editorial skill, not a detector-gaming trick. It is meant to produce writing that is more truthful to the writer, not to invent fake personality or fake experience.

## Repository Layout

This repository follows the simple root-level layout used by single-skill repositories in the `skills` ecosystem:

```text
.
├── SKILL.md
├── README.md
├── LICENSE
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── score_text.py
│   ├── compare_variants.py
│   └── hypothesis_panel.py
└── references/
    ├── research-notes.md
    ├── anti-patterns.md
    └── scoring-model.md
```

## Install with npx skills

List the skill:

```bash
npx skills add Grail-Computer/anti-ai-writing --list
```

Install it for the current project:

```bash
npx skills add Grail-Computer/anti-ai-writing
```

Install it globally for Codex without prompts:

```bash
npx skills add Grail-Computer/anti-ai-writing -g -a codex -y
```

Install it for Claude Code globally:

```bash
npx skills add Grail-Computer/anti-ai-writing -g -a claude-code -y
```

## Usage

Ask your agent to use the skill explicitly:

```text
Use $anti-ai-writing to rewrite this draft so it sounds more like me.
Keep the facts and argument intact.
Use these 2 old posts as voice reference.
Do a standard pass and then a final anti-slop pass.
```

You can also use shorter prompts:

```text
Use $anti-ai-writing on this essay draft.
```

```text
Use $anti-ai-writing on this X thread. Keep it punchy and direct.
```

## Local scoring loop

The repo includes a local `uv` scorer that surfaces explainable synthetic-writing risk signals:

```bash
uv run ./scripts/score_text.py --input draft.txt --format summary
uv run ./scripts/score_text.py --input draft.txt --format json --pretty
cat draft.txt | uv run ./scripts/score_text.py --stdin --format summary
```

The score is a local heuristic, not a claim that the text is AI-generated. It is designed to surface rewrite targets such as:

- slogan thesis openings
- rhetorical question batteries
- over-regular sentence cadence
- abstraction-heavy paragraphs with too few concrete anchors
- manifesto-style endings

Use it as a revision loop:

1. score the draft
2. rewrite against the top findings
3. score again
4. stop after 2 to 3 passes or once the gains flatten

## Variant panel

When one rewrite loop is not enough, compare multiple drafts across higher-level hypotheses:

```bash
uv run ./scripts/hypothesis_panel.py draft-a.txt draft-b.txt draft-c.txt
```

The panel reports:

- `risk`: base synthetic-risk score from `score_text.py`
- `q`: question / interview-checklist pressure
- `list`: checklist-like sentence and paragraph pressure
- `slop`: repeated-frame, low-variety, and scaffolding pressure
- `texture`: conversational texture score
- `ground`: grounding and worked-example score

Use it when you want to explore several writing shapes in parallel instead of polishing one draft blindly.

## Writing Model

The skill works in focused passes:

1. Extract voice anchors and non-negotiables.
2. Check grounding and run the local scorer when available.
3. Fix the lead and structure.
4. Replace abstract phrasing with mechanisms, objects, and stakes.
5. Restore voice, rhythm, and authorial stake.
6. Re-score and run a final synthetic-tell pass using the anti-pattern checklist.

The detailed checklist lives in [references/anti-patterns.md](references/anti-patterns.md), the scoring model lives in [references/scoring-model.md](references/scoring-model.md), and the paper-backed notes live in [references/research-notes.md](references/research-notes.md).

## References

- [skills.sh](https://skills.sh/)
- [vercel-labs/skills](https://github.com/vercel-labs/skills)

## License

MIT

## Attribution

This skill is fully developed by **FastClaw** and the **Grail.Computer** team.

- FastClaw repo: https://github.com/Grail-Computer/FastClaw
- Grail: https://grail.computer

## Hire Grail as an AI Employee

You can hire Grail as an AI Employee by:
- Emailing us at **yash@grail.computer**
- Visiting **https://grail.computer**

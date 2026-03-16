# Research notes

These notes summarize the public guidance and research that informed the local scoring script.

The script is **not** an authorship detector. It uses explainable editorial heuristics that approximate recurring patterns discussed in detector documentation, stylometry research, and public cleanup guides.

## Sources used

- [GPTZero: AI Vocabulary FAQ](https://gptzero.me/ai-vocabulary)
- [Turnitin: AI writing detection model](https://guides.turnitin.com/hc/en-us/articles/28294949544717-AI-writing-detection-model)
- [Stylometry](https://en.wikipedia.org/wiki/Stylometry)
- [A Lightweight Approach to Detection of AI-Generated Texts Using Stylometric Features](https://arxiv.org/abs/2511.21744)
- [Distinguishing AI-Generated and Human-Written Text Through Psycholinguistic Analysis](https://arxiv.org/abs/2505.01800)
- [Distinguishing ChatGPT-generated and human-written papers through stylometric analysis](https://arxiv.org/abs/2304.05534)
- [Can AI-generated text be reliably detected?](https://arxiv.org/abs/2303.11156)

## Signals worth approximating

### 1. Predictability and burstiness

GPTZero describes detector signals in terms of predictability and burstiness rather than any single banned word list. Human writing tends to vary more in sentence shape and pressure; generated writing often settles into cleaner regularity.

Local proxy:
- sentence-length coefficient of variation
- paragraph-length coefficient of variation
- short declarative ladders

### 2. Generic, repetitive style

GPTZero also notes that even when certain words are common in AI-generated text, vocabulary alone does not prove anything. Style matters more when it becomes generic or repetitive.

Local proxy:
- repeated structural openings
- repeated contrast templates
- stock rhetorical frames
- clusters of frequently flagged prestige words

### 3. Stylometric and readability features

Stylometry research has long used measurable signals such as word frequencies, sentence structure, punctuation patterns, and function words. Recent AI-text work extends that approach with lightweight stylometric and readability features.

Local proxy:
- sentence and paragraph variance
- lexical density and abstract-word density
- simple readability metrics
- first-person and function-word ratios as metrics, not verdicts

### 4. Generic intros and endings create false positives

Turnitin notes that false positives appeared more often in generic opening and closing sentences. This is important because polished op-eds and essays often use exactly those shapes.

Local proxy:
- slogan or binary thesis openings
- polished manifesto endings
- broad future or category-closing claims

### 5. Abstract language without grounding

Public cleanup guides and editorial practice repeatedly flag inflated significance, broad market claims, and abstract nouns doing the work of real examples.

Local proxy:
- abstract-noun density
- scarcity of concrete anchors such as numbers, quoted phrases, named artifacts, product names, or operational details

### 6. Neat rhetorical symmetry

Generated prose often arrives in suspiciously balanced groups: binary contrasts, question batteries, definition ladders, and clean three-part lists.

Local proxy:
- question batteries
- repeated “the real question is” / “that is why” / “what happens when” frames
- short parallel sentence ladders

### 7. Thin personal stake

A detector cannot reliably measure “voice,” but readers often perceive category arguments as synthetic when they contain strong opinions with little personal, operational, or situational anchoring.

Local proxy:
- opinion-heavy language combined with low first-person signal and few concrete anchors

## Important caveat

Detection papers repeatedly show that detector-style systems make mistakes. They can overflag polished prose, formulaic student writing, translated text, and some non-native writing.

That is why this repo treats the score as a **revision aid**:
- use it to identify what feels too clean, too abstract, or too symmetrical
- do not treat it as a truth machine
- stop optimizing if the prose becomes flatter or less honest

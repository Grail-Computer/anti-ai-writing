#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


VERSION = "0.2.0"

MAX_DIMENSION_WEIGHTS = {
    "abstraction": 1.35,
    "grounding_gap": 1.95,
    "cadence_regularness": 2.9,
    "structural_symmetry": 3.05,
    "lexical_genericness": 1.15,
    "ending_genericness": 0.95,
}

MONTHS = {
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}

FIRST_PERSON = {
    "i",
    "i'm",
    "i've",
    "i'd",
    "i'll",
    "me",
    "my",
    "mine",
    "myself",
    "we",
    "we're",
    "we've",
    "we'd",
    "we'll",
    "us",
    "our",
    "ours",
}

FUNCTION_WORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "now",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "would",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}

ABSTRACT_WORDS = {
    "abstraction",
    "access",
    "accountability",
    "adoption",
    "advancement",
    "alignment",
    "authority",
    "autonomy",
    "boundary",
    "capability",
    "category",
    "clarity",
    "coherence",
    "complexity",
    "confidence",
    "consequence",
    "constraint",
    "context",
    "credibility",
    "decision",
    "dependability",
    "difference",
    "direction",
    "discovery",
    "efficiency",
    "evolution",
    "execution",
    "expectation",
    "framework",
    "future",
    "governance",
    "improvement",
    "importance",
    "incentive",
    "innovation",
    "insight",
    "integrity",
    "judgment",
    "landscape",
    "layer",
    "maturity",
    "mechanism",
    "momentum",
    "narrative",
    "operation",
    "optimization",
    "outcome",
    "ownership",
    "paradigm",
    "performance",
    "perspective",
    "positioning",
    "potential",
    "priority",
    "process",
    "reality",
    "relationship",
    "reliability",
    "representation",
    "risk",
    "scope",
    "significance",
    "simplicity",
    "solution",
    "strategy",
    "structure",
    "system",
    "terminology",
    "thesis",
    "transformation",
    "transition",
    "trust",
    "value",
    "variability",
    "workflow",
}

AI_VOCAB = {
    "additionally",
    "align",
    "aligned",
    "crucial",
    "delve",
    "emphasize",
    "emphasizing",
    "enduring",
    "enhance",
    "enhancing",
    "foster",
    "fostering",
    "garner",
    "highlight",
    "highlighting",
    "interplay",
    "intricate",
    "intricacies",
    "landscape",
    "pivotal",
    "robust",
    "seamless",
    "showcase",
    "showcasing",
    "tapestry",
    "testament",
    "underscore",
    "underscoring",
    "valuable",
    "vibrant",
}

NOMINALIZATION_SUFFIXES = (
    "tion",
    "sion",
    "ment",
    "ness",
    "ity",
    "ism",
    "ance",
    "ence",
    "ship",
)

PARALLELISM_PATTERNS = [
    r"\bnot just\b",
    r"\bnot only\b",
    r"\bit's not\b",
    r"\bit is not\b",
    r"\bnot because\b",
    r"\bthe problem is not\b",
    r"\bthe real question is\b",
    r"\bthat is why\b",
    r"\bthis is where\b",
    r"\bthat is the part\b",
    r"\bfor me the\b",
    r"\bthis matters because\b",
    r"\bonce you ask\b",
    r"\bwhat happens when\b",
]


@dataclass
class Finding:
    code: str
    label: str
    dimension: str
    severity: float
    weight: float
    count: int
    examples: list[str]
    suggestion: str

    @property
    def contribution(self) -> float:
        return self.severity * self.weight


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def truncate(text: str, limit: int = 150) -> str:
    compact = re.sub(r"\s+", " ", text.strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.strip())
    if not normalized:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[\"'A-Z0-9])", normalized)
    return [part.strip() for part in parts if part.strip()]


def tokenize_words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*|\d+(?:\.\d+)?", text)


def sentence_word_counts(sentences: list[str]) -> list[int]:
    return [len(tokenize_words(sentence)) for sentence in sentences if tokenize_words(sentence)]


def count_syllables(word: str) -> int:
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    syllables = max(1, len(groups))
    if word.endswith("e") and syllables > 1:
        syllables -= 1
    return max(1, syllables)


def flesch_reading_ease(words: list[str], sentences: list[str]) -> float:
    word_count = len(words)
    sentence_count = max(1, len(sentences))
    syllable_count = sum(count_syllables(word) for word in words)
    if not word_count:
        return 0.0
    return 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)


def count_nominalizations(words: list[str]) -> int:
    return sum(1 for word in words if len(word) > 5 and word.endswith(NOMINALIZATION_SUFFIXES))


def concrete_anchors(text: str, sentences: list[str]) -> list[str]:
    anchors: set[str] = set()
    for match in re.findall(r"https?://\S+|@\w+|\b\d+(?:\.\d+)?%?\b", text):
        anchors.add(match)
    for match in re.findall(r'"[^"]{2,50}"|“[^”]{2,50}”', text):
        anchors.add(match)
    for match in re.findall(r"\([^)]{2,40}\)", text):
        anchors.add(match)
    for sentence in sentences:
        tokens = re.findall(r"\b[A-Z][A-Za-z0-9-]+\b", sentence)
        for token in tokens[1:]:
            lowered = token.lower()
            if lowered not in MONTHS and lowered not in {"i"}:
                anchors.add(token)
    return sorted(anchors)


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def coeff_var(values: list[int]) -> float:
    if len(values) < 2:
        return 0.0
    mean = statistics.mean(values)
    if mean == 0:
        return 0.0
    return statistics.pstdev(values) / mean


def collect_metrics(text: str) -> dict[str, float]:
    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)
    words = tokenize_words(text)
    lower_words = [word.lower() for word in words]
    sentence_lengths = sentence_word_counts(sentences)
    paragraph_lengths = [len(tokenize_words(paragraph)) for paragraph in paragraphs]
    abstract_count = sum(1 for word in lower_words if word in ABSTRACT_WORDS) + count_nominalizations(lower_words)
    ai_vocab_hits = sum(1 for word in lower_words if word in AI_VOCAB)
    question_count = sum(sentence.count("?") for sentence in sentences)
    first_person_count = sum(1 for word in lower_words if word in FIRST_PERSON)
    function_word_count = sum(1 for word in lower_words if word in FUNCTION_WORDS)
    anchor_list = concrete_anchors(text, sentences)
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "question_count": question_count,
        "mean_sentence_length": round(average(sentence_lengths), 2),
        "sentence_length_stddev": round(statistics.pstdev(sentence_lengths), 2) if len(sentence_lengths) > 1 else 0.0,
        "sentence_length_cv": round(coeff_var(sentence_lengths), 3),
        "mean_paragraph_length": round(average(paragraph_lengths), 2),
        "paragraph_length_cv": round(coeff_var(paragraph_lengths), 3),
        "type_token_ratio": round(safe_div(len(set(lower_words)), len(lower_words)), 3),
        "first_person_rate": round(safe_div(first_person_count, max(1, len(lower_words))), 3),
        "function_word_ratio": round(safe_div(function_word_count, max(1, len(lower_words))), 3),
        "abstract_word_count": abstract_count,
        "abstract_word_density": round(safe_div(abstract_count, max(1, len(lower_words))), 3),
        "ai_vocab_hits": ai_vocab_hits,
        "ai_vocab_density": round(safe_div(ai_vocab_hits, max(1, len(lower_words))), 3),
        "concrete_anchor_count": len(anchor_list),
        "flesch_reading_ease": round(flesch_reading_ease(words, sentences), 2),
    }


def detect_slogan_thesis(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    if len(sentences) < 2:
        return None
    opening = " ".join(sentences[:2])
    patterns = [
        r"\bmost [^.?!]{0,80}\b(do not|don't|does not|doesn't|are not|aren't)\b",
        r"\bthe problem is not\b",
        r"\bthe real question is not\b",
    ]
    second_short = len(tokenize_words(sentences[1])) <= 10
    if any(re.search(pattern, opening, flags=re.IGNORECASE) for pattern in patterns) and second_short:
        return Finding(
            code="slogan-thesis",
            label="Slogan thesis in the opening",
            dimension="structural_symmetry",
            severity=0.92,
            weight=1.2,
            count=1,
            examples=[truncate(opening)],
            suggestion="Keep the thesis if it is strong, but ground it immediately with a concrete reason or operational example.",
        )
    return None


def detect_question_battery(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    question_sentences = [sentence for sentence in sentences if sentence.endswith("?")]
    if not question_sentences:
        return None
    streak = 0
    max_streak = 0
    streak_examples: list[str] = []
    current_examples: list[str] = []
    for sentence in sentences:
        if sentence.endswith("?"):
            streak += 1
            current_examples.append(sentence)
        else:
            if streak > max_streak:
                max_streak = streak
                streak_examples = current_examples[:]
            streak = 0
            current_examples = []
    if streak > max_streak:
        max_streak = streak
        streak_examples = current_examples[:]
    if max_streak >= 3 or len(question_sentences) >= 4:
        severity = clamp(max(max_streak / 5, len(question_sentences) / 6))
        return Finding(
            code="question-battery",
            label="Checklist-like question battery",
            dimension="structural_symmetry",
            severity=severity,
            weight=1.0,
            count=len(question_sentences),
            examples=[truncate(example) for example in streak_examples[:3] or question_sentences[:3]],
            suggestion="Keep only the strongest question. Turn the rest into prose, a worked example, or explicit criteria.",
        )
    return None


def detect_sentence_uniformity(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    sentence_lengths = sentence_word_counts(sentences)
    if len(sentence_lengths) < 6:
        return None
    cv = coeff_var(sentence_lengths)
    severity = clamp((0.38 - cv) / 0.22)
    if severity <= 0:
        return None
    return Finding(
        code="sentence-uniformity",
        label="Sentence lengths are too uniform",
        dimension="cadence_regularness",
        severity=severity,
        weight=1.1,
        count=len(sentence_lengths),
        examples=[f"sentence length CV={cv:.3f}, mean={statistics.mean(sentence_lengths):.1f} words"],
        suggestion="Mix sentence lengths more aggressively. Let some ideas unfold instead of landing every line with the same pressure.",
    )


def detect_paragraph_uniformity(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    paragraphs = split_paragraphs(text)
    paragraph_lengths = [len(tokenize_words(paragraph)) for paragraph in paragraphs]
    if len(paragraph_lengths) < 3:
        return None
    cv = coeff_var(paragraph_lengths)
    severity = clamp((0.55 - cv) / 0.30)
    if severity <= 0.05:
        return None
    return Finding(
        code="paragraph-uniformity",
        label="Paragraph lengths are too even",
        dimension="cadence_regularness",
        severity=severity,
        weight=0.8,
        count=len(paragraph_lengths),
        examples=[f"paragraph length CV={cv:.3f}, mean={statistics.mean(paragraph_lengths):.1f} words"],
        suggestion="Vary paragraph size. Let some paragraphs do setup and others carry the argument.",
    )


def detect_short_ladder(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    streak = 0
    max_streak = 0
    examples: list[str] = []
    current_examples: list[str] = []
    for sentence in sentences:
        tokens = tokenize_words(sentence)
        short = len(tokens) <= 9 and "," not in sentence and "—" not in sentence and ";" not in sentence
        if short and not sentence.endswith("?"):
            streak += 1
            current_examples.append(sentence)
        else:
            if streak > max_streak:
                max_streak = streak
                examples = current_examples[:]
            streak = 0
            current_examples = []
    if streak > max_streak:
        max_streak = streak
        examples = current_examples[:]
    if max_streak >= 3:
        severity = clamp(max_streak / 5)
        return Finding(
            code="short-declarative-ladder",
            label="Checklist-like sentence ladder",
            dimension="cadence_regularness",
            severity=severity,
            weight=1.0,
            count=max_streak,
            examples=[truncate(example) for example in examples[:3]],
            suggestion="Replace serial mini-sentences with one fuller sentence or a worked example. Avoid prose that reads like a checklist.",
        )
    return None


def detect_micro_paragraphs(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    paragraphs = split_paragraphs(text)
    if len(paragraphs) < 5:
        return None

    short_paragraphs = [paragraph for paragraph in paragraphs if len(tokenize_words(paragraph)) <= 10]
    ratio = safe_div(len(short_paragraphs), len(paragraphs))
    severity = clamp((ratio - 0.22) / 0.33)
    if len(short_paragraphs) < 3 or severity <= 0:
        return None

    return Finding(
        code="micro-paragraphs",
        label="Too many micro-paragraph emphasis beats",
        dimension="cadence_regularness",
        severity=severity,
        weight=0.7,
        count=len(short_paragraphs),
        examples=[truncate(paragraph) for paragraph in short_paragraphs[:3]],
        suggestion="Merge some one-line paragraphs back into fuller prose. Too many emphasis beats can feel staged.",
    )


def detect_repeated_openings(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    openings: list[tuple[str, str]] = []
    for sentence in sentences:
        words = [word.lower() for word in tokenize_words(sentence)]
        if len(words) < 2:
            continue
        opening = " ".join(words[:2])
        openings.append((opening, sentence))

    if len(openings) < 5:
        return None

    counts = Counter(opening for opening, _ in openings)
    repeated = [(opening, count) for opening, count in counts.items() if count >= 3]
    if not repeated:
        return None

    repeated.sort(key=lambda item: (-item[1], item[0]))
    examples: list[str] = []
    for opening, _count in repeated[:3]:
        matching = [truncate(sentence) for seen_opening, sentence in openings if seen_opening == opening][:2]
        examples.extend(matching)

    severity = clamp((repeated[0][1] - 2) / 3)
    return Finding(
        code="repeated-openings",
        label="Repeated sentence openings",
        dimension="structural_symmetry",
        severity=severity,
        weight=0.8,
        count=sum(count for _, count in repeated),
        examples=examples[:4],
        suggestion="Collapse repeated sentence stems unless the repetition carries real force. One fuller sentence is often stronger.",
    )


def detect_abstraction_stack(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    density = metrics["abstract_word_density"]
    anchor_count = int(metrics["concrete_anchor_count"])
    word_count = int(metrics["word_count"])
    anchor_rate = safe_div(anchor_count, max(1, word_count)) * 100
    severity = clamp(((density - 0.05) / 0.04) + ((0.7 - anchor_rate) / 0.8))
    if severity <= 0:
        return None
    paragraphs = split_paragraphs(text)
    abstract_paragraphs = [
        paragraph
        for paragraph in paragraphs
        if safe_div(
            sum(
                1
                for word in tokenize_words(paragraph)
                if word.lower() in ABSTRACT_WORDS or word.lower().endswith(NOMINALIZATION_SUFFIXES)
            ),
            max(1, len(tokenize_words(paragraph))),
        )
        >= 0.07
    ]
    return Finding(
        code="abstraction-stack",
        label="Abstraction-heavy prose without enough grounding",
        dimension="abstraction",
        severity=severity,
        weight=1.35,
        count=len(abstract_paragraphs) or 1,
        examples=[truncate(paragraph) for paragraph in abstract_paragraphs[:2] or paragraphs[:1]],
        suggestion="Trade at least one polished abstraction for a workflow, failure case, named artifact, or operational detail.",
    )
    return None


def detect_low_lexical_diversity(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    word_count = int(metrics["word_count"])
    if word_count < 180:
        return None
    ttr = metrics["type_token_ratio"]
    severity = clamp((0.47 - ttr) / 0.10)
    if severity <= 0:
        return None
    return Finding(
        code="low-lexical-diversity",
        label="Lexical variety is too low for the length",
        dimension="lexical_genericness",
        severity=severity,
        weight=0.75,
        count=word_count,
        examples=[f"type-token ratio={ttr:.3f} over {word_count} words"],
        suggestion="Reduce safe repetition. Swap one abstract restatement for fresher concrete nouns, verbs, or a worked example.",
    )


def detect_function_word_load(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    word_count = int(metrics["word_count"])
    if word_count < 180:
        return None
    ratio = metrics["function_word_ratio"]
    severity = clamp((ratio - 0.60) / 0.08)
    if severity <= 0:
        return None
    return Finding(
        code="function-word-load",
        label="Too much connective or scaffolding language",
        dimension="lexical_genericness",
        severity=severity,
        weight=0.6,
        count=word_count,
        examples=[f"function-word ratio={ratio:.3f}"],
        suggestion="Trim connective scaffolding and let more of the prose ride on concrete nouns, verbs, and examples.",
    )


def detect_anchor_scarcity(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    word_count = int(metrics["word_count"])
    if word_count < 180:
        return None
    anchor_count = int(metrics["concrete_anchor_count"])
    expected = max(2.0, word_count / 160.0)
    severity = clamp((expected - anchor_count) / expected)
    if severity <= 0:
        return None
    examples = concrete_anchors(text, sentences)[:5]
    return Finding(
        code="grounding-gap",
        label="Too few concrete anchors for the length",
        dimension="grounding_gap",
        severity=severity,
        weight=1.25,
        count=anchor_count,
        examples=examples or ["No strong concrete anchors found."],
        suggestion="Add a real observation, workflow step, product behavior, bug, metric, or named decision if the source supports it.",
    )


def detect_parallelism(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    matches: list[str] = []
    count = 0
    for pattern in PARALLELISM_PATTERNS:
        found = re.findall(pattern, text, flags=re.IGNORECASE)
        if found:
            count += len(found)
            matches.extend(found)
    if count < 3:
        return None
    severity = clamp((count - 2) / 4)
    return Finding(
        code="parallelism-overuse",
        label="Repeated contrast or rhetorical frame",
        dimension="structural_symmetry",
        severity=severity,
        weight=0.85,
        count=count,
        examples=matches[:5],
        suggestion="Keep the strongest frame and turn the rest into ordinary prose.",
    )


def detect_participial_tails(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    matches = re.findall(r",\s+[A-Za-z-]+ing\b[^,.!?;:]{0,80}", text)
    if not matches:
        return None
    severity = clamp(len(matches) / max(3, len(sentences) / 4))
    if severity <= 0.15:
        return None
    return Finding(
        code="participial-tails",
        label="Too many trailing -ing clauses",
        dimension="lexical_genericness",
        severity=severity,
        weight=0.6,
        count=len(matches),
        examples=[truncate(match) for match in matches[:3]],
        suggestion="Cut or rewrite trailing -ing clauses unless they add a concrete fact.",
    )


def detect_ai_vocab(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    hits = [word for word in tokenize_words(text) if word.lower() in AI_VOCAB]
    if len(hits) < 3:
        return None
    severity = clamp(len(hits) / max(6, len(tokenize_words(text)) / 70))
    return Finding(
        code="ai-vocabulary",
        label="Cluster of frequently flagged AI vocabulary",
        dimension="lexical_genericness",
        severity=severity,
        weight=0.55,
        count=len(hits),
        examples=sorted(set(hit.lower() for hit in hits))[:8],
        suggestion="Replace generic prestige words with plainer language or a more precise noun.",
    )


def detect_manifesto_ending(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    if len(sentences) < 2:
        return None
    ending = " ".join(sentences[-3:])
    patterns = [
        r"\bthe teams that\b",
        r"\beveryone else\b",
        r"\bwill build the category\b",
        r"\bthe future\b",
        r"\bone day\b",
        r"\bthe winners\b",
        r"\bthey will\b",
    ]
    if not any(re.search(pattern, ending, flags=re.IGNORECASE) for pattern in patterns):
        return None
    return Finding(
        code="manifesto-ending",
        label="Ending reads like a polished manifesto",
        dimension="ending_genericness",
        severity=0.78,
        weight=0.95,
        count=1,
        examples=[truncate(ending)],
        suggestion="End closer to the operational bet, unresolved risk, or concrete consequence.",
    )


def detect_opinion_without_self(text: str, sentences: list[str], metrics: dict[str, float]) -> Finding | None:
    opinion_signals = len(
        re.findall(r"\b(should|need|matters?|prefer|trust|important|winners?|losers?|real question)\b", text, flags=re.IGNORECASE)
    )
    if opinion_signals < 5:
        return None
    first_person_rate = metrics["first_person_rate"]
    anchor_count = metrics["concrete_anchor_count"]
    if first_person_rate >= 0.01 or anchor_count >= 3:
        return None
    severity = clamp((0.01 - first_person_rate) * 30 + (3 - anchor_count) * 0.12)
    return Finding(
        code="opinion-without-anchor",
        label="Opinion-heavy draft with little personal or concrete anchoring",
        dimension="grounding_gap",
        severity=severity,
        weight=0.7,
        count=opinion_signals,
        examples=[truncate(" ".join(sentences[:2]))],
        suggestion="If the source supports it, add one real observation, preference, or operational detail instead of stacking more claims.",
    )


HEURISTICS = [
    detect_slogan_thesis,
    detect_question_battery,
    detect_sentence_uniformity,
    detect_paragraph_uniformity,
    detect_short_ladder,
    detect_micro_paragraphs,
    detect_repeated_openings,
    detect_abstraction_stack,
    detect_low_lexical_diversity,
    detect_function_word_load,
    detect_anchor_scarcity,
    detect_parallelism,
    detect_participial_tails,
    detect_ai_vocab,
    detect_manifesto_ending,
    detect_opinion_without_self,
]


def score_text(text: str) -> dict:
    sentences = split_sentences(text)
    metrics = collect_metrics(text)
    findings = [finding for heuristic in HEURISTICS if (finding := heuristic(text, sentences, metrics))]
    total_weight = sum(MAX_DIMENSION_WEIGHTS.values()) or 1.0
    weighted_score = sum(finding.contribution for finding in findings)
    overall_score = round((weighted_score / total_weight) * 100, 1)

    if overall_score < 20:
        band = "low"
    elif overall_score < 40:
        band = "guarded"
    elif overall_score < 60:
        band = "elevated"
    else:
        band = "high"

    grouped: dict[str, list[Finding]] = {}
    for finding in findings:
        grouped.setdefault(finding.dimension, []).append(finding)

    dimension_scores = {}
    for name, max_weight in MAX_DIMENSION_WEIGHTS.items():
        dimension_scores[name] = round(sum(item.contribution for item in grouped.get(name, [])) / max_weight * 100, 1)

    findings_sorted = sorted(findings, key=lambda finding: (-finding.contribution, -finding.severity, finding.code))
    rewrite_targets: list[str] = []
    seen = set()
    for finding in findings_sorted:
        if finding.suggestion not in seen:
            rewrite_targets.append(finding.suggestion)
            seen.add(finding.suggestion)
        if len(rewrite_targets) >= 5:
            break

    return {
        "version": VERSION,
        "overall_score": overall_score,
        "band": band,
        "dimensions": dimension_scores,
        "metrics": metrics,
        "findings": [
            {
                **asdict(finding),
                "severity": round(finding.severity, 3),
                "weight": round(finding.weight, 3),
                "contribution": round(finding.contribution, 3),
            }
            for finding in findings_sorted
        ],
        "rewrite_targets": rewrite_targets,
        "note": "Heuristic score only. This is an explainable editorial proxy, not a detector verdict.",
    }


def print_summary(report: dict, top: int) -> None:
    print(f"Synthetic-risk score: {report['overall_score']:.1f} ({report['band']})")
    print(report["note"])
    print()
    print("Top findings:")
    if not report["findings"]:
        print("- No strong signals fired.")
    for finding in report["findings"][:top]:
        print(f"- {finding['label']} [{finding['dimension']}] score={finding['severity']:.2f}")
        for example in finding["examples"][:2]:
            print(f"  example: {example}")
        print(f"  suggestion: {finding['suggestion']}")
    print()
    print("Key metrics:")
    metrics = report["metrics"]
    print(
        "  words={word_count} sentences={sentence_count} paragraphs={paragraph_count} questions={question_count}".format(
            **metrics
        )
    )
    print(
        "  sentence_cv={sentence_length_cv} paragraph_cv={paragraph_length_cv} anchors={concrete_anchor_count} "
        "abstract_density={abstract_word_density} first_person_rate={first_person_rate}".format(**metrics)
    )
    print()
    print("Dimension scores:")
    for name, score in report["dimensions"].items():
        print(f"  {name}: {score}")
    if report["rewrite_targets"]:
        print()
        print("Rewrite targets:")
        for target in report["rewrite_targets"][:top]:
            print(f"- {target}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score explainable synthetic-writing risk signals in a text. Higher scores mean the prose is more likely to read as templated, overly regular, or insufficiently grounded."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stdin", action="store_true", help="Read text from stdin.")
    group.add_argument("--input", help="Path to a UTF-8 text file.")
    group.add_argument("--text", help="Score a literal text argument.")
    parser.add_argument("--format", choices=("summary", "json"), default="summary", help="Output format.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--top", type=int, default=5, help="How many findings or rewrite targets to show.")
    parser.add_argument("--fail-above", type=float, help="Exit nonzero if the overall score is at or above this threshold.")
    return parser


def read_input(args: argparse.Namespace) -> str:
    if args.stdin:
        return sys.stdin.read()
    if args.input:
        return Path(args.input).read_text(encoding="utf-8")
    if args.text is not None:
        return args.text
    raise SystemExit("Provide one of --stdin, --input, or --text.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    text = read_input(args)
    report = score_text(text)

    if args.format == "json":
        if args.pretty:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(report, ensure_ascii=False))
    else:
        print_summary(report, top=max(1, args.top))

    if args.fail_above is not None and report["overall_score"] >= args.fail_above:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

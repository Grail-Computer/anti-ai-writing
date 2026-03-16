#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path


def load_score_module(script_path: Path):
    spec = importlib.util.spec_from_file_location("score_text_module", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load scorer from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def count_contractions(text: str) -> int:
    return len(re.findall(r"\b[A-Za-z]+['’][A-Za-z]+\b", text))


def count_example_markers(text: str) -> int:
    patterns = [
        r"\bfor example\b",
        r"\btake\b",
        r"\bimagine\b",
        r"\bif you\b",
        r"\bsupport triage\b",
        r"\bqueue\b",
        r"\bticket",
    ]
    return sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in patterns)


def find_finding(report: dict, code: str) -> dict | None:
    for finding in report.get("findings", []):
        if finding.get("code") == code:
            return finding
    return None


def score_variant(text: str, score_module) -> dict:
    report = score_module.score_text(text)
    metrics = report["metrics"]
    words = max(1, int(metrics["word_count"]))
    contractions = count_contractions(text)
    contractions_per_100 = contractions / words * 100
    example_markers = count_example_markers(text)

    question_finding = find_finding(report, "question-battery")
    ladder_finding = find_finding(report, "short-declarative-ladder")
    opening_finding = find_finding(report, "repeated-openings")

    question_risk = clamp((question_finding["severity"] * 100) if question_finding else metrics["question_count"] * 8)
    checklist_risk = clamp(
        (ladder_finding["severity"] * 55 if ladder_finding else 0)
        + (opening_finding["severity"] * 45 if opening_finding else 0)
    )

    conversational_texture = clamp(
        contractions_per_100 * 10
        + metrics["sentence_length_cv"] * 35
        + metrics["paragraph_length_cv"] * 25
        + metrics["first_person_rate"] * 500
    )
    grounding_score = clamp(
        min(30, metrics["concrete_anchor_count"] * 6)
        + example_markers * 8
        + max(0, 20 - metrics["abstract_word_density"] * 200)
    )

    candidate_score = clamp(
        (100 - report["overall_score"]) * 0.35
        + (100 - question_risk) * 0.2
        + (100 - checklist_risk) * 0.2
        + conversational_texture * 0.15
        + grounding_score * 0.10
    )

    return {
        "synthetic_risk": report["overall_score"],
        "question_risk": round(question_risk, 1),
        "checklist_risk": round(checklist_risk, 1),
        "conversational_texture": round(conversational_texture, 1),
        "grounding_score": round(grounding_score, 1),
        "candidate_score": round(candidate_score, 1),
        "word_count": words,
        "questions": metrics["question_count"],
        "contractions": contractions,
    }


def format_table(rows: list[dict]) -> str:
    headers = [
        "variant",
        "cand",
        "risk",
        "questions",
        "checklist",
        "texture",
        "grounding",
        "words",
    ]
    widths = {header: len(header) for header in headers}
    for row in rows:
        widths["variant"] = max(widths["variant"], len(row["variant"]))
        widths["cand"] = max(widths["cand"], len(f"{row['candidate_score']:.1f}"))
        widths["risk"] = max(widths["risk"], len(f"{row['synthetic_risk']:.1f}"))
        widths["questions"] = max(widths["questions"], len(f"{row['question_risk']:.1f}"))
        widths["checklist"] = max(widths["checklist"], len(f"{row['checklist_risk']:.1f}"))
        widths["texture"] = max(widths["texture"], len(f"{row['conversational_texture']:.1f}"))
        widths["grounding"] = max(widths["grounding"], len(f"{row['grounding_score']:.1f}"))
        widths["words"] = max(widths["words"], len(str(row["word_count"])))

    lines = []
    header_line = "  ".join(header.ljust(widths[header]) for header in headers)
    lines.append(header_line)
    lines.append("  ".join("-" * widths[header] for header in headers))
    for row in rows:
        lines.append(
            "  ".join(
                [
                    row["variant"].ljust(widths["variant"]),
                    f"{row['candidate_score']:.1f}".rjust(widths["cand"]),
                    f"{row['synthetic_risk']:.1f}".rjust(widths["risk"]),
                    f"{row['question_risk']:.1f}".rjust(widths["questions"]),
                    f"{row['checklist_risk']:.1f}".rjust(widths["checklist"]),
                    f"{row['conversational_texture']:.1f}".rjust(widths["texture"]),
                    f"{row['grounding_score']:.1f}".rjust(widths["grounding"]),
                    str(row["word_count"]).rjust(widths["words"]),
                ]
            )
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare multiple text variants against hypothesis-driven editorial metrics."
    )
    parser.add_argument("files", nargs="+", help="Text files to compare.")
    parser.add_argument(
        "--scorer",
        default=str(Path(__file__).with_name("score_text.py")),
        help="Path to score_text.py",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    score_module = load_score_module(Path(args.scorer))

    rows = []
    for file_path in args.files:
        path = Path(file_path)
        text = path.read_text(encoding="utf-8")
        row = score_variant(text, score_module)
        row["variant"] = path.stem
        rows.append(row)

    rows.sort(key=lambda row: (-row["candidate_score"], row["synthetic_risk"], row["variant"]))
    print("Higher `cand` is better. Lower `risk`, `questions`, and `checklist` are better.")
    print(format_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

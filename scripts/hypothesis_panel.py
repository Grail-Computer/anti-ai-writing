#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import importlib.util
import json
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
        r"\bsupport triage\b",
        r"\bqueue\b",
        r"\bticket",
        r"\bworkflow\b",
    ]
    return sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in patterns)


def find_finding(report: dict, code: str) -> dict | None:
    for finding in report.get("findings", []):
        if finding.get("code") == code:
            return finding
    return None


def pressure_from(report: dict, code: str, default: float = 0.0, multiplier: float = 100.0) -> float:
    finding = find_finding(report, code)
    if not finding:
        return default
    return clamp(finding["severity"] * multiplier)


def score_variant(text: str, score_module) -> dict:
    report = score_module.score_text(text)
    metrics = report["metrics"]
    words = max(1, int(metrics["word_count"]))
    contractions = count_contractions(text)
    contractions_per_100 = contractions / words * 100
    example_markers = count_example_markers(text)

    question_pressure = max(
        pressure_from(report, "question-battery"),
        clamp(metrics["question_count"] * 8),
    )
    checklist_pressure = clamp(
        pressure_from(report, "short-declarative-ladder", multiplier=55.0)
        + pressure_from(report, "repeated-openings", multiplier=45.0)
        + pressure_from(report, "micro-paragraphs", multiplier=25.0)
    )
    slop_profile_pressure = clamp(
        pressure_from(report, "parallelism-overuse", multiplier=45.0)
        + pressure_from(report, "low-lexical-diversity", multiplier=35.0)
        + pressure_from(report, "function-word-load", multiplier=25.0)
    )
    conversational_texture = clamp(
        contractions_per_100 * 10
        + metrics["sentence_length_cv"] * 35
        + metrics["paragraph_length_cv"] * 25
        + metrics["first_person_rate"] * 400
    )
    grounding_score = clamp(
        min(30, metrics["concrete_anchor_count"] * 6)
        + example_markers * 8
        + max(0, 20 - metrics["abstract_word_density"] * 200)
    )

    composite = clamp(
        (100 - report["overall_score"]) * 0.30
        + (100 - question_pressure) * 0.15
        + (100 - checklist_pressure) * 0.20
        + (100 - slop_profile_pressure) * 0.15
        + conversational_texture * 0.10
        + grounding_score * 0.10
    )

    top_codes = [finding["code"] for finding in report["findings"][:3]]

    return {
        "variant": "",
        "composite": round(composite, 1),
        "risk": round(report["overall_score"], 1),
        "question_pressure": round(question_pressure, 1),
        "checklist_pressure": round(checklist_pressure, 1),
        "slop_pressure": round(slop_profile_pressure, 1),
        "texture": round(conversational_texture, 1),
        "grounding": round(grounding_score, 1),
        "words": words,
        "top_codes": ",".join(top_codes) if top_codes else "-",
    }


def format_table(rows: list[dict]) -> str:
    headers = [
        "variant",
        "score",
        "risk",
        "q",
        "list",
        "slop",
        "texture",
        "ground",
        "words",
        "top_findings",
    ]
    widths = {header: len(header) for header in headers}
    for row in rows:
        widths["variant"] = max(widths["variant"], len(row["variant"]))
        widths["score"] = max(widths["score"], len(f"{row['composite']:.1f}"))
        widths["risk"] = max(widths["risk"], len(f"{row['risk']:.1f}"))
        widths["q"] = max(widths["q"], len(f"{row['question_pressure']:.1f}"))
        widths["list"] = max(widths["list"], len(f"{row['checklist_pressure']:.1f}"))
        widths["slop"] = max(widths["slop"], len(f"{row['slop_pressure']:.1f}"))
        widths["texture"] = max(widths["texture"], len(f"{row['texture']:.1f}"))
        widths["ground"] = max(widths["ground"], len(f"{row['grounding']:.1f}"))
        widths["words"] = max(widths["words"], len(str(row["words"])))
        widths["top_findings"] = max(widths["top_findings"], len(row["top_codes"]))

    lines = []
    lines.append("  ".join(header.ljust(widths[header]) for header in headers))
    lines.append("  ".join("-" * widths[header] for header in headers))
    for row in rows:
        lines.append(
            "  ".join(
                [
                    row["variant"].ljust(widths["variant"]),
                    f"{row['composite']:.1f}".rjust(widths["score"]),
                    f"{row['risk']:.1f}".rjust(widths["risk"]),
                    f"{row['question_pressure']:.1f}".rjust(widths["q"]),
                    f"{row['checklist_pressure']:.1f}".rjust(widths["list"]),
                    f"{row['slop_pressure']:.1f}".rjust(widths["slop"]),
                    f"{row['texture']:.1f}".rjust(widths["texture"]),
                    f"{row['grounding']:.1f}".rjust(widths["ground"]),
                    str(row["words"]).rjust(widths["words"]),
                    row["top_codes"].ljust(widths["top_findings"]),
                ]
            )
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare text variants across higher-level writing hypotheses built on top of score_text.py."
    )
    parser.add_argument("files", nargs="+", help="One or more UTF-8 text files to compare.")
    parser.add_argument(
        "--scorer",
        default=str(Path(__file__).with_name("score_text.py")),
        help="Path to the base score_text.py script.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
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

    rows.sort(key=lambda row: (-row["composite"], row["risk"], row["variant"]))

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0

    print("Higher `score` is better. Lower `risk`, `q`, `list`, and `slop` are better.")
    print(format_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Offline manuscript structure checks. Marker counts do not establish source truth."""
import argparse
from pathlib import Path
import re
import sys

CITATION = re.compile(r"（[^）]*(?:19|20)\d{2}[^）]*）|\([A-Z][^)]*(?:19|20)\d{2}[^)]*\)|\[(?:[A-Za-z]+-?\d+|[1-9][0-9]*(?:\s*-\s*[1-9][0-9]*)?(?:\s*,\s*[1-9][0-9]*(?:\s*-\s*[1-9][0-9]*)?)*)\]")
LIST = re.compile(r"^\s*(?:[-*+]\s+|[0-9]+\.\s+)", re.M)
PROCESS = re.compile(r"说明：|实验目的|表位|图位|回填模板|讨论提示|请用户|用户替换|写作要求|修改要求|this section is a template|discussion prompt|fill later", re.I)
PLACEHOLDER = re.compile(r"待回填|待实验回填|待真实实验替换|公式占位|算法占位|TODO|TBD", re.I)
OVERCLAIM = re.compile(r"实验结果表明|results show|verified", re.I)
ROLES = {"abstract", "introduction", "related-work", "methodology", "body", "empirical-results", "discussion", "conclusion", "references", "acknowledgements"}
RESULT_ARTIFACTS = ("plan/experiment-protocol.md", "plan/review/method-experiment-traceability.md",
                    "tables/table-schema.md", "figures/data-manifest.md")


def count_citations(text):
    return len(CITATION.findall(text))


def read(path):
    return path.read_text(encoding="utf-8-sig") if path.is_file() else ""


def chapter_specs(root, failures):
    path = root / "plan/chapter-architecture.md"
    if not path.is_file():
        failures.append("Missing plan/chapter-architecture.md; declare chapter roles before checking.")
        return []
    specs, seen = [], set()
    for line in read(path).splitlines():
        if not re.match(r"^\s*-\s*chapters/", line):
            continue
        parts = [part.strip() for part in line.strip()[1:].split("|")]
        rel = parts[0]
        target = root / rel
        if (not rel.endswith(".md") or ".." in Path(rel).parts
                or not target.resolve().is_relative_to(root)
                or not target.resolve().is_relative_to((root / "chapters").resolve())):
            failures.append(f"Invalid chapter path: {rel}")
            continue
        if rel in seen:
            failures.append(f"Duplicate chapter: {rel}")
            continue
        seen.add(rel)
        fields = {}
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                if key.strip() in fields:
                    failures.append(f"Duplicate chapter field: {rel} {key}")
                fields[key.strip()] = value.strip()
        role = fields.get("role")
        if role not in ROLES:
            failures.append(f"{rel}: missing or invalid role; choose from {', '.join(sorted(ROLES))}.")
        for field in ("min_chars", "min_citations", "min_paragraphs"):
            if field in fields and not re.fullmatch(r"[0-9]+", fields[field]):
                failures.append(f"{rel}: {field} must be a nonnegative integer.")
                fields[field] = "0"
        for field, choices in (("agent", {"required", "optional"}), ("placeholders", {"yes", "no"})):
            if field in fields and fields[field] not in choices:
                failures.append(f"{rel}: invalid {field}.")
        specs.append({"rel": rel, **fields})
    if not specs:
        failures.append("Chapter architecture has no valid chapter entries.")
    return specs


def prose_count(text):
    return sum(len(p.strip()) > 80 and not re.match(r"^\s*(?:#|[-*+]\s|\||```)", p)
               for p in re.split(r"\r?\n\s*\r?\n", text))


def check_project(project, submission=False):
    root = Path(project).resolve()
    failures, warnings = [], []
    if not root.is_dir():
        return [f"Project directory does not exist: {root}"], []
    chapters = root / "chapters"
    if not chapters.is_dir():
        failures.append(f"Missing chapters directory: {chapters}")
    elif not chapters.resolve().is_relative_to(root):
        return ["Chapter path escapes project: chapters"], []
    specs = chapter_specs(root, failures)
    expected = {spec["rel"] for spec in specs}
    actual = {p.relative_to(root).as_posix() for p in chapters.rglob("*.md")} if chapters.is_dir() else set()
    for rel in sorted(expected - actual):
        failures.append(f"Chapter architecture requires missing file: {rel}")
    for rel in sorted(actual - expected):
        failures.append(f"Unexpected chapter file not listed in plan/chapter-architecture.md: {rel}")
    provenance = read(root / "plan/chapter-agent-provenance.md")
    for spec in specs:
        rel, role = spec["rel"], spec.get("role")
        if rel not in actual:
            continue
        text = read(root / rel)
        chars = len(re.sub(r"\s", "", text))
        minimum = int(spec.get("min_chars", 0))
        if chars < minimum:
            failures.append(f"{rel} has {chars} non-whitespace characters; required min_chars={minimum}.")
        if spec.get("agent") == "required" and not any(rel in line and "status=ACCEPTED" in line for line in provenance.splitlines()):
            failures.append(f"{rel} requires an accepted chapter agent provenance entry.")
        exempt = role in {"references", "abstract", "acknowledgements"}
        if not exempt and len(LIST.findall(text)) > 3:
            failures.append(f"{rel} has too many list-like lines; full-paper chapters must be prose-led.")
        min_paragraphs = int(spec.get("min_paragraphs", 0 if exempt else 6))
        if prose_count(text) < min_paragraphs:
            failures.append(f"{rel} has too few substantial prose paragraphs; required {min_paragraphs}.")
        if spec.get("placeholders", "no") != "yes" and PLACEHOLDER.search(text):
            failures.append(f"{rel} contains unresolved placeholders but chapter architecture sets placeholders=no.")
        min_citations = int(spec.get("min_citations", {"introduction": 5, "related-work": 8}.get(role, 0)))
        count = count_citations(text)
        if count < min_citations:
            failures.append(f"{rel} has only {count} citation-like markers; required {min_citations} for role={role}.")
    chapter_texts = []
    for rel in sorted(actual):
        path = root / rel
        if not path.resolve().is_relative_to(root):
            failures.append(f"Chapter path escapes project: {rel}")
            continue
        text = read(path)
        chapter_texts.append(text)
        hits = len(PROCESS.findall(text))
        if hits:
            failures.append(f"{rel} contains process/user-instruction language ({hits} hits).")
        if len(LIST.findall(text)) > 12:
            warnings.append(f"{rel} has many list lines; verify prose style.")
    nonchapter_texts = []
    artifact_files = []
    for directory in ("plan", "tables", "figures", "refs"):
        for path in (root / directory).rglob("*"):
            if path.is_file() and path.suffix in {".md", ".csv", ".json", ".txt"}:
                if not path.resolve().is_relative_to(root):
                    failures.append(f"Artifact path escapes project: {path.relative_to(root)}")
                    continue
                artifact_files.append(path)
                nonchapter_texts.append(read(path))
    chapter_text = "\n".join(chapter_texts)
    nonchapter_text = "\n".join(nonchapter_texts)
    project_text = chapter_text + "\n" + nonchapter_text
    if not any((root / rel).is_file() for rel in ("refs/evidence-map.md", "plan/evidence-map.md")):
        failures.append("Missing evidence map: expected refs/evidence-map.md or plan/evidence-map.md.")
    if any(spec.get("role") == "empirical-results" for spec in specs):
        for artifact in RESULT_ARTIFACTS:
            if not (root / artifact).is_file():
                failures.append(f"Empirical results role requires {artifact}.")
        if OVERCLAIM.search(chapter_text) and re.search(r"mock_|synthetic_|PLANNING DATA", project_text):
            failures.append("Results text contains real-result language while mock/synthetic planning data is present.")
    for path in artifact_files:
        if path.name.startswith(("mock_", "synthetic_")):
            if "PLANNING DATA - replace before submission" not in read(path):
                failures.append(f"Mock/synthetic file lacks required planning-data marker: {path}")
            if submission:
                failures.append(f"Submission mode forbids mock/synthetic planning files: {path}")
    placeholders = len(PLACEHOLDER.findall(project_text))
    if placeholders:
        message = f"Unresolved placeholders found: {placeholders}."
        (failures if submission else warnings).append(message)
    return failures, warnings


def self_test():
    assert len(PROCESS.findall("实验目的\n回填模板\n[待回填-F1]")) == 2
    assert len(PLACEHOLDER.findall("实验目的\n回填模板\n[待回填-F1]")) == 1
    assert count_citations("[1] [1,2] [1-3] [FL-05] （张三，2024）") == 5


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", type=Path)
    parser.add_argument("--submission", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("Research quality gate self-test passed.")
        return 0
    if args.project_path is None:
        parser.error("--project-path is required unless --self-test is used")
    try:
        failures, warnings = check_project(args.project_path, args.submission)
    except (OSError, UnicodeError) as exc:
        print(f"Research quality gate failed: {exc}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"WARN: {warning}")
    for failure in failures:
        print(f"FAIL: {failure}")
    print(f"Research quality gate {'failed' if failures else 'passed'}.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

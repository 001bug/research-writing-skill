#!/usr/bin/env python3
"""Check resource completeness and workflow contracts without invoking any model."""
import argparse
import json
from pathlib import Path
import re
import sys
from install_dsh import catalog, InstallError

EXPECTED = set("brainstorming-research environment-setup evidence-driven-writing experiment-results-planning figures-diagram figures-python latex-output literature-review paper-orchestration peer-review prompts-collection statistical-analysis using-research-writing verification writing-chapters writing-core writing-humanities writing-law writing-medical".split())


def check(root):
    root = Path(root).resolve()
    failures = []
    try:
        skills = catalog(root)
    except (InstallError, OSError) as exc:
        return [str(exc)]
    if set(skills) != EXPECTED:
        failures.append(f"Skill catalog differs: missing={sorted(EXPECTED-set(skills))}, extra={sorted(set(skills)-EXPECTED)}")
    required = (".dsh/INSTALL.md", ".dsh/RUNTIME.md", "requirements-dsh.txt", "requirements-dsh.lock.txt",
                "scripts/research_quality_gate.py", "scripts/install_dsh.py", "scripts/dsh_runtime.py",
                "templates/figure-template.py", "templates/paper-outline.md", "templates/color-palettes.md",
                "skills/evidence-driven-writing/references/gpr-introduction-example.md")
    for rel in required:
        if not (root / rel).is_file():
            failures.append(f"Missing file: {rel}")
    for directory in ("templates", "plan-template", "latex-templates"):
        if not (root / directory).is_dir():
            failures.append(f"Missing resource directory: {directory}")
    for name, path in skills.items():
        text = (Path(path) / "SKILL.md").read_text(encoding="utf-8")
        if "## DSH 运行约定" not in text or ".dsh/RUNTIME.md" not in text:
            failures.append(f"{name}: missing DSH runtime/resource contract")
        if re.search(r"(?m)^python scripts/", text):
            failures.append(f"{name}: cwd-dependent Python command")
    # Retain upstream content contracts; the separate regression suite tests actual behavior.
    rules_path = root / "scripts/integrity-rules.json"
    try:
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        for rule in rules:
            path = root / rule["path"]
            if not path.is_file() or not re.search(rule["pattern"], path.read_text(encoding="utf-8")):
                failures.append(f"{rule['path']} missing: {rule['label']}")
    except (OSError, ValueError, KeyError) as exc:
        failures.append(f"Cannot load upstream integrity rules: {exc}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    failures = check(args.root)
    for failure in failures:
        print(f"FAIL: {failure}")
    print(f"Skill integrity check {'failed' if failures else 'passed'} (19 expected skills).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

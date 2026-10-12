#!/usr/bin/env python3
"""Resolve DSH skill resources after following the skill bundle's symbolic link."""
import argparse
import json
import os
from pathlib import Path


def resolve_root(skill_path):
    location = Path(skill_path).expanduser().resolve(strict=True)
    if location.is_file():
        location = location.parent
    root = location.parent.parent
    if location.parent.name != "skills" or not (location / "SKILL.md").is_file() or not (root / "scripts/install_dsh.py").is_file():
        raise ValueError(f"Not a research-writing skill directory: {location}")
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-path", type=Path, required=True)
    args = parser.parse_args()
    root = resolve_root(args.skill_path)
    home = Path(os.environ.get("DSH_HOME", "~/.dsh")).expanduser().resolve()
    print(json.dumps({"resource_root": str(root), "python": str(home / "research-writing/.venv/bin/python"),
                      "paper_root": str(Path.cwd().resolve())}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

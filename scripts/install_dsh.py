#!/usr/bin/env python3
"""Register complete skill bundles in the user's DSH catalog without overwriting skills."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile


class InstallError(RuntimeError):
    pass


def default_home():
    return Path(os.environ.get("DSH_HOME", "~/.dsh")).expanduser().resolve()


def catalog(root):
    root = Path(root).resolve()
    found = {}
    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
        name = re.search(r"^name:\s*([a-z0-9]+(?:-[a-z0-9]+)*)\s*$", match[1], re.M) if match else None
        description = re.search(r"^description:\s*\S", match[1], re.M) if match else None
        if not name or not description or name[1] != skill.parent.name or name[1] in found:
            raise InstallError(f"Invalid or duplicate skill frontmatter: {skill}")
        found[name[1]] = str(skill.parent)
    if not found:
        raise InstallError(f"No skills found under {root}")
    for directory in ("scripts", "templates", "plan-template"):
        if not (root / directory).is_dir():
            raise InstallError(f"Incomplete skill repository: missing {directory}")
    return found


def manifest_path(home):
    return Path(home) / "research-writing/installation.json"


def read_manifest(home):
    path = manifest_path(home)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        links = data["links"]
        if data["version"] != 1 or not isinstance(links, dict):
            raise ValueError("invalid version/links")
        for name, target in links.items():
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or not isinstance(target, str) or not Path(target).is_absolute():
                raise ValueError("invalid managed link")
        return links
    except (ValueError, KeyError, TypeError) as exc:
        raise InstallError(f"Invalid ownership manifest {path}: {exc}") from exc


def present(path):
    return path.exists() or path.is_symlink()


def owned(path, target):
    return path.is_symlink() and os.readlink(path) == target


def preflight(home, old, new):
    for name in sorted(old.keys() | new.keys()):
        path = home / "skills" / name
        if present(path) and (name not in old or not owned(path, old[name])):
            raise InstallError(f"Skill conflict; nothing changed: {path}")


def write_manifest(home, root, links):
    path = manifest_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump({"version": 1, "root": str(root), "links": links}, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def install(root, home):
    root, home = Path(root).resolve(), Path(home).expanduser().resolve()
    new, old = catalog(root), read_manifest(home)
    preflight(home, old, new)
    (home / "skills").mkdir(parents=True, exist_ok=True)
    changed = []
    try:
        for name in sorted(old.keys() | new.keys()):
            path = home / "skills" / name
            if name in new and owned(path, new[name]):
                continue
            previous = os.readlink(path) if path.is_symlink() else None
            changed.append((path, previous))
            if previous is not None:
                path.unlink()
            if name in new:
                path.symlink_to(new[name], target_is_directory=True)
        write_manifest(home, root, new)
    except Exception:
        for path, previous in reversed(changed):
            if path.is_symlink():
                path.unlink()
            if previous is not None:
                path.symlink_to(previous, target_is_directory=True)
        raise
    return new


def uninstall(home):
    home = Path(home).expanduser().resolve()
    old = read_manifest(home)
    preflight(home, old, {})
    for name, target in old.items():
        path = home / "skills" / name
        if owned(path, target):
            path.unlink()
    manifest_path(home).unlink(missing_ok=True)
    return old


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dsh-home", type=Path, default=default_home())
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    try:
        links = uninstall(args.dsh_home) if args.uninstall else install(args.root, args.dsh_home)
        print(f"{'Unregistered' if args.uninstall else 'Registered'} {len(links)} skills in {args.dsh_home / 'skills'}")
        return 0
    except (InstallError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

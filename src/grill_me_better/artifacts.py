"""Discover planning repo artifacts by path convention."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactRef:
    kind: str
    label: str
    rel_path: str


KIND_LABELS: dict[str, str] = {
    "glossary": "Glossary",
    "adr": "ADRs",
    "spec": "Specs",
    "ticket": "Tickets",
    "wayfinder": "Wayfinder",
    "research": "Research",
    "prototype": "Prototypes",
}

EMPTY_HELP: dict[str, str] = {
    "glossary": "Add GLOSSARY.md at the repo root.",
    "adr": "Add ADRs under docs/adr/ (e.g. 0001-slug.md).",
    "spec": "Add docs/SPEC.md or .scratch/<effort>/spec.md.",
    "ticket": "Add .scratch/<effort>/issues/NN-slug.md.",
    "wayfinder": "Add .scratch/<effort>/map.md for a wayfinder map.",
    "research": "Add docs/research/*.md or .scratch/*/research*.md.",
    "prototype": "Add .scratch/*/prototype* files.",
}


def discover_by_kind(planning_root: Path) -> dict[str, list[ArtifactRef]]:
    found: dict[str, list[ArtifactRef]] = {k: [] for k in KIND_LABELS}
    glossary = planning_root / "GLOSSARY.md"
    if glossary.is_file():
        found["glossary"].append(
            ArtifactRef("glossary", "GLOSSARY.md", "GLOSSARY.md")
        )
    for path in sorted((planning_root / "docs" / "adr").glob("*.md")):
        found["adr"].append(
            ArtifactRef("adr", path.name, _rel(planning_root, path))
        )
    for path in sorted(planning_root.glob("docs/SPEC*.md")):
        found["spec"].append(ArtifactRef("spec", path.name, _rel(planning_root, path)))
    for path in sorted(planning_root.glob(".scratch/*/spec.md")):
        found["spec"].append(ArtifactRef("spec", path.parent.name, _rel(planning_root, path)))
    for path in sorted(planning_root.glob(".scratch/*/issues/*.md")):
        found["ticket"].append(
            ArtifactRef("ticket", f"{path.parent.parent.name}/{path.name}", _rel(planning_root, path))
        )
    for path in sorted(planning_root.glob(".scratch/*/map.md")):
        found["wayfinder"].append(
            ArtifactRef("wayfinder", path.parent.name, _rel(planning_root, path))
        )
    research_dir = planning_root / "docs" / "research"
    if research_dir.is_dir():
        for path in sorted(research_dir.glob("*.md")):
            found["research"].append(
                ArtifactRef("research", path.name, _rel(planning_root, path))
            )
    for path in sorted(planning_root.glob(".scratch/*/research*.md")):
        found["research"].append(
            ArtifactRef("research", path.name, _rel(planning_root, path))
        )
    for path in sorted(planning_root.glob(".scratch/*/prototype*")):
        if path.is_file():
            found["prototype"].append(
                ArtifactRef("prototype", path.name, _rel(planning_root, path))
            )
    return found


def resolve_safe_path(planning_root: Path, rel_path: str) -> Path | None:
    root = planning_root.resolve()
    target = (planning_root / rel_path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()

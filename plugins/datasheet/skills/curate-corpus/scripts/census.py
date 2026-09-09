#!/usr/bin/env python3
"""Corpus metadata census — what is missing, and who can fix it.

`shelf verify` reports unknown revisions, unknown paper bylines, and
unconfirmed `auto` guesses. It does not report missing `source_url`, missing
`page_offset`, or an empty `title`, because none of those are errors — they are
debt. This script reports all of it, grouped by the tier that can close it, so
an agent fan-out can be planned without spending a single agent on triage.

Tiers:
    confirm   a value exists but is a machine guess (`auto`); corroborate it on
              a page the detector did not vote on, then clear the flag
    cover     readable from the document's own front matter (revision, title,
              paper year)
    offset    printed folio vs PDF index; needs two pages read and subtracted
    web       not in the document at all (source_url, and years no cover states)

Fields recorded as undoable are excluded from every count. Mark them with a
note (see --undoable), which is the only place shelf has to put that fact.

Usage:
    census.py [--root DIR] [--tier NAME] [--json] [--limit N]
    census.py --undoable <field> <reason>      # print the shelf edit command
"""

import argparse
import json
import sys
from pathlib import Path

# A note carrying this marker means "this field cannot be filled, stop asking".
UNDOABLE = "[curator: {field} undoable"

TIERS = ("confirm", "cover", "offset", "web")


def find_project_root() -> Path:
    """Walk up from CWD to find .claude/vibe-hacker.json."""
    p = Path.cwd()
    while p != p.parent:
        if (p / ".claude" / "vibe-hacker.json").exists():
            return p
        p = p.parent
    return Path.cwd()


def shelf_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    root = find_project_root()
    config = root / ".claude" / "vibe-hacker.json"
    sub = "docs/reference"
    if config.exists():
        with open(config) as f:
            sub = json.load(f).get("datasheet", {}).get("root", sub)
    return root / sub


def undoable(doc: dict, field: str) -> bool:
    return UNDOABLE.format(field=field) in (doc.get("notes") or "")


def gaps(doc: dict) -> list[tuple[str, str, str]]:
    """Return (tier, field, detail) for every open gap on one document."""
    out = []
    is_paper = doc.get("type") == "paper"

    for field in doc.get("auto") or []:
        out.append(("confirm", field, f"guessed {doc.get(field)!r} — corroborate and clear"))

    if is_paper:
        if not doc.get("authors") and not undoable(doc, "authors"):
            out.append(("cover", "authors", "byline — an initial must be present to believe it"))
        if not doc.get("year") and not undoable(doc, "year"):
            out.append(("web", "year", "not on the cover; DOI or venue lookup"))
    elif doc.get("revision") == "unknown" and not undoable(doc, "revision"):
        out.append(("cover", "revision", "document number line on the cover or footer"))

    if not doc.get("title") and not undoable(doc, "title"):
        out.append(("cover", "title", "title block on the cover"))

    if doc.get("page_offset") is None and "page_offset" not in (doc.get("auto") or []):
        if not undoable(doc, "page_offset"):
            out.append(("offset", "page_offset", "printed folio minus PDF index"))

    if not doc.get("source_url") and not undoable(doc, "source_url"):
        out.append(("web", "source_url", "vendor or publisher download URL"))

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="shelf root (directory containing shelf.json)")
    ap.add_argument("--tier", choices=TIERS, help="only this tier")
    ap.add_argument("--limit", type=int, help="at most N documents per tier")
    ap.add_argument("--json", action="store_true", help="machine-readable, for planning a fan-out")
    ap.add_argument("--undoable", nargs=2, metavar=("FIELD", "REASON"),
                    help="print the `shelf edit` note that retires a field, and exit")
    args = ap.parse_args()

    if args.undoable:
        field, reason = args.undoable
        print(f'shelf edit <id> --notes "<existing notes> {UNDOABLE.format(field=field)} — {reason}]"')
        return 0

    root = shelf_root(args.root)
    path = root / "shelf.json"
    if not path.is_file():
        print(f"census: no shelf.json at {path}", file=sys.stderr)
        return 2
    with open(path) as f:
        docs = json.load(f)["documents"]

    by_tier: dict[str, list[tuple[str, str, str]]] = {t: [] for t in TIERS}
    for doc in docs:
        for tier, field, detail in gaps(doc):
            by_tier[tier].append((doc["id"], field, detail))
    # Sorted by id so a batch is the same batch on every run — `--limit 8` twice
    # in a row must hand out the same eight documents, not a reshuffle.
    for rows in by_tier.values():
        rows.sort()

    tiers = [args.tier] if args.tier else list(TIERS)
    plan = {}
    for t in tiers:
        rows = by_tier[t]
        ids = sorted({i for i, _, _ in rows})
        kept = ids[: args.limit] if args.limit else ids
        plan[t] = (rows, ids, [r for r in rows if r[0] in set(kept)])

    if args.json:
        out = {t: [{"id": i, "field": f, "detail": d} for i, f, d in shown]
               for t, (_, _, shown) in plan.items()}
        json.dump(out, sys.stdout, indent=2)
        print()
        return 0

    total = 0
    for t, (rows, ids, shown) in plan.items():
        total += len(rows)
        print(f"\n{t.upper()}  {len(rows)} field(s) across {len(ids)} document(s)")
        for doc_id, field, detail in shown:
            print(f"  {doc_id:<50} {field:<13} {detail}")
        if args.limit and len(ids) > args.limit:
            print(f"  … {len(ids) - args.limit} more document(s)")
    print(f"\n{len(docs)} documents, {total} open field(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

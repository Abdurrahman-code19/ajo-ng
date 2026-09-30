#!/usr/bin/env python3
"""
build_spec — assemble every section module into the final AJO.ng specification DOCX.

    python3 docs/src/build_spec.py [--out PATH] [--check]

The section list and its order live in sections/frontmatter.py (SECTIONS), so
reordering the document is a one-line change rather than an edit to the builder.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import importlib
import os
import sys
import traceback
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

from docxkit import SpecBuilder, render  # noqa: E402

DEFAULT_OUT = os.path.join(
    ROOT, "AJO-ng-Complete-Product-Technical-Specification.docx"
)

TAGLINE = "Your Ajo. Your Story."
TITLE = "AJO.ng — Complete Product and Technical Specification"
SUBTITLE = "Complete Product and Technical Specification"
VERSION = "1.0"

# frontmatter supplies these as a single module so the document has one front end
from sections import frontmatter as FM  # noqa: E402


def _load(module: str):
    return importlib.import_module(f"sections.{module}")


def build(out_path: str) -> dict:
    date = _dt.date.today().isoformat()

    builder = SpecBuilder(
        title=TITLE,
        subtitle=SUBTITLE,
        tagline=TAGLINE,
        version=VERSION,
        date=date,
        classification="Internal — Confidential",
    )

    # ---- cover, legal statement, contents
    builder.cover(meta_rows=FM.COVER_META)
    builder.pagebreak()
    builder.h1("Document Control and Legal Statement")
    builder.p(FM.LEGAL_STATEMENT)
    builder.h2("How to use this document")
    builder.p(
        "This is a single source of truth for the AJO.ng product, design, "
        "architecture, operations, and open compliance questions. The canonical "
        "business rules live in docs/src/CANONICAL.md, and where the two disagree, "
        "CANONICAL.md and this document take precedence over all earlier business "
        "and financial material."
    )
    builder.toc()

    # ---- executive summary
    render(builder, FM.EXECUTIVE_SUMMARY)
    # ---- product overview
    render(builder, FM.PRODUCT_OVERVIEW)

    # ---- sections 1..26 in declared order
    rendered, errors = [], []
    for title, module in FM.SECTIONS:
        if module == "frontmatter":
            continue
        try:
            mod = _load(module)
        except Exception:  # noqa: BLE001
            errors.append((title, module, traceback.format_exc(limit=3)))
            continue
        blocks = getattr(mod, "BLOCKS", None)
        if not blocks:
            errors.append((title, module, "module has no BLOCKS"))
            continue
        render(builder, blocks)
        rendered.append(title)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    builder.save(out_path)
    _normalise_zip(out_path)

    return {
        "path": out_path,
        "rendered": rendered,
        "errors": errors,
        "blocks": len(builder.doc.element.body),
    }


# A fixed DOS timestamp for every zip entry. The zip format cannot store a year
# before 1980, and 1980-01-01 is the earliest value it can represent, so it is
# both the canonical "no real time" constant and a valid one.
_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def _normalise_zip(path: str) -> None:
    """Rewrite a DOCX with deterministic zip metadata.

    python-docx stamps each zip entry with the wall-clock time of the build, so
    two builds of identical content produce different bytes. That makes it
    impossible to tell "the committed specification is stale" apart from "somebody
    rebuilt it", which is exactly the distinction CI needs to make. Entries are
    also written in a stable order and with a fixed compression level, so an
    unchanged spec always rebuilds to an identical file.
    """
    with zipfile.ZipFile(path) as src:
        entries = [
            (info.filename, info.compress_type, src.read(info.filename))
            for info in sorted(src.infolist(), key=lambda i: i.filename)
        ]

    tmp = f"{path}.tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for name, compress_type, payload in entries:
            info = zipfile.ZipInfo(filename=name, date_time=_ZIP_EPOCH)
            info.compress_type = compress_type
            # The external attributes are what mark an entry as a regular file;
            # without them a reader may treat the part as a directory.
            info.external_attr = 0o600 << 16
            dst.writestr(info, payload)

    os.replace(tmp, path)


def check(path: str) -> int:
    """Structural verification: the file is a valid, readable, non-trivial DOCX."""
    problems = []
    if not os.path.exists(path):
        print(f"FAIL  file not found: {path}")
        return 1

    size = os.path.getsize(path)
    if size < 200_000:
        problems.append(f"file is suspiciously small: {size:,} bytes")

    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad:
            problems.append(f"corrupt zip member: {bad}")
        names = zf.namelist()
        for required in ("[Content_Types].xml", "word/document.xml", "word/settings.xml"):
            if required not in names:
                problems.append(f"missing part: {required}")
        document = zf.read("word/document.xml").decode("utf-8", "replace")
        settings = (zf.read("word/settings.xml").decode("utf-8", "replace")
                    if "word/settings.xml" in names else "")
        # PAGE / NUMPAGES live in the footer part, not the body
        footers = "".join(
            zf.read(n).decode("utf-8", "replace") for n in names if "footer" in n
        )
        headers = "".join(
            zf.read(n).decode("utf-8", "replace") for n in names if "header" in n
        )

    checks = {
        "TOC field present": "TOC \\o" in document,
        "PAGE field present": "PAGE" in footers,
        "NUMPAGES field present": "NUMPAGES" in footers,
        "tagline in footer": "Your Ajo" in footers,
        "running header present": bool(headers.strip()),
        "updateFields enabled": "updateFields" in settings,
    }
    for name, ok in checks.items():
        if not ok:
            problems.append(f"check failed: {name}")

    h1_count = document.count('w:val="Heading1"')
    tables = document.count("<w:tbl>")
    if h1_count < 20:
        problems.append(f"expected 20+ Heading 1 paragraphs, found {h1_count}")
    if tables < 100:
        problems.append(f"expected 100+ tables, found {tables}")

    print(f"file    {path}")
    print(f"size    {size:,} bytes")
    print(f"h1      {h1_count}   tables {tables}   body children {len(document)//1000}k/1000 chars")
    for name, ok in checks.items():
        print(f"{'ok  ' if ok else 'FAIL'}  {name}")

    if problems:
        print("\nPROBLEMS")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nPASS  structure verified")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    result = build(args.out)

    print(f"built   {result['path']}")
    print(f"sections rendered: {len(result['rendered'])}")
    if result["errors"]:
        print("\nSECTION ERRORS")
        for title, module, err in result["errors"]:
            print(f"\n  {title} ({module})\n{err}")
        return 1

    if args.check:
        return check(result["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

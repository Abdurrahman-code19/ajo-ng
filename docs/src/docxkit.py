"""
docxkit — the document engine for the AJO.ng specification.

A small block DSL so 25 sections of content can be authored as readable Python
instead of hand-placed Word objects, and rendered with consistent styling,
brand colours, working page numbers and a live table of contents.

Block types:
    h1, h2, h3, h4   headings (h1 starts a new page)
    p                body paragraph
    lead              larger intro paragraph
    bullets, numbers  lists
    table             header row + body rows
    code              monospace diagram / snippet
    callout           emphasised box: NOTE | WARNING | LEGAL | ASSUMPTION | DECISION
    kv                two-column definition list
    pagebreak
    toc, cover
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Sequence

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

# ------------------------------------------------------------------ brand
DEEP = "0B1F3A"
PRIMARY = "146EF5"
CYAN = "22C7D6"
GOLD = "FBBF24"
WHITE = "FFFFFF"
CLOUD = "F4F7FB"
DARK = "101828"

MUTED = "475467"
LINE = "D0D5DD"
CALLOUT_FILL = {
    "NOTE": "EFF6FF",
    "WARNING": "FEF3C7",
    "LEGAL": "FEE2E2",
    "ASSUMPTION": "EDE9FE",
    "DECISION": "E0F2FE",
}
CALLOUT_BAR = {
    "NOTE": PRIMARY,
    "WARNING": GOLD,
    "LEGAL": "DC2626",
    "ASSUMPTION": "7C3AED",
    "DECISION": CYAN,
}

BODY_FONT = "Calibri"
MONO_FONT = "Consolas"

INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\*[^*]+\*)")


# ------------------------------------------------------------ xml helpers
def _shade(el, fill: str) -> None:
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    el.append(shd)


def _shade_paragraph(p, fill: str) -> None:
    _shade(p._p.get_or_add_pPr(), fill)


def _shade_cell(cell, fill: str) -> None:
    _shade(cell._tc.get_or_add_tcPr(), fill)


def _cell_margins(cell, top=60, bottom=60, left=110, right=110) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for tag, val in (("top", top), ("start", left), ("bottom", bottom), ("end", right)):
        node = OxmlElement(f"w:{tag}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    tcPr.append(mar)


def _paragraph_border(p, color: str, size: int = 6, sides: Sequence[str] = ("left",)) -> None:
    pPr = p._p.get_or_add_pPr()
    bdr = pPr.find(qn("w:pBdr"))
    if bdr is None:
        bdr = OxmlElement("w:pBdr")
        pPr.append(bdr)
    for side in sides:
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), str(size))
        node.set(qn("w:space"), "6")
        node.set(qn("w:color"), color)
        bdr.append(node)


def _keep_with_next(p) -> None:
    pPr = p._p.get_or_add_pPr()
    node = OxmlElement("w:keepNext")
    pPr.append(node)


def _no_split(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    node = OxmlElement("w:cantSplit")
    trPr.append(node)


def _repeat_header(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    node = OxmlElement("w:tblHeader")
    trPr.append(node)


def _field(paragraph, instruction: str) -> None:
    """Insert a Word field (PAGE, TOC, NUMPAGES...)."""
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t")
    txt.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for node in (begin, instr, sep, txt, end):
        run._r.append(node)


# ------------------------------------------------------------- inline text
def _add_runs(paragraph, text: str, size: float = 10.5, color: str = DARK,
              bold: bool = False, italic: bool = False, font: str = BODY_FONT) -> None:
    """Render **bold**, *italic* and `code` inline spans."""
    for token in INLINE.split(text):
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            r = paragraph.add_run(token[2:-2])
            r.bold = True
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            r = paragraph.add_run(token[1:-1])
            r.font.name = MONO_FONT
            r.font.size = Pt(size - 1)
            r.font.color.rgb = RGBColor.from_string(PRIMARY)
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            r = paragraph.add_run(token[1:-1])
            r.italic = True
        else:
            r = paragraph.add_run(token)
            r.bold = bold
            r.italic = italic
        if r.font.name is None:
            r.font.name = font
        r.font.size = Pt(size)
        if r.font.color.rgb is None:
            r.font.color.rgb = RGBColor.from_string(color)


# ------------------------------------------------------------------ styles
def _base_styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(DARK)
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.13

    for name, size, color, before, after in (
        ("Heading 1", 20, DEEP, 20, 9),
        ("Heading 2", 14.5, PRIMARY, 15, 6),
        ("Heading 3", 12, DEEP, 11, 4),
        ("Heading 4", 10.5, MUTED, 9, 3),
    ):
        st = doc.styles[name]
        st.font.name = BODY_FONT
        st.font.size = Pt(size)
        st.font.color.rgb = RGBColor.from_string(color)
        st.font.bold = True
        st.font.italic = False
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True


# ------------------------------------------------------------- the builder
class SpecBuilder:
    def __init__(self, *, title: str, subtitle: str, tagline: str, version: str,
                 date: str, classification: str = "Internal — Confidential") -> None:
        self.doc = Document()
        self.meta = dict(title=title, subtitle=subtitle, tagline=tagline,
                         version=version, date=date, classification=classification)
        self.toc_entries: list[tuple[int, str]] = []
        self._first_h1 = True
        self._setup()

    # ---------------------------------------------------------- scaffolding
    def _setup(self) -> None:
        doc = self.doc
        _base_styles(doc)

        section = doc.sections[0]
        section.page_width = Inches(8.27)   # A4
        section.page_height = Inches(11.69)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.75)

        # running header
        hp = section.header.paragraphs[0]
        hp.text = ""
        r = hp.add_run(f"{self.meta['title']}  ·  {self.meta['classification']}")
        r.font.size = Pt(8)
        r.font.color.rgb = RGBColor.from_string(MUTED)
        r.font.name = BODY_FONT
        _paragraph_border(hp, LINE, 4, ("bottom",))

        # running footer with page numbers
        fp = section.footer.paragraphs[0]
        fp.text = ""
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = fp.add_run(f"{self.meta['tagline']}     |     Page ")
        r.font.size = Pt(8)
        r.font.color.rgb = RGBColor.from_string(MUTED)
        r.font.name = BODY_FONT
        _field(fp, " PAGE ")
        r = fp.add_run(" of ")
        r.font.size = Pt(8)
        r.font.color.rgb = RGBColor.from_string(MUTED)
        r.font.name = BODY_FONT
        _field(fp, " NUMPAGES ")
        for run in fp.runs:
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor.from_string(MUTED)
            run.font.name = BODY_FONT

    # -------------------------------------------------------------- helpers
    def _h(self, level: int, text: str) -> None:
        if level == 1:
            if not self._first_h1:
                self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            self._first_h1 = False
        p = self.doc.add_paragraph()
        style = self.doc.styles[f"Heading {level}"]
        p.style = style
        size = {1: 20, 2: 14.5, 3: 12, 4: 10.5}[level]
        colour = {1: DEEP, 2: PRIMARY, 3: DEEP, 4: MUTED}[level]
        _add_runs(p, text, size=size, color=colour, bold=True)
        for run in p.runs:
            run.font.name = BODY_FONT
            run.bold = True
        if level == 1:
            self.toc_entries.append((1, text))
            _paragraph_border(p, PRIMARY, 12, ("bottom",))
            p.paragraph_format.space_after = Pt(12)
        elif level == 2:
            self.toc_entries.append((2, text))

    def _pagebreak(self) -> None:
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # --------------------------------------------------------------- blocks
    def h1(self, text: str) -> None:
        self._h(1, text)

    def h2(self, text: str) -> None:
        self._h(2, text)

    def h3(self, text: str) -> None:
        self._h(3, text)

    def h4(self, text: str) -> None:
        self._h(4, text)

    def p(self, text: str) -> None:
        par = self.doc.add_paragraph()
        _add_runs(par, text)

    def lead(self, text: str) -> None:
        par = self.doc.add_paragraph()
        par.paragraph_format.space_after = Pt(10)
        _add_runs(par, text, size=12, color=MUTED)

    def bullets(self, items: Iterable[str], indent: int = 0) -> None:
        for item in items:
            par = self.doc.add_paragraph(style="List Bullet")
            par.paragraph_format.left_indent = Inches(0.25 + 0.25 * indent)
            par.paragraph_format.space_after = Pt(3)
            _add_runs(par, item)

    def numbers(self, items: Iterable[str]) -> None:
        for item in items:
            par = self.doc.add_paragraph(style="List Number")
            par.paragraph_format.left_indent = Inches(0.3)
            par.paragraph_format.space_after = Pt(3)
            _add_runs(par, item)

    def kv(self, pairs: Sequence[tuple[str, Any]]) -> None:
        for key, val in pairs:
            par = self.doc.add_paragraph()
            par.paragraph_format.left_indent = Inches(0.12)
            par.paragraph_format.space_after = Pt(2)
            r = par.add_run(f"{key}  ")
            r.bold = True
            r.font.size = Pt(10.5)
            r.font.color.rgb = RGBColor.from_string(DEEP)
            r.font.name = BODY_FONT
            _add_runs(par, "None" if val is None else str(val))

    def table(self, head: Sequence[str], rows: Sequence[Sequence[str]],
              widths: Sequence[float] | None = None, font_size: float = 8.8,
              zebra: bool = True) -> None:
        ncols = len(head)
        table = self.doc.add_table(rows=1, cols=ncols)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True

        hdr = table.rows[0]
        _repeat_header(hdr)
        _no_split(hdr)
        for i, label in enumerate(head):
            cell = hdr.cells[i]
            cell.text = ""
            par = cell.paragraphs[0]
            par.paragraph_format.space_after = Pt(0)
            _add_runs(par, str(label), size=font_size, color=WHITE, bold=True)
            _shade_cell(cell, DEEP)
            _cell_margins(cell)

        for ridx, row in enumerate(rows):
            cells = table.add_row().cells
            _no_split(table.rows[-1])
            for i in range(ncols):
                value = str(row[i]) if i < len(row) else ""
                cell = cells[i]
                cell.text = ""
                par = cell.paragraphs[0]
                par.paragraph_format.space_after = Pt(0)
                _add_runs(par, value, size=font_size, color=DARK)
                _cell_margins(cell)
                if zebra and ridx % 2 == 1:
                    _shade_cell(cell, CLOUD)

        if widths:
            for row in table.rows:
                for i, w in enumerate(widths):
                    if i < len(row.cells):
                        row.cells[i].width = Inches(w)

        self.doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def code(self, text: str, font_size: float = 8.0, fill: str = "F7F9FC") -> None:
        lines = text.strip("\n").split("\n")
        for line in lines:
            par = self.doc.add_paragraph()
            pf = par.paragraph_format
            pf.space_before = Pt(0)
            pf.space_after = Pt(0)
            pf.left_indent = Inches(0.16)
            pf.line_spacing = 1.0
            _shade_paragraph(par, fill)
            _paragraph_border(par, LINE, 4, ("left",))
            run = par.add_run(line if line else " ")
            run.font.name = MONO_FONT
            run.font.size = Pt(font_size)
            run.font.color.rgb = RGBColor.from_string(DEEP)

    def callout(self, kind: str, text: str, title: str | None = None) -> None:
        kind = kind.upper()
        fill = CALLOUT_FILL.get(kind, CLOUD)
        bar = CALLOUT_BAR.get(kind, PRIMARY)
        par = self.doc.add_paragraph()
        pf = par.paragraph_format
        pf.space_before = Pt(7)
        pf.space_after = Pt(9)
        pf.left_indent = Inches(0.1)
        _shade_paragraph(par, fill)
        _paragraph_border(par, bar, 18, ("left",))
        if title:
            r = par.add_run(f"{title}  ")
            r.bold = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor.from_string(bar)
            r.font.name = BODY_FONT
        _add_runs(par, text, size=9.5, color=DEEP)

    def pagebreak(self) -> None:
        self._pagebreak()

    # ---------------------------------------------------------- front matter
    def cover(self, meta_rows: Sequence[tuple[str, str]] | None = None) -> None:
        doc = self.doc
        for _ in range(2):
            doc.add_paragraph()

        band = doc.add_paragraph()
        band.paragraph_format.space_after = Pt(2)
        r = band.add_run("  AJO.ng  ")
        r.bold = True
        r.font.size = Pt(30)
        r.font.color.rgb = RGBColor.from_string(WHITE)
        r.font.name = BODY_FONT
        _shade_paragraph(band, DEEP)

        bar = doc.add_paragraph()
        bar.paragraph_format.space_after = Pt(26)
        bar.paragraph_format.space_before = Pt(0)
        r = bar.add_run("  " + " " * 60)
        r.font.size = Pt(5)
        _shade_paragraph(bar, CYAN)

        tag = doc.add_paragraph()
        r = tag.add_run(self.meta["tagline"])
        r.font.size = Pt(17)
        r.font.color.rgb = RGBColor.from_string(PRIMARY)
        r.bold = True
        r.font.name = BODY_FONT
        tag.paragraph_format.space_after = Pt(4)

        sub = doc.add_paragraph()
        r = sub.add_run(self.meta["subtitle"])
        r.font.size = Pt(11.5)
        r.font.color.rgb = RGBColor.from_string(MUTED)
        r.font.name = BODY_FONT
        sub.paragraph_format.space_after = Pt(30)

        for label, value in (meta_rows if meta_rows is not None else (
            ("Document", self.meta["title"]),
            ("Version", self.meta["version"]),
            ("Status", "Draft for review — pre-launch"),
            ("Date", self.meta["date"]),
            ("Classification", self.meta["classification"]),
            ("Product stage", "Pre-launch. No live transaction volume. No customer data."),
            ("Founders", "Abdurrahman Lawal & Abdurrahman Oriolowo — Co-Founders"),
        )):
            par = doc.add_paragraph()
            par.paragraph_format.space_after = Pt(3)
            r = par.add_run(f"{label}:  ")
            r.bold = True
            r.font.size = Pt(10)
            r.font.color.rgb = RGBColor.from_string(DEEP)
            r.font.name = BODY_FONT
            r = par.add_run(value)
            r.font.size = Pt(10)
            r.font.color.rgb = RGBColor.from_string(DARK)
            r.font.name = BODY_FONT

        doc.add_paragraph()
        note = doc.add_paragraph()
        note.paragraph_format.space_before = Pt(14)
        _shade_paragraph(note, "FEF3C7")
        _paragraph_border(note, GOLD, 18, ("left",))
        r = note.add_run(
            "This document is a technical and product blueprint. It is not legal, "
            "regulatory, tax or investment advice. Statements about Nigerian financial "
            "regulation, data protection and payment-provider capabilities require "
            "verification by qualified Nigerian professionals and by the appointed "
            "payment partner before production launch."
        )
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor.from_string(DEEP)
        r.font.name = BODY_FONT

    def toc(self) -> None:
        self._pagebreak()
        p = self.doc.add_paragraph()
        p.style = self.doc.styles["Heading 1"]
        r = p.add_run("Table of Contents")
        r.bold = True
        r.font.size = Pt(20)
        r.font.color.rgb = RGBColor.from_string(DEEP)
        r.font.name = BODY_FONT
        _paragraph_border(p, PRIMARY, 12, ("bottom",))

        hint = self.doc.add_paragraph()
        r = hint.add_run(
            "If the list below is empty, select it and press F9 (Word) to update fields."
        )
        r.font.size = Pt(8.5)
        r.italic = True
        r.font.color.rgb = RGBColor.from_string(MUTED)
        r.font.name = BODY_FONT

        par = self.doc.add_paragraph()
        _field(par, r' TOC \o "1-2" \h \z \u ')

        # The TOC field expands to an unknown number of pages, so content must start
        # on a fresh page rather than flowing immediately after the field.
        self._first_h1 = True
        self._pagebreak()

    def enable_update_fields(self) -> None:
        settings = self.doc.settings.element
        node = OxmlElement("w:updateFields")
        node.set(qn("w:val"), "true")
        settings.append(node)

    def save(self, path: str) -> None:
        self.enable_update_fields()
        self.doc.save(path)


# --------------------------------------------------------- authoring sugar
def _flatten(blocks: Iterable[Any]) -> list[dict[str, Any]]:
    """Allow a block helper to return either one block or a list of blocks."""
    out: list[dict[str, Any]] = []
    for block in blocks:
        if isinstance(block, dict):
            out.append(block)
        elif isinstance(block, (list, tuple)):
            out.extend(_flatten(block))
        else:
            raise TypeError(f"block must be a dict or a list of dicts, got {type(block)}")
    return out


def render(builder: SpecBuilder, blocks: Sequence[dict[str, Any]]) -> None:
    """Render a list of block dicts onto the builder."""
    for block in _flatten(blocks):
        kind = block["t"]
        if kind == "h1":
            builder.h1(block["text"])
        elif kind == "h2":
            builder.h2(block["text"])
        elif kind == "h3":
            builder.h3(block["text"])
        elif kind == "h4":
            builder.h4(block["text"])
        elif kind == "p":
            builder.p(block["text"])
        elif kind == "lead":
            builder.lead(block["text"])
        elif kind == "bullets":
            builder.bullets(block["items"])
        elif kind == "numbers":
            builder.numbers(block["items"])
        elif kind == "table":
            builder.table(block["head"], block["rows"],
                          widths=block.get("widths"),
                          font_size=block.get("size", 8.8))
        elif kind == "code":
            builder.code(block["text"], font_size=block.get("size", 8.0))
        elif kind == "callout":
            builder.callout(block.get("kind", "NOTE"), block["text"], block.get("title"))
        elif kind == "kv":
            builder.kv(block["pairs"])
        elif kind == "pagebreak":
            builder.pagebreak()
        else:
            raise ValueError(f"unknown block type: {kind}")

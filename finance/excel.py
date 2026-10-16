"""Write a real .xlsx with no third-party library.

An xlsx is a zip of XML parts, so the standard library can produce one. That
keeps the tracker dependency-free (ADR 001's reasoning applies here too): an
accountant can run this on any machine with Python and open the result in
Excel, LibreOffice or Numbers.

What this deliberately does not do: formulas, charts, merged cells, multiple
fonts. It writes typed cells — real numbers and real dates, not strings that
look like them — because a spreadsheet you cannot sum is not worth exporting.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

# Excel counts days from 1899-12-30 (the leap-year bug is baked into the format).
EXCEL_EPOCH = date(1899, 12, 30)

# Style indices into the cellXfs list built in _styles().
S_DEFAULT, S_HEADER, S_MONEY, S_DATE, S_BOLD_MONEY = 0, 1, 2, 3, 4


@dataclass
class Sheet:
    name: str
    headers: list[str]
    rows: list[list] = field(default_factory=list)
    widths: list[int] = field(default_factory=list)
    note: str = ""


def _col_letter(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _cell(ref: str, value, style: int) -> str:
    """One <c> element, typed by what the value actually is."""
    if value is None or value == "":
        return f'<c r="{ref}" s="{style}"/>'
    if isinstance(value, bool):
        value = "yes" if value else ""
        return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
    if isinstance(value, (date, datetime)):
        day = value.date() if isinstance(value, datetime) else value
        return f'<c r="{ref}" s="{S_DATE}"><v>{(day - EXCEL_EPOCH).days}</v></c>'
    if isinstance(value, Decimal):
        return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'


def _sheet_xml(sheet: Sheet) -> str:
    cols = ""
    if sheet.widths:
        entries = "".join(
            f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>'
            for i, w in enumerate(sheet.widths)
        )
        cols = f"<cols>{entries}</cols>"

    body = [
        "<row r='1'>"
        + "".join(
            _cell(f"{_col_letter(i)}1", h, S_HEADER) for i, h in enumerate(sheet.headers)
        )
        + "</row>"
    ]
    for offset, row in enumerate(sheet.rows, start=2):
        cells = []
        for i, value in enumerate(row):
            style = S_MONEY if isinstance(value, Decimal) else S_DEFAULT
            cells.append(_cell(f"{_col_letter(i)}{offset}", value, style))
        body.append(f"<row r='{offset}'>" + "".join(cells) + "</row>")

    last = _col_letter(max(len(sheet.headers) - 1, 0))
    rows_end = len(sheet.rows) + 1
    # Freeze the header and switch on filtering: the first things anyone does
    # to a sheet this shape.
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        f"{cols}<sheetData>{''.join(body)}</sheetData>"
        f'<autoFilter ref="A1:{last}{max(rows_end, 1)}"/>'
        "</worksheet>"
    )


def _styles() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<numFmts count="2">'
        '<numFmt numFmtId="164" formatCode="#,##0.00"/>'
        '<numFmt numFmtId="165" formatCode="yyyy\\-mm\\-dd"/>'
        "</numFmts>"
        '<fonts count="2">'
        '<font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><name val="Calibri"/></font>'
        "</fonts>"
        '<fills count="3">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFF2E8EC"/>'
        '<bgColor indexed="64"/></patternFill></fill>'
        "</fills>"
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
        '<cellXfs count="5">'
        "<xf/>"
        '<xf fontId="1" fillId="2" applyFont="1" applyFill="1"/>'
        '<xf numFmtId="164" applyNumberFormat="1"/>'
        '<xf numFmtId="165" applyNumberFormat="1"/>'
        '<xf numFmtId="164" fontId="1" applyNumberFormat="1" applyFont="1"/>'
        "</cellXfs>"
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        "</styleSheet>"
    )


def build_workbook(sheets: list[Sheet]) -> bytes:
    """The workbook as bytes, so it can be written to disk or embedded."""
    buffer = io.BytesIO()
    _write(buffer, sheets)
    return buffer.getvalue()


def write_workbook(path: Path | str, sheets: list[Sheet]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_workbook(sheets))
    return path


def _write(target, sheets: list[Sheet]) -> None:
    names = [s.name[:31] for s in sheets]  # Excel caps sheet names at 31 chars
    tabs = "".join(
        f'<sheet name="{escape(name)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>'
        for i, name in enumerate(names)
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{tabs}</sheets></workbook>"
    )
    rels = "".join(
        f'<Relationship Id="rId{i + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{i + 1}.xml"/>'
        for i in range(len(sheets))
    )
    styles_rel = (
        f'<Relationship Id="rId{len(sheets) + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
    )
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(len(sheets))
    )

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            f"{overrides}</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/></Relationships>',
        )
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{rels}{styles_rel}</Relationships>",
        )
        zf.writestr("xl/styles.xml", _styles())
        for i, sheet in enumerate(sheets):
            zf.writestr(f"xl/worksheets/sheet{i + 1}.xml", _sheet_xml(sheet))

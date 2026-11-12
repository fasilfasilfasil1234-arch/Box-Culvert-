"""
edrc_sheet.py - build engineering calculation sheets in the L&T Construction /
Heavy Civil Infrastructure - EDRC Excel format.

The format is a single continuous calculation sheet, not a set of tables:

    A = code / source reference   (8pt bold italic, wrapped, centred)
    B = description               (11pt; bold for section headings)
  C,D = substituted-number working string, built dynamically with TEXT()
    E = "="
    F = value   RED = input/given, BLACK = calculated, BOLD = key result
    G = unit

Vertical frame rules only (left of A, left of B, right of F, right of G);
no horizontal rules in the body. Rows 1-8 are the title block and repeat on
every printed page. Supporting calculations live from column I rightwards,
deliberately OUTSIDE the print area.

Typical use:

    from edrc_sheet import EDRCSheet
    s = EDRCSheet(title="DESIGN OF ...", designed="MF", checked="ASB")
    s.section("1", "DESIGN OF ...", size=12)
    s.head("1.1", "Design Data")
    r_W = s.row(ref="Design input", desc="Load (W)", val=100, unit="kN",
                fmt="0.000", inp=True)
    r_b = s.row(desc="Width (b)", val=300, unit="mm", fmt="0.0", inp=True)
    s.row(desc="Area", work=f'="="&TEXT(F{r_W},"0.0")&"/"&TEXT(F{r_b},"0")',
          val=f"=F{r_W}/F{r_b}", unit="kN/mm", fmt="0.000", key=True)
    s.finish("/path/out.xlsx")

Then ALWAYS recalculate and re-pin the column widths - see SKILL.md.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule
from openpyxl.utils import column_index_from_string
import os

TNR = "Times New Roman"

# ---- fonts -----------------------------------------------------------------
F10   = Font(name=TNR, size=10)
F10B  = Font(name=TNR, size=10, bold=True)
F11   = Font(name=TNR, size=11)
F11B  = Font(name=TNR, size=11, bold=True)
F11I  = Font(name=TNR, size=11, italic=True)
F11R  = Font(name=TNR, size=11, color="FFFF0000")               # input value
F11RB = Font(name=TNR, size=11, bold=True, color="FFFF0000")
F11BB = Font(name=TNR, size=11, bold=True)                      # key result
F8BI  = Font(name=TNR, size=8, bold=True, italic=True)          # col A reference
F10BR = Font(name=TNR, size=10, bold=True)                      # section number
F11BLU= Font(name=TNR, size=11, bold=True, color="FF0070C0")    # supporting hdrs
F9    = Font(name=TNR, size=9)
F9B   = Font(name=TNR, size=9, bold=True)
F9I   = Font(name=TNR, size=9, italic=True)
F9R   = Font(name=TNR, size=9, color="FFFF0000")
MONO  = Font(name="Courier New", size=8)

# ---- borders / fills / alignment -------------------------------------------
THIN = Side(style="thin", color="FF000000")
MED  = Side(style="medium", color="FF000000")
BOX  = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
L_WRAP = Alignment(horizontal="left", vertical="center", wrap_text=True)
C_WRAP = Alignment(horizontal="center", vertical="center", wrap_text=True)
LV     = Alignment(horizontal="left", vertical="center")
RV     = Alignment(horizontal="right", vertical="center")
# Conditional-format (DXF) fills: Excel paints a DXF solid fill with bgColor, so set both
# colours - with fgColor alone the fill is dropped and white UNSAFE text becomes invisible.
GREEN  = PatternFill("solid", fgColor="FFC6EFCE", bgColor="FFC6EFCE")
RED    = PatternFill("solid", fgColor="FFFF0000", bgColor="FFFF0000")
AMBER  = PatternFill("solid", fgColor="FFFFEB9C", bgColor="FFFFEB9C")

# Column widths taken from the reference template. Keep these exact.
WIDTHS = {"A":12.71,"B":14.57,"C":14.57,"D":16.0,"E":12.29,"F":12.14,"G":13.71,
          "H":8.86,"I":9.14,"J":9.43,"K":9.14,"L":11.57,"M":10.0,"N":9.14,
          "O":9.14,"P":9.14,"Q":9.14,"R":10.0,"S":10.0,"T":10.0,"U":10.0,
          "V":10.0,"W":10.0,"X":10.0}

BODY_START = 9          # first row below the title block


class EDRCSheet:
    def __init__(self, title, sheet_name="Calc",
                 project="MUMBAI - AHMEDABAD HIGH SPEED RAIL PROJECT (Package No. MAHSR - C-3)",
                 doc_no="O23062-Q-VIA-CM-DC- 21460",
                 format_no="EDRC-GN-ST-06-2-R0",
                 designed="", checked="", logo=None, wb=None):
        if wb is None:
            self.wb = Workbook()
            self.ws = self.wb.active
        else:  # add this calculation as another sheet of an existing workbook
            self.wb = wb
            self.ws = wb.create_sheet()
        self.ws.title = sheet_name[:31]
        self.ws.sheet_view.showGridLines = False
        for col, w in WIDTHS.items():
            self.ws.column_dimensions[col].width = w
        self.cursor = BODY_START
        self._title_block(title, project, doc_no, format_no, designed, checked, logo)

    # ------------------------------------------------------------ primitives
    def put(self, ref, val, font=F11, align=None, fmt=None, fill=None, text=False):
        c = self.ws[ref]
        c.value = val
        c.font = font
        if align: c.alignment = align
        if fmt:   c.number_format = fmt
        if fill:  c.fill = fill
        if text:  c.data_type = "s"     # keep a leading "=" as literal text
        return c

    def bonly(self, ref):
        """Apply the table border without touching the value (merged-cell safe)."""
        self.ws[ref].border = BOX

    # ----------------------------------------------------------- title block
    def _title_block(self, title, project, doc_no, format_no, designed, checked, logo):
        ws = self.ws
        ws.row_dimensions[1].height = 7.5
        for r, h in {2:20.25, 3:15.75, 4:14.1, 5:13.5, 6:13.5, 7:13.5, 8:16.5}.items():
            ws.row_dimensions[r].height = h
        for rng in ["B2:G3","F4:G4","A5:A6","B5:D6","E5:F5","E6:F6","A7:A8","B7:D8"]:
            ws.merge_cells(rng)
        self.put("B2", "L&T CONSTRUCTION \nHEAVY CIVIL INFRASTRUCTURE - EDRC", F10B, L_WRAP)
        self.put("E4", "FORMAT NO", F10, C_WRAP)
        self.put("F4", format_no, F10, C_WRAP)
        self.put("A5", "PROJECT:", F10, C_WRAP)
        self.put("B5", project, F10, L_WRAP)
        self.put("E5", "DOCUMENT NO:", F10, C_WRAP)
        self.put("G5", "DATE", F10, C_WRAP)
        self.put("E6", doc_no, F10, C_WRAP)
        self.put("G6", "=TODAY()", F10, C_WRAP, "dd-mm-yy")
        self.put("A7", "TITLE:", F10, C_WRAP)
        self.put("B7", title, F10, L_WRAP)
        self.put("E7", "DESIGNED", F10, C_WRAP)
        self.put("F7", "CHECKED", F10, C_WRAP)
        self.put("G7", "SHEET", F10, C_WRAP)
        self.put("E8", designed, F10, C_WRAP)
        self.put("F8", checked, F10, C_WRAP)
        self.put("G8", "", F10, C_WRAP)

        ws["A2"].border = Border(left=THIN, right=THIN, top=THIN)
        ws["B2"].border = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
        ws["G2"].border = Border(right=THIN, top=THIN)
        ws["A3"].border = Border(left=THIN, right=THIN)
        ws["G3"].border = Border(right=THIN)
        ws["A4"].border = Border(left=THIN, right=THIN, bottom=THIN)
        ws["B4"].border = Border(left=THIN, bottom=THIN)
        for col in "CD":
            ws[f"{col}4"].border = Border(bottom=THIN)
        ws["E4"].border = Border(left=THIN, bottom=THIN)
        ws["F4"].border = Border(right=THIN, bottom=THIN)
        ws["G4"].border = Border(left=THIN, right=THIN, bottom=THIN)
        for r in (5, 7):
            for col in "ABEFG":
                ws[f"{col}{r}"].border = Border(left=THIN, right=THIN, top=THIN,
                                                bottom=THIN if col in "EFG" else None)
        for r in (6, 8):
            for col in "ABEFG":
                ws[f"{col}{r}"].border = Border(left=THIN, right=THIN, bottom=THIN)

        if logo and os.path.exists(logo):
            img = XLImage(logo)
            img.width, img.height = 78, 45
            ws.add_image(img, "A2")

    # -------------------------------------------------------------- body rows
    def row(self, ref=None, desc=None, work=None, workcol="D", val=None,
            unit=None, fmt=None, inp=False, key=False, bold_desc=False,
            height=24, secnum=None, descfont=None, valfont=None, no_eq=False):
        """Emit one body row in template format and return its row number.

        A row carries EITHER a working string (which begins with "=") in C/D
        OR an "=" in column E - never both; that is how the reference reads.
        A long description beside a working string is pushed onto its own row,
        exactly as the reference does.
        """
        ws = self.ws
        if desc is not None and work is not None and len(str(desc)) > 28:
            self.row(ref=ref, desc=desc, bold_desc=bold_desc, height=height,
                     secnum=secnum, descfont=descfont)
            ref = desc = secnum = None

        r = self.cursor
        ws.row_dimensions[r].height = height

        if secnum is not None:
            self.put(f"A{r}", secnum, F10BR, RV)
        elif ref is not None:
            self.put(f"A{r}", ref, F8BI, C_WRAP)

        if desc is not None:
            d = str(desc)
            long_text = len(d) > 52 and not d.startswith("=")
            if long_text and val is None and work is None:
                ws.merge_cells(f"B{r}:E{r}")          # never merge over F/G:
                self.put(f"B{r}", desc, descfont or (F11B if bold_desc else F11), L_WRAP)
                fsz = (descfont or F11).size or 11
                cpl = 56 if fsz >= 11 else 68
                lines = max(1, -(-len(d) // cpl) + d.count("\n"))
                ws.row_dimensions[r].height = max(height, 13.5 * lines + 7)
            elif long_text:
                ws.merge_cells(f"B{r}:D{r}")
                self.put(f"B{r}", desc, descfont or (F11B if bold_desc else F11), L_WRAP)
                ws.row_dimensions[r].height = max(height, 13.5 * max(1, -(-len(d)//42)) + 7)
            else:
                self.put(f"B{r}", desc, descfont or (F11B if bold_desc else F11), LV)

        if work is not None:
            self.put(f"{workcol}{r}", work, F11, LV)
        elif val is not None and not no_eq:
            self.put(f"E{r}", "=", F11, RV, text=True)

        if val is not None:
            f = valfont or (F11RB if (inp and key) else F11R if inp
                            else F11BB if key else F11)
            self.put(f"F{r}", val, f, RV, fmt or "0.00")
        if unit is not None:
            self.put(f"G{r}", unit, F11, LV)

        self.cursor = r + 1
        return r

    def head(self, num, text, height=24):
        """Numbered section heading, e.g. head('1.1', 'Design Data')."""
        return self.row(secnum=num, desc=text, bold_desc=True, height=height)

    def section(self, num, text, size=12):
        return self.row(secnum=num, desc=text,
                        descfont=Font(name=TNR, size=size, bold=True))

    def status(self, formula, height=24):
        """Bare SAFE/UNSAFE verdict row: value in F, nothing else, no "=".

        The reference puts the verdict alone on its own row (e.g. F73), so it
        reads as a conclusion rather than another quantity.
        """
        r = self.row(val=formula, fmt="General", no_eq=True, height=height)
        self.ws[f"F{r}"].font = F11BB
        self.ws[f"F{r}"].alignment = C_WRAP
        return r

    def note(self, text, height=None):
        """Small italic note line."""
        return self.row(desc=text, descfont=F9I, height=height or 20)

    def blank(self, n=1, height=12):
        for _ in range(n):
            self.ws.row_dimensions[self.cursor].height = height
            self.cursor += 1

    # ------------------------------------------------ supporting calculations
    def support_header(self, r, text, c1="I", c2="R"):
        """Blue banner across the supporting-calculation area."""
        self.ws.merge_cells(f"{c1}{r}:{c2}{r}")
        self.put(f"{c1}{r}", text, F11BLU, C_WRAP)
        i1, i2 = column_index_from_string(c1), column_index_from_string(c2)
        for col in range(i1, i2 + 1):
            c = self.ws.cell(row=r, column=col)
            c.border = Border(left=MED if col == i1 else THIN,
                              right=MED if col == i2 else THIN,
                              top=MED, bottom=MED)

    def support_cols(self, r, cols, labels):
        """Column headers for a supporting table."""
        for col, lab in zip(cols, labels):
            c = self.put(f"{col}{r}", lab, F11BLU, C_WRAP)
            c.border = Border(left=THIN, right=THIN, top=MED, bottom=MED)

    def cell(self, ref, val=None, font=F9, align=None, fmt=None, fill=None, text=False):
        """Bordered supporting-table cell."""
        c = self.put(ref, val, font, align or C_WRAP, fmt, fill, text=text)
        c.border = BOX
        return c

    # ------------------------------------------------------------- behaviours
    def dropdown(self, target, source, error="Select a listed value."):
        dv = DataValidation(type="list", formula1=source, allow_blank=False,
                            showErrorMessage=True, error=error)
        self.ws.add_data_validation(dv)
        dv.add(target)
        return dv

    def positive(self, targets, strict=True, error="Value must be positive."):
        dv = DataValidation(type="decimal",
                            operator="greaterThan" if strict else "greaterThanOrEqual",
                            formula1="0", showErrorMessage=True, error=error)
        self.ws.add_data_validation(dv)
        for t in targets:
            dv.add(t)
        return dv

    def status_format(self, ranges):
        """Green / red / amber status wording, in the template's SAFE-UNSAFE idiom."""
        for rng in ranges:
            first = rng.split(":")[0]
            self.ws.conditional_formatting.add(rng, FormulaRule(
                formula=[f'OR(TRIM({first})="UNSAFE",TRIM({first})="FAIL",'
                         f'TRIM({first})="MISMATCH",TRIM({first})="ERROR",TRIM({first})="CHECK")'],
                fill=RED, font=Font(color="FFFFFFFF", bold=True)))
            self.ws.conditional_formatting.add(rng, FormulaRule(
                formula=[f'OR(TRIM({first})="SAFE",TRIM({first})="PASS",'
                         f'TRIM({first})="OK",TRIM({first})="VERIFIED")'],
                fill=GREEN, font=Font(color="FF006100", bold=True)))
            self.ws.conditional_formatting.add(rng, FormulaRule(
                formula=[f'LEFT(TRIM({first}),4)="NOTE"'],
                fill=AMBER, font=Font(color="FF9C5700", bold=True)))

    # ----------------------------------------------------------------- finish
    def finish(self, path, body_end=None):
        """Draw the frame rules, set print setup as the reference, save."""
        ws = self.ws
        end = body_end or (self.cursor - 1)
        for r in range(BODY_START, end + 1):
            for col, side in (("A", "l"), ("B", "l"), ("F", "r"), ("G", "r")):
                ws[f"{col}{r}"].border = Border(
                    left=THIN if side == "l" else None,
                    right=THIN if side == "r" else None)
        ws.print_area = f"A1:G{end}"
        ws.print_title_rows = "$1:$8"
        ws.page_setup.orientation = "portrait"
        ws.page_setup.paperSize = 9                 # A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_margins.left = 0.236220472440945
        ws.page_margins.right = 0.0
        ws.page_margins.top = 0.196850393700787
        ws.page_margins.bottom = 0.511811023622047
        ws.page_margins.header = 0.2
        ws.page_margins.footer = 0.236220472440945
        ws.freeze_panes = f"A{BODY_START}"
        if path:
            self.wb.save(path)
        return end

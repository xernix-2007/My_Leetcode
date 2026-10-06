from pathlib import Path
from html import unescape
import re
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    Preformatted,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "LeetCode_Notes_Simple.pdf"

LANGUAGES = {
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".c": "C",
    ".py": "Python", ".java": "Java", ".js": "JavaScript", ".ts": "TypeScript",
    ".go": "Go", ".rs": "Rust", ".cs": "C#", ".kt": "Kotlin",
    ".swift": "Swift", ".php": "PHP", ".rb": "Ruby",
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("LC_Sans", f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("LC_Bold", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("LC_Mono", f"{FONT_DIR}/DejaVuSansMono.ttf"))

INK = colors.HexColor("#20242B")
MUTED = colors.HexColor("#68707A")
ACCENT = colors.HexColor("#5B258C")
ACCENT_SOFT = colors.HexColor("#F4EFF8")
LINE = colors.HexColor("#D7DCE2")
CODE_BG = colors.HexColor("#F8F9FA")
WHITE = colors.white

PAGE_W, PAGE_H = A4
LEFT = 18 * mm
RIGHT = 18 * mm
TOP = 16 * mm
BOTTOM = 17 * mm
CONTENT_W = PAGE_W - LEFT - RIGHT

def style(name, font="LC_Sans", size=10, leading=None, color=INK):
    return ParagraphStyle(
        name,
        fontName=font,
        fontSize=size,
        leading=leading or size * 1.4,
        textColor=color,
        spaceAfter=0,
    )

TITLE = style("lc_title", "LC_Bold", 22, 26)
META = style("lc_meta", size=9.2, leading=12, color=MUTED)
SECTION = style("lc_section", "LC_Bold", 10.5, 13, ACCENT)
BODY = style("lc_body", size=10.5, leading=15)
BODY_BOLD = style("lc_body_bold", "LC_Bold", 10.5, 15)
EXAMPLE = style("lc_example", "LC_Mono", 9.2, 13)
CODE = style("lc_code", "LC_Mono", 10.3, 14, INK)

def clean_html(text):
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(p|li|pre|h[1-6])>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def clean_inline(text):
    return clean_html(text).replace("\n", " ").strip()

def extract_paragraphs(raw):
    result = []
    for item in re.findall(r"<p>(.*?)</p>", raw, re.I | re.S):
        value = clean_inline(item)
        if value:
            result.append(value)
    return result

def extract_examples(raw):
    result = []
    for item in re.findall(r"<pre>(.*?)</pre>", raw, re.I | re.S):
        value = clean_html(item)
        if value:
            result.append(value)
    return result

def extract_constraints(raw):
    match = re.search(
        r"<p>\s*<strong>Constraints:</strong>\s*</p>\s*(<ul>.*?</ul>)",
        raw, re.I | re.S
    )
    if not match:
        return []
    return [
        clean_inline(x)
        for x in re.findall(r"<li>(.*?)</li>", match.group(1), re.I | re.S)
        if clean_inline(x)
    ]

def extract_follow_up(raw):
    match = re.search(
        r"<strong>Follow-up:\s*</strong>(.*?)(?:<font|$)",
        raw, re.I | re.S
    )
    return clean_inline(match.group(1)) if match else ""

def read_readme(path):
    raw = path.read_text(encoding="utf-8", errors="ignore")

    h2 = (
        re.search(r"<h2>.*?>(.*?)</a></h2>", raw, re.I | re.S)
        or re.search(r"<h2>(.*?)</h2>", raw, re.I | re.S)
    )
    title = clean_inline(h2.group(1)) if h2 else path.parent.name

    h3 = re.search(r"<h3>(.*?)</h3>", raw, re.I | re.S)
    difficulty = clean_inline(h3.group(1)) if h3 else ""

    paragraphs = extract_paragraphs(raw)
    question = [
        x for x in paragraphs
        if not x.lower().startswith(("example", "constraints", "follow-up"))
    ]

    return {
        "title": title,
        "difficulty": difficulty,
        "question": question,
        "examples": extract_examples(raw),
        "constraints": extract_constraints(raw),
        "follow_up": extract_follow_up(raw),
    }

def find_solution(folder):
    files = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in LANGUAGES
    ]
    if not files:
        return None
    named = [p for p in files if p.stem.lower() == "solution"]
    return sorted(named or files, key=lambda p: p.name.lower())[0]

def complexity(code):
    compact = re.sub(r"\s+", "", code)
    if "sort(" in compact or ".sort(" in compact:
        return "O(n log n)", "O(n)"
    if "lower_bound" in compact or "upper_bound" in compact:
        return "O(log n)", "O(1)"
    if "unordered_map" in compact or "unordered_set" in compact:
        return "O(n) average", "O(n)"
    if len(re.findall(r"for\s*\(", code)) >= 2:
        return "O(n²)", "O(1)"
    return "O(n)", "O(1)"

def gather():
    problems = []

    for folder in sorted(ROOT.iterdir(), key=lambda p: p.name.lower()):
        if not folder.is_dir() or not re.match(r"^\d{4}-", folder.name):
            continue

        readme = folder / "README.md"
        solution = find_solution(folder)
        if not readme.exists() or solution is None:
            continue

        data = read_readme(readme)
        code = (
            solution.read_text(encoding="utf-8", errors="ignore")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .rstrip()
        )

        number_match = re.match(r"^(\d+)-", folder.name)
        number = number_match.group(1) if number_match else folder.name
        time, space = complexity(code)

        problems.append({
            "number": number,
            "title": data["title"],
            "difficulty": data["difficulty"],
            "question": data["question"],
            "examples": data["examples"],
            "constraints": data["constraints"],
            "follow_up": data["follow_up"],
            "code": code,
            "language": LANGUAGES[solution.suffix.lower()],
            "time": time,
            "space": space,
        })

    return sorted(
        problems,
        key=lambda p: int(p["number"]) if p["number"].isdigit() else 999999,
    )

def section_heading(text):
    return [Paragraph(text, SECTION), Spacer(1, 2.2 * mm)]

def example_box(example, label, index):
    return [
        Paragraph(label, BODY_BOLD),
        Spacer(1, 1.2 * mm),
        Table(
            [[Preformatted(example, EXAMPLE)]],
            colWidths=[CONTENT_W],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]),
        ),
        Spacer(1, 3.5 * mm),
    ]

def code_block(code, index):
    # Deliberately large. Never shrink the font just to squeeze a long solution
    # into one page. ReportLab will naturally flow the block onto another page.
    lines = code.splitlines() or [""]
    numbered = "\n".join(f"{n:>2}  {line}" for n, line in enumerate(lines, start=1))

    # Wrap only unusually long source lines. The font stays large and the
    # original line remains readable instead of shrinking the whole solution.
    return Table(
        [[Preformatted(numbered, CODE, maxLineLength=86)]],
        colWidths=[CONTENT_W],
        splitByRow=1,
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
            ("BOX", (0, 0), (-1, -1), 0.6, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]),
    )

def footer(canvas, doc):
    canvas.saveState()
    y = 11.5 * mm
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(LEFT, y + 3.8 * mm, PAGE_W - RIGHT, y + 3.8 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("LC_Sans", 7.2)
    canvas.drawString(LEFT, y, "My LeetCode Notes")
    canvas.drawRightString(PAGE_W - RIGHT, y, str(doc.page))
    canvas.restoreState()

def first_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(ACCENT_SOFT)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 46 * mm, PAGE_W, 46 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("LC_Bold", 11)
    canvas.drawString(LEFT, PAGE_H - 15 * mm, "XERNIX")
    canvas.setFont("LC_Bold", 26)
    canvas.drawString(LEFT, PAGE_H - 30 * mm, "LeetCode Revision Notes")
    canvas.setFont("LC_Sans", 9.5)
    canvas.drawString(
        LEFT,
        PAGE_H - 38 * mm,
        "Simple layout • complete statements • readable code"
    )
    canvas.restoreState()
    footer(canvas, doc)

def later_page(canvas, doc):
    footer(canvas, doc)

def build():
    problems = gather()

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=LEFT,
        rightMargin=RIGHT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="My LeetCode Notes - Simple",
        author="xernix-2007",
        allowSplitting=1,
    )

    story = [
        Spacer(1, 53 * mm),
        Paragraph(
            f"{len(problems)} problems",
            style("cover_count", "LC_Bold", 18, 22, ACCENT),
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            "Made for revision: read the whole problem, inspect every example, "
            "check the constraints and complexity, then reproduce the solution.",
            style("cover_body", size=10.5, leading=15),
        ),
        Spacer(1, 10 * mm),
        Table(
            [[Paragraph(
                "Clean typography • comfortable spacing • large code",
                style("cover_tag", "LC_Bold", 9, 12, ACCENT)
            )]],
            colWidths=[CONTENT_W],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]),
        ),
        PageBreak(),
    ]

    for index, p in enumerate(problems):
        story += [
            Paragraph(
                f"{xml_escape(p['number'])}. {xml_escape(p['title'])}",
                TITLE
            ),
            Spacer(1, 2.2 * mm),
            Paragraph(
                f"<b>{xml_escape(p['difficulty'] or 'Unknown')}</b>"
                f"   •   {xml_escape(p['language'])}",
                META
            ),
            Spacer(1, 7.5 * mm),
        ]

        story += section_heading("QUESTION")
        if p["question"]:
            for paragraph in p["question"]:
                story += [
                    Paragraph(xml_escape(paragraph), BODY),
                    Spacer(1, 3.2 * mm),
                ]
        else:
            story += [Paragraph(
                "Problem statement not found in this README.",
                BODY
            )]

        if p["examples"]:
            story += section_heading("EXAMPLES")
            for n, example in enumerate(p["examples"], start=1):
                story += example_box(example, f"Example {n}", index)

        if p["constraints"]:
            story += section_heading("CONSTRAINTS")
            for constraint in p["constraints"]:
                story += [
                    Paragraph("• " + xml_escape(constraint), BODY),
                    Spacer(1, 1.4 * mm),
                ]

        if p["follow_up"]:
            story += section_heading("FOLLOW-UP")
            story += [
                Paragraph(xml_escape(p["follow_up"]), BODY),
                Spacer(1, 4 * mm),
            ]

        story += section_heading("COMPLEXITY")
        story += [
            Paragraph(
                f"<b>Time:</b> {xml_escape(p['time'])}"
                f"    <b>Space:</b> {xml_escape(p['space'])}",
                BODY,
            ),
            Spacer(1, 5 * mm),
        ]

        story += section_heading("SOLUTION")
        story += [code_block(p["code"], index)]

        if index != len(problems) - 1:
            story.append(PageBreak())

    doc.build(story, onFirstPage=first_page, onLaterPages=later_page)
    print(f"Generated {OUTPUT} with {len(problems)} problems.")

if __name__ == "__main__":
    build()

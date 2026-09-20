from pathlib import Path
from html import unescape
import re
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
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
pdfmetrics.registerFont(TTFont("SimpleSans", f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("SimpleBold", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("SimpleMono", f"{FONT_DIR}/DejaVuSansMono.ttf"))

BLACK = colors.HexColor("#20252D")
GRAY = colors.HexColor("#69717D")
ACCENT = colors.HexColor("#5B258C")
LINE = colors.HexColor("#D9DDE3")
CODE_BG = colors.HexColor("#F7F8FA")
PAGE_W, PAGE_H = A4

def style(name, font="SimpleSans", size=9, leading=None, color=BLACK):
    return ParagraphStyle(
        name, fontName=font, fontSize=size,
        leading=leading or size * 1.35, textColor=color
    )

TITLE = style("simple_title", "SimpleBold", 21, 25)
SECTION = style("simple_section", "SimpleBold", 8.5, 10, ACCENT)
BODY = style("simple_body", size=9, leading=12)
META = style("simple_meta", size=7.5, leading=9, color=GRAY)

def clean(text):
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>|</li>|</pre>|</h[1-6]>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    return re.sub(r"[ \t]+", " ", text).strip()

def read_readme(path):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    h2 = (
        re.search(r"<h2>.*?>(.*?)</a></h2>", raw, re.I | re.S)
        or re.search(r"<h2>(.*?)</h2>", raw, re.I | re.S)
    )
    title = clean(h2.group(1)) if h2 else path.parent.name

    h3 = re.search(r"<h3>(.*?)</h3>", raw, re.I | re.S)
    difficulty = clean(h3.group(1)) if h3 else ""

    paragraphs = [
        clean(x) for x in re.findall(r"<p>(.*?)</p>", raw, re.I | re.S)
    ]
    paragraphs = [x for x in paragraphs if x]
    question = next(
        (x for x in paragraphs
         if not x.lower().startswith(("example", "constraints", "follow-up"))),
        ""
    )

    examples = [
        clean(x) for x in re.findall(r"<pre>(.*?)</pre>", raw, re.I | re.S)
    ]
    return title, difficulty, question, next(iter(examples), "")

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

        title, difficulty, question, example = read_readme(readme)
        code = (
            solution.read_text(encoding="utf-8", errors="ignore")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .strip()
        )

        time, space = complexity(code)
        number_match = re.match(r"^(\d+)-", folder.name)
        number = number_match.group(1) if number_match else folder.name

        problems.append({
            "number": number,
            "title": title,
            "difficulty": difficulty,
            "question": question,
            "example": example,
            "code": code,
            "language": LANGUAGES[solution.suffix.lower()],
            "time": time,
            "space": space,
        })

    return sorted(
        problems,
        key=lambda p: int(p["number"]) if p["number"].isdigit() else 999999
    )

def code_lines(code, index):
    lines = code.splitlines() or [""]
    # Keep code comfortably readable. Long lines wrap instead of
    # shrinking the whole solution down to tiny text.
    font_size = 8.6
    leading = 12.4
    code_style = style(
        f"simple_code_{index}",
        "SimpleMono",
        font_size,
        leading,
        BLACK
    )
    code_style.wordWrap = "CJK"

    # Each source line is a separate Paragraph, with a small visual gap
    # between lines so the solution reads like normal source code.
    result = []
    for line in lines:
        result.append(Paragraph(xml_escape(line) if line else " ", code_style))
        result.append(Spacer(1, 1.2))
    return result

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 12 * mm, PAGE_W - 18 * mm, 12 * mm)
    canvas.setFillColor(GRAY)
    canvas.setFont("SimpleSans", 7)
    canvas.drawString(18 * mm, 7 * mm, "My LeetCode Notes — Simple")
    canvas.drawRightString(PAGE_W - 18 * mm, 7 * mm, str(doc.page))
    canvas.restoreState()

def build():
    problems = gather()

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=17 * mm,
        title="My LeetCode Notes - Simple",
        author="xernix-2007",
    )

    story = [
        Spacer(1, 65 * mm),
        Paragraph(
            "MY LEETCODE",
            style("cover_a", "SimpleBold", 12, 14, ACCENT),
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "INTERVIEW NOTES",
            style("cover_b", "SimpleBold", 27, 31),
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            f"{len(problems)} problems  |  Questions  |  Examples  |  Complexity  |  Solutions",
            style("cover_c", size=9.5, leading=12, color=GRAY),
        ),
        Spacer(1, 82 * mm),
        Paragraph(
            "Focused notes for fast revision.",
            style("cover_d", size=9, color=GRAY),
        ),
        PageBreak(),
    ]

    for i, p in enumerate(problems):
        story.extend([
            Paragraph(f"{p['number']}. {p['title']}", TITLE),
            Spacer(1, 2 * mm),
            Paragraph(
                f"<b>Difficulty:</b> {xml_escape(p['difficulty'] or 'Unknown')}    "
                f"<b>Language:</b> {xml_escape(p['language'])}",
                META,
            ),
            Spacer(1, 8 * mm),

            Paragraph("QUESTION", SECTION),
            Spacer(1, 1.5 * mm),
            Paragraph(
                xml_escape(p["question"] or "See the original problem statement."),
                BODY,
            ),
            Spacer(1, 7 * mm),

            Paragraph("EXAMPLE", SECTION),
            Spacer(1, 1.5 * mm),
            Paragraph(
                xml_escape(p["example"] or "No example extracted from the README."),
                style(f"example_{i}", "SimpleMono", 7.6, 10),
            ),
            Spacer(1, 7 * mm),

            Paragraph("COMPLEXITY", SECTION),
            Spacer(1, 1.5 * mm),
            Paragraph(
                f"<b>Time:</b> {xml_escape(p['time'])}    "
                f"<b>Space:</b> {xml_escape(p['space'])}",
                BODY,
            ),
            Spacer(1, 7 * mm),

            Paragraph("SOLUTION", SECTION),
            Spacer(1, 2 * mm),

            # Plain code: no dark UI, no syntax decoration, no card.
            *code_lines(p["code"], i),
        ])

        if i != len(problems) - 1:
            story.append(PageBreak())

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Generated {OUTPUT} with {len(problems)} problems.")

if __name__ == "__main__":
    build()

from pathlib import Path
from html import unescape, escape
from pygments import lex
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.token import Token
from xml.sax.saxutils import escape as xml_escape
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted, XPreformatted,
    Table, TableStyle, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "LeetCode_Notes.pdf"

LANGUAGES = {
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++",
    ".c": "C", ".py": "Python", ".java": "Java",
    ".js": "JavaScript", ".ts": "TypeScript", ".go": "Go",
    ".rs": "Rust", ".cs": "C#", ".kt": "Kotlin",
    ".swift": "Swift", ".php": "PHP", ".rb": "Ruby",
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DejaVu", f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuMono", f"{FONT_DIR}/DejaVuSansMono.ttf"))

PAGE_W, PAGE_H = A4
MARGIN_X = 15 * mm
TOP = 14 * mm
BOTTOM = 15 * mm

NAVY = colors.HexColor("#132238")
BLUE = colors.HexColor("#1976D2")
BLUE_DARK = colors.HexColor("#0D47A1")
BLUE_LIGHT = colors.HexColor("#EAF3FF")
BLUE_PALE = colors.HexColor("#F6FAFF")
TEXT = colors.HexColor("#263238")
MUTED = colors.HexColor("#6B7785")
BORDER = colors.HexColor("#D9E2EC")
SOFT = colors.HexColor("#F4F6F8")
CODE_BG = colors.HexColor("#111827")
WHITE = colors.white
MAGENTA = colors.HexColor("#D72C86")
PURPLE = colors.HexColor("#7026A8")
PURPLE_DARK = colors.HexColor("#4B177C")
CYAN = colors.HexColor("#27C2D1")
EASY = colors.HexColor("#14804A")
MEDIUM = colors.HexColor("#B26A00")
HARD = colors.HexColor("#C0392B")

styles = getSampleStyleSheet()

cover_title = ParagraphStyle(
    "CoverTitle", fontName="DejaVu-Bold", fontSize=31, leading=36,
    alignment=TA_LEFT, textColor=NAVY, spaceAfter=5
)
cover_sub = ParagraphStyle(
    "CoverSub", fontName="DejaVu", fontSize=12, leading=17,
    alignment=TA_LEFT, textColor=MUTED
)
eyebrow = ParagraphStyle(
    "Eyebrow", fontName="DejaVu-Bold", fontSize=8.5, leading=10,
    textColor=PURPLE, spaceAfter=4
)
problem_title = ParagraphStyle(
    "ProblemTitle", fontName="DejaVu-Bold", fontSize=22, leading=26,
    textColor=PURPLE_DARK, spaceAfter=7
)
section = ParagraphStyle(
    "Section", fontName="DejaVu-Bold", fontSize=10.2, leading=12.5,
    textColor=NAVY, spaceBefore=4, spaceAfter=4
)
body = ParagraphStyle(
    "Body", fontName="DejaVu", fontSize=10.2, leading=14.2,
    textColor=TEXT, spaceAfter=2
)
small = ParagraphStyle(
    "Small", fontName="DejaVu", fontSize=8.6, leading=11,
    textColor=MUTED
)
tiny = ParagraphStyle(
    "Tiny", fontName="DejaVu", fontSize=7.6, leading=9.5,
    textColor=MUTED
)
card_text = ParagraphStyle(
    "CardText", fontName="DejaVu", fontSize=9.8, leading=13.5,
    textColor=TEXT
)
card_label = ParagraphStyle(
    "CardLabel", fontName="DejaVu-Bold", fontSize=7.6, leading=9,
    textColor=MUTED
)
index_title = ParagraphStyle(
    "IndexTitle", fontName="DejaVu-Bold", fontSize=22, leading=26,
    textColor=PURPLE_DARK, spaceAfter=3
)
index_cell = ParagraphStyle(
    "IndexCell", fontName="DejaVu", fontSize=8.4, leading=10.5,
    textColor=TEXT
)
index_cell_bold = ParagraphStyle(
    "IndexCellBold", fontName="DejaVu-Bold", fontSize=8.4, leading=10.5,
    textColor=NAVY
)
code_label = ParagraphStyle(
    "CodeLabel", fontName="DejaVu-Bold", fontSize=8.3, leading=10,
    textColor=WHITE
)
code_text = ParagraphStyle(
    "CodeText", fontName="DejaVuMono", fontSize=7.65, leading=8.9,
    textColor=colors.HexColor("#E5E7EB")
)
tip_text = ParagraphStyle(
    "TipText", fontName="DejaVu", fontSize=8.4, leading=11.5,
    textColor=TEXT
)


def strip_html(text):
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>|</li>|</pre>|</h[1-6]>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def read_readme(path):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    h2 = re.search(r"<h2>.*?>(.*?)</a></h2>", raw, re.I | re.S)
    if not h2:
        h2 = re.search(r"<h2>(.*?)</h2>", raw, re.I | re.S)
    title = strip_html(h2.group(1)) if h2 else path.parent.name

    diff = re.search(r"<h3>(.*?)</h3>", raw, re.I | re.S)
    difficulty = strip_html(diff.group(1)) if diff else ""

    paragraphs = re.findall(r"<p>(.*?)</p>", raw, re.I | re.S)
    question = ""
    for p in paragraphs:
        candidate = strip_html(p)
        if candidate and not candidate.lower().startswith(
            ("example", "constraints", "follow-up")
        ):
            question = candidate
            break

    examples = []
    for pre in re.findall(r"<pre>(.*?)</pre>", raw, re.I | re.S):
        candidate = strip_html(pre)
        if candidate:
            examples.append(candidate)
        if len(examples) == 1:
            break

    return title, difficulty, question, examples[0] if examples else ""


def infer_pattern(title, question, code):
    text = f"{title} {question} {code}".lower()
    rules = [
        (r"binary|mid\s*=|lower_bound|upper_bound", "Binary Search"),
        (r"unordered_map|unordered_set|set<|map<", "Hashing / Set"),
        (r"left.*right|two pointer|while.*left.*right", "Two Pointers"),
        (r"window|sliding|substring", "Sliding Window"),
        (r"listnode|linked list", "Linked List"),
        (r"tree|treenode|inorder|preorder|postorder", "Binary Tree / Recursion"),
        (r"sort\(|sorting", "Sorting"),
        (r"dp|dynamic programming|memo", "Dynamic Programming"),
        (r"maxprofit|maximum subarray|kadane", "Greedy / Kadane"),
        (r"reverse|palindrome|digit", "Math / Simulation"),
    ]
    for pattern, label in rules:
        if re.search(pattern, text):
            return label
    return "Arrays / Implementation"


def complexity(code):
    c = code.replace(" ", "")
    if "sort(" in c or ".sort(" in c:
        return "O(n log n)", "O(n) / O(1)"
    if "unordered_set" in c or "unordered_map" in c or "set<" in c:
        return "O(n) average", "O(n)"
    if len(re.findall(r"for\s*\([^)]*\).*\{", c, re.S)) >= 2:
        return "O(n²)", "O(1)"
    if "while" in c and "left" in c and "right" in c:
        return "O(n)", "O(1)"
    return "O(n)", "O(1)"


def clean_code(code):
    return code.replace("\r\n", "\n").replace("\r", "\n").strip()


def find_solution_file(folder):
    candidates = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in LANGUAGES
    ]
    if not candidates:
        return None

    exact = [p for p in candidates if p.stem.lower() == folder.name.lower()]
    if exact:
        return sorted(exact)[0]

    solution_named = [p for p in candidates if p.stem.lower() == "solution"]
    if solution_named:
        return sorted(solution_named)[0]

    return sorted(candidates, key=lambda p: p.name.lower())[0]


def difficulty_color(value):
    v = value.lower()
    if "easy" in v:
        return EASY
    if "medium" in v:
        return MEDIUM
    if "hard" in v:
        return HARD
    return BLUE


def badge(label, bg, fg=WHITE, width=None):
    t = Table([[Paragraph(label, ParagraphStyle(
        "Badge", fontName="DejaVu-Bold", fontSize=7.4, leading=9,
        alignment=TA_CENTER, textColor=fg
    ))]], colWidths=[width] if width else None, rowHeights=[7.2 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0, bg),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def pill_row(p):
    diff = p["difficulty"] or "Unknown"
    items = [
        badge(diff, difficulty_color(diff)),
        badge(p["pattern"], PURPLE, width=41 * mm),
        badge(p["language"], NAVY, width=25 * mm),
    ]
    row = Table([items], hAlign="LEFT", colWidths=[32 * mm, 46 * mm, 29 * mm])
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return row


def card(content, bg=WHITE, border=BORDER, pad=8):
    t = Table([[content]], colWidths=[PAGE_W - 2 * MARGIN_X])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.7, border),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def stat_card(label, value):
    label_p = Paragraph(label.upper(), card_label)
    value_p = Paragraph(value, ParagraphStyle(
        "StatValue", parent=card_text, fontName="DejaVu-Bold",
        fontSize=18, leading=20, textColor=NAVY
    ))
    t = Table([[label_p], [value_p]], colWidths=[54 * mm], rowHeights=[7 * mm, 14 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_PALE),
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def syntax_highlight(code, lexer_name):
    try:
        lexer = get_lexer_by_name(lexer_name)
    except Exception:
        lexer = TextLexer()

    def color_for(token):
        if token in Token.Comment:
            return "#6A9955"       # VS Code comment green
        if token in Token.Keyword or token in Token.Keyword.Type:
            return "#C586C0"       # keyword purple
        if token in Token.Name.Class:
            return "#4EC9B0"       # class/type teal
        if token in Token.Name.Function or token in Token.Name.Function.Magic:
            return "#DCDCAA"       # function yellow
        if token in Token.Name.Builtin:
            return "#569CD6"       # builtin blue
        if token in Token.Literal.String:
            return "#CE9178"       # string orange
        if token in Token.Literal.Number:
            return "#B5CEA8"       # number green
        if token in Token.Operator:
            return "#D4D4D4"
        if token in Token.Punctuation:
            return "#D4D4D4"
        return "#D4D4D4"

    parts = []
    for token, value in lex(code, lexer):
        parts.append(
            f'<font color="{color_for(token)}">{xml_escape(value)}</font>'
        )
    return "".join(parts)


def code_block(p, fs=7.65, leading=8.9):
    header = Table(
        [[Paragraph(
            f'{escape(p["language"])}  •  LeetCode Solution  •  #{escape(p["number"])}',
            code_label
        )]],
        colWidths=[PAGE_W - 2 * MARGIN_X]
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PURPLE_DARK),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    lexer_names = {
        "C++": "cpp", "C": "c", "Python": "python", "Java": "java",
        "JavaScript": "javascript", "TypeScript": "typescript",
        "Go": "go", "Rust": "rust", "C#": "csharp", "Kotlin": "kotlin",
        "Swift": "swift", "PHP": "php", "Ruby": "ruby"
    }
    highlighted = syntax_highlight(
        p["code"], lexer_names.get(p["language"], "text")
    )

    source = XPreformatted(
        highlighted,
        ParagraphStyle(
            f'Code{p["number"]}', fontName="DejaVuMono",
            fontSize=fs, leading=leading,
            textColor=colors.HexColor("#D4D4D4")
        ),
        maxLineLength=105
    )

    body_t = Table([[source]], colWidths=[PAGE_W - 2 * MARGIN_X])
    body_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.7, CODE_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return [header, body_t]

def abstract_blob(canvas, x, y, w, h, top_color, bottom_color):
    """Draw layered organic shapes inspired by the supplied annual-report template."""
    canvas.saveState()

    canvas.setFillColor(bottom_color)
    p = canvas.beginPath()
    p.moveTo(x, y + h * 0.55)
    p.curveTo(
        x + w * 0.12, y + h * 0.98,
        x + w * 0.46, y + h * 0.90,
        x + w * 0.62, y + h * 0.68
    )
    p.curveTo(
        x + w * 0.76, y + h * 0.48,
        x + w * 0.92, y + h * 0.70,
        x + w, y + h * 0.40
    )
    p.lineTo(x + w, y)
    p.lineTo(x, y)
    p.close()
    canvas.drawPath(p, fill=1, stroke=0)

    canvas.setFillColor(top_color)
    p2 = canvas.beginPath()
    p2.moveTo(x, y + h * 0.78)
    p2.curveTo(
        x + w * 0.18, y + h * 1.04,
        x + w * 0.56, y + h * 0.76,
        x + w * 0.78, y + h * 0.86
    )
    p2.curveTo(
        x + w * 0.92, y + h * 0.92,
        x + w * 0.98, y + h * 0.60,
        x + w, y + h * 0.50
    )
    p2.lineTo(x + w, y + h)
    p2.lineTo(x, y + h)
    p2.close()
    canvas.drawPath(p2, fill=1, stroke=0)
    canvas.restoreState()


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PURPLE)
    canvas.rect(0, 0, PAGE_W, 7.5 * mm, fill=1, stroke=0)
    canvas.setFont("DejaVu-Bold", 7.5)
    canvas.setFillColor(WHITE)
    canvas.drawString(MARGIN_X, 2.7 * mm, "MY LEETCODE  •  REVISION HANDBOOK")
    canvas.drawRightString(PAGE_W - MARGIN_X, 2.7 * mm, f"{doc.page:02d}")
    canvas.restoreState()


def top_accent(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PURPLE_DARK)
    canvas.rect(0, PAGE_H - 2.5 * mm, PAGE_W, 2.5 * mm, fill=1, stroke=0)
    canvas.restoreState()


def cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(CYAN)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    canvas.setFillColor(WHITE)
    canvas.roundRect(
        8 * mm, 8 * mm, PAGE_W - 16 * mm, PAGE_H - 16 * mm,
        3 * mm, fill=1, stroke=0
    )

    # Large top/bottom artwork matching the visual language of the reference.
    abstract_blob(
        canvas, 8 * mm, PAGE_H - 87 * mm, PAGE_W - 16 * mm, 76 * mm,
        MAGENTA, PURPLE
    )
    abstract_blob(
        canvas, 8 * mm, 10 * mm, PAGE_W - 16 * mm, 48 * mm,
        PURPLE, MAGENTA
    )

    canvas.setFillColor(PURPLE_DARK)
    canvas.setFont("DejaVu-Bold", 7.5)
    canvas.drawString(18 * mm, PAGE_H - 22 * mm, "XERNIX  /  DSA")
    canvas.setFont("DejaVu", 6.7)
    canvas.drawString(18 * mm, PAGE_H - 27 * mm, "INTERVIEW REVISION HANDBOOK")

    canvas.setFont("DejaVu-Bold", 7.5)
    canvas.drawRightString(
        PAGE_W - 18 * mm, 16 * mm,
        "LEETCODE  •  PATTERNS  •  CODE"
    )
    canvas.restoreState()

    # Content is drawn by the normal story flow.
    footer(canvas, doc)


def cover_content():
    return


def cover_page(canvas, doc):
    top_accent(canvas, doc)
    footer(canvas, doc)


def indexed_problems(problems):
    return sorted(
        problems,
        key=lambda p: int(re.match(r"\d+", p["number"]).group())
        if re.match(r"\d+", p["number"]) else 10**9
    )


def number_from_folder(folder):
    m = re.match(r"^(\d+)-", folder.name)
    return m.group(1) if m else ""


def build():
    problems = []
    for folder in sorted(ROOT.iterdir(), key=lambda p: p.name):
        if not folder.is_dir() or not re.match(r"^\d{4}-", folder.name):
            continue

        readme = folder / "README.md"
        solution_file = find_solution_file(folder)
        if not readme.exists() or solution_file is None:
            continue

        title, difficulty, question, example = read_readme(readme)
        code = clean_code(
            solution_file.read_text(encoding="utf-8", errors="ignore")
        )
        language = LANGUAGES[solution_file.suffix.lower()]
        time_c, space_c = complexity(code)

        problems.append({
            "number": number_from_folder(folder),
            "title": title,
            "difficulty": difficulty,
            "question": question,
            "example": example,
            "code": code,
            "language": language,
            "pattern": infer_pattern(title, question, code),
            "time": time_c,
            "space": space_c,
        })

    problems = indexed_problems(problems)

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=MARGIN_X,
        leftMargin=MARGIN_X,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="My Leetcode Notes",
        author="xernix-2007",
        subject="Interview and DSA revision notes",
    )

    story = []

    # -------------------------
    # Cover
    # -------------------------
    story += [
        Spacer(1, 78 * mm),
        Paragraph("MY LEETCODE", eyebrow),
        Paragraph("Interview Revision", cover_title),
        Paragraph(
            "A visual DSA handbook for patterns, complexity, and LeetCode solutions — "
            "made to keep your revision focused.",
            cover_sub
        ),
        Spacer(1, 11 * mm),
    ]

    easy = sum("easy" in p["difficulty"].lower() for p in problems)
    medium = sum("medium" in p["difficulty"].lower() for p in problems)
    hard = sum("hard" in p["difficulty"].lower() for p in problems)

    stats = Table(
        [[stat_card("Solved", str(len(problems))),
          stat_card("Patterns", str(len(set(p["pattern"] for p in problems)))),
          stat_card("Languages", str(len(set(p["language"] for p in problems))))]],
        colWidths=[57 * mm, 57 * mm, 57 * mm]
    )
    stats.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(stats)
    story.append(Spacer(1, 10 * mm))

    story.append(Paragraph("Difficulty split", section))
    split = Table(
        [[badge("Easy", EASY, width=30 * mm),
          Paragraph(str(easy), index_cell_bold),
          badge("Medium", MEDIUM, width=30 * mm),
          Paragraph(str(medium), index_cell_bold),
          badge("Hard", HARD, width=30 * mm),
          Paragraph(str(hard), index_cell_bold)]],
        colWidths=[30 * mm, 15 * mm, 30 * mm, 15 * mm, 30 * mm, 15 * mm]
    )
    split.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(split)
    story.append(Spacer(1, 12 * mm))

    story.append(card(
        [
            Paragraph("HOW TO REVISE", eyebrow),
            Paragraph(
                "<b>1.</b> Read the title and question. "
                "<b>2.</b> Cover the code and recall the pattern. "
                "<b>3.</b> Check time and space complexity. "
                "<b>4.</b> Only then inspect the solution.",
                card_text
            ),
        ],
        bg=BLUE_PALE,
        border=colors.HexColor("#C8DDF7")
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        "The goal is recall, not rereading. Try to solve the idea in your head before the code.",
        small
    ))
    story.append(PageBreak())

    # -------------------------
    # Revision index
    # -------------------------
    story += [
        Paragraph("Revision Index", index_title),
        Paragraph(
            "Use this page to jump to a problem by number, pattern, or difficulty.",
            small
        ),
        Spacer(1, 5 * mm)
    ]

    rows = [[
        Paragraph("NO.", index_cell_bold),
        Paragraph("PROBLEM", index_cell_bold),
        Paragraph("PATTERN", index_cell_bold),
        Paragraph("LEVEL", index_cell_bold),
    ]]
    for p in problems:
        rows.append([
            Paragraph(p["number"], index_cell),
            Paragraph(p["title"], index_cell),
            Paragraph(p["pattern"], index_cell),
            Paragraph(p["difficulty"] or "—", index_cell),
        ])

    idx_table = Table(
        rows,
        colWidths=[15 * mm, 66 * mm, 56 * mm, 25 * mm],
        repeatRows=1
    )
    idx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.35, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SOFT]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(idx_table)
    story.append(PageBreak())

    # -------------------------
    # Problem pages
    # -------------------------
    for idx, p in enumerate(problems):
        story.append(Paragraph(
            f"PROBLEM {p['number']}", eyebrow
        ))
        story.append(Paragraph(
            escape(p["title"]), problem_title
        ))
        story.append(pill_row(p))
        story.append(Spacer(1, 1 * mm))

        question_text = escape(
            p["question"] or
            "See the original LeetCode statement in the problem README."
        )
        story.append(Paragraph("QUESTION", eyebrow))
        story.append(card(
            Paragraph(question_text, card_text),
            bg=WHITE,
            border=BORDER,
            pad=9
        ))
        story.append(Spacer(1, 4 * mm))

        if p["example"]:
            story.append(Paragraph("EXAMPLE", eyebrow))
            # Preformatted keeps all programming symbols exactly as written.
            ex = Preformatted(
                p["example"],
                ParagraphStyle(
                    f"Example{idx}", fontName="DejaVuMono", fontSize=8.3,
                    leading=10.1, textColor=TEXT
                ),
                maxLineLength=100
            )
            story.append(card(ex, bg=SOFT, border=BORDER, pad=7))
            story.append(Spacer(1, 4 * mm))

        recall = Table([[
            [Paragraph("PATTERN", card_label), Paragraph(escape(p["pattern"]), card_text)],
            [Paragraph("TIME", card_label), Paragraph(escape(p["time"]), card_text)],
            [Paragraph("SPACE", card_label), Paragraph(escape(p["space"]), card_text)],
        ]], colWidths=[57 * mm, 57 * mm, 57 * mm])
        recall.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BLUE_PALE),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#C8DDF7")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(recall)
        story.append(Spacer(1, 5 * mm))

        lines = p["code"].count("\n") + 1
        if lines <= 28:
            fs, leading = 8.5, 9.9
        elif lines <= 38:
            fs, leading = 7.8, 9.1
        elif lines <= 50:
            fs, leading = 7.15, 8.35
        else:
            fs, leading = 6.55, 7.7

        story.append(Paragraph("SOLUTION", eyebrow))
        story += code_block(
            p,
            fs=fs,
            leading=leading
        )
        story.append(Spacer(1, 4 * mm))
        story.append(card(
            Paragraph(
                "<b>Revision cue:</b> Before moving on, explain the "
                "core idea in one or two sentences without looking back.",
                tip_text
            ),
            bg=BLUE_PALE,
            border=colors.HexColor("#C8DDF7"),
            pad=7
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f"{idx + 1} / {len(problems)}",
            tiny
        ))

        if idx != len(problems) - 1:
            story.append(PageBreak())

    doc.build(
        story,
        onFirstPage=cover_page,
        onLaterPages=lambda canvas, doc: (
            top_accent(canvas, doc),
            footer(canvas, doc)
        )
    )
    print(f"Generated {OUTPUT} with {len(problems)} problems.")


if __name__ == "__main__":
    build()

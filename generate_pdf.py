from pathlib import Path
from html import unescape, escape
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted,
    KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "LeetCode_Notes.pdf"

# Supported source-file extensions. The generator preserves the submitted file exactly.
LANGUAGES = {
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++",
    ".c": "C", ".py": "Python", ".java": "Java",
    ".js": "JavaScript", ".ts": "TypeScript", ".go": "Go",
    ".rs": "Rust", ".cs": "C#", ".kt": "Kotlin",
    ".swift": "Swift", ".php": "PHP", ".rb": "Ruby",
}

# Use a readable Unicode font available on GitHub Actions runners.
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuMono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))

PAGE_W, PAGE_H = A4
MARGIN = 14 * mm

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleLarge", fontName="DejaVu-Bold", fontSize=20, leading=23,
    alignment=TA_CENTER, spaceAfter=7, textColor=colors.HexColor("#17365D")
)
meta_style = ParagraphStyle(
    "Meta", fontName="DejaVu-Bold", fontSize=10.5, leading=13,
    spaceAfter=3, textColor=colors.HexColor("#333333")
)
section_style = ParagraphStyle(
    "Section", fontName="DejaVu-Bold", fontSize=12.5, leading=15,
    spaceBefore=5, spaceAfter=3, textColor=colors.HexColor("#17365D")
)
body_style = ParagraphStyle(
    "BodyLarge", fontName="DejaVu", fontSize=11.2, leading=14.2,
    spaceAfter=4
)
small_style = ParagraphStyle(
    "Small", fontName="DejaVu", fontSize=9.3, leading=11.5,
    textColor=colors.HexColor("#555555")
)
cover_style = ParagraphStyle(
    "Cover", fontName="DejaVu-Bold", fontSize=27, leading=33,
    alignment=TA_CENTER, textColor=colors.HexColor("#17365D")
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
        if candidate and not candidate.lower().startswith(("example", "constraints", "follow-up")):
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
    nested = len(re.findall(r"for\s*\([^)]*\).*\{", c, re.S))
    if "sort(" in c or ".sort(" in c:
        return "Time: O(n log n) typical  |  Space: O(n) or O(1) auxiliary"
    if "unordered_set" in c or "unordered_map" in c or "set<" in c:
        return "Time: O(n) average  |  Space: O(n)"
    if nested >= 2:
        return "Time: O(n²)  |  Space: O(1) auxiliary"
    if "while" in c and ("left" in c and "right" in c):
        return "Time: O(n)  |  Space: O(1) auxiliary"
    return "Time: O(n)  |  Space: O(1) auxiliary"


def clean_code(code):
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    return code.strip()


def find_solution_file(folder):
    """Find the submitted solution without assuming it is C++."""
    candidates = []
    for path in folder.iterdir():
        if not path.is_file() or path.suffix.lower() not in LANGUAGES:
            continue
        candidates.append(path)

    if not candidates:
        return None

    # Prefer a solution whose stem matches the problem folder, e.g. 0001-two-sum.cpp.
    exact = [p for p in candidates if p.stem.lower() == folder.name.lower()]
    if exact:
        return sorted(exact)[0]

    # Also support LeetHub's solution.<ext> naming convention.
    solution_named = [p for p in candidates if p.stem.lower() == "solution"]
    if solution_named:
        return sorted(solution_named)[0]

    return sorted(candidates, key=lambda p: p.name.lower())[0]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DejaVu", 8.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(PAGE_W / 2, 7 * mm, f"My_Leetcode • Page {doc.page}")
    canvas.restoreState()


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
        code = clean_code(solution_file.read_text(encoding="utf-8", errors="ignore"))
        language = LANGUAGES[solution_file.suffix.lower()]
        problems.append({
            "title": title,
            "difficulty": difficulty,
            "question": question,
            "example": example,
            "code": code,
            "language": language,
            "pattern": infer_pattern(title, question, code),
            "complexity": complexity(code),
        })

    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=11 * mm, bottomMargin=12 * mm,
        title="My Leetcode Notes", author="xernix-2007"
    )

    story = [Spacer(1, 55 * mm), Paragraph("My Leetcode", cover_style),
             Spacer(1, 7 * mm),
             Paragraph(f"{len(problems)} solved problems • automatically generated", body_style),
             Spacer(1, 5 * mm),
             Paragraph("Each problem gets one page with a large, readable solution code section.", body_style),
             PageBreak()]

    for idx, p in enumerate(problems):
        story.append(Paragraph(p["title"], title_style))
        story.append(Paragraph(
            f"Difficulty: {p['difficulty'] or '—'} &nbsp;&nbsp; | &nbsp;&nbsp; Pattern: {p['pattern']}",
            meta_style
        ))

        story.append(Paragraph("Question", section_style))
        story.append(Paragraph(p["question"] or "See the original LeetCode statement in the problem README.", body_style))

        if p["example"]:
            story.append(Paragraph("Example", section_style))
            story.append(Preformatted(escape(p["example"]), ParagraphStyle(
                "Example", fontName="DejaVuMono", fontSize=9.5, leading=11.5,
                leftIndent=5, spaceAfter=3
            )))

        story.append(Paragraph("Short Answer / Approach", section_style))
        story.append(Paragraph(
            "Use the repository solution below. The key pattern is " + p["pattern"] + ".",
            body_style
        ))
        story.append(Paragraph("Complexity", section_style))
        story.append(Paragraph(p["complexity"], body_style))

        story.append(Paragraph(f"{p['language']} Solution", section_style))
        lines = p["code"].count("\n") + 1
        if lines <= 28:
            fs, leading = 10.2, 12.0
        elif lines <= 38:
            fs, leading = 9.4, 11.0
        elif lines <= 50:
            fs, leading = 8.5, 9.9
        else:
            fs, leading = 7.6, 8.8
        code_style = ParagraphStyle(
            f"Code{idx}", fontName="DejaVuMono", fontSize=fs, leading=leading,
            leftIndent=5, rightIndent=5, spaceBefore=1, spaceAfter=1,
            borderWidth=0.5, borderPadding=5,
            borderColor=colors.HexColor("#B8C7D9"),
            backColor=colors.HexColor("#F5F7FA")
        )
        # Escape source so C++/HTML-like syntax such as vector<int> is never treated as markup.
        story.append(Preformatted(escape(p["code"]), code_style, maxLineLength=95))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(f"Problem {idx + 1} of {len(problems)}", small_style))
        if idx != len(problems) - 1:
            story.append(PageBreak())

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Generated {OUTPUT} with {len(problems)} problems.")


if __name__ == "__main__":
    build()

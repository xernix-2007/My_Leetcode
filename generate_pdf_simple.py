from pathlib import Path
from html import unescape
import re
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "LeetCode_Notes_Simple.pdf"

LANGUAGES = {
    ".cpp":"C++",".cc":"C++",".cxx":"C++",".c":"C",".py":"Python",".java":"Java",
    ".js":"JavaScript",".ts":"TypeScript",".go":"Go",".rs":"Rust",".cs":"C#",
    ".kt":"Kotlin",".swift":"Swift",".php":"PHP",".rb":"Ruby",
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("SimpleSans", f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("SimpleBold", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("SimpleMono", f"{FONT_DIR}/DejaVuSansMono.ttf"))

BLACK = colors.HexColor("#20252D")
GRAY = colors.HexColor("#69717D")
ACCENT = colors.HexColor("#5B258C")
LINE = colors.HexColor("#D9DDE3")
PAGE_W, PAGE_H = A4

def style(name, font="SimpleSans", size=9, leading=None, color=BLACK):
    return ParagraphStyle(name, fontName=font, fontSize=size,
                          leading=leading or size * 1.35, textColor=color)

TITLE = style("simple_title", "SimpleBold", 21, 25)
SECTION = style("simple_section", "SimpleBold", 8.5, 10, ACCENT)
BODY = style("simple_body", size=9, leading=12)
META = style("simple_meta", size=7.5, leading=9, color=GRAY)

def clean(text):
    text = re.sub(r"<br\\s*/?>", "\\n", text, flags=re.I)
    text = re.sub(r"</p>|</li>|</pre>|</h[1-6]>", "\\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"[ \\t]+", " ", unescape(text)).strip()

def read_readme(path):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    h2 = re.search(r"<h2>.*?>(.*?)</a></h2>", raw, re.I | re.S) or re.search(r"<h2>(.*?)</h2>", raw, re.I | re.S)
    title = clean(h2.group(1)) if h2 else path.parent.name
    h3 = re.search(r"<h3>(.*?)</h3>", raw, re.I | re.S)
    difficulty = clean(h3.group(1)) if h3 else ""
    ps = [clean(x) for x in re.findall(r"<p>(.*?)</p>", raw, re.I | re.S)]
    ps = [x for x in ps if x]
    question = next((x for x in ps if not x.lower().startswith(("example","constraints","follow-up"))), "")
    examples = [clean(x) for x in re.findall(r"<pre>(.*?)</pre>", raw, re.I | re.S)]
    return title, difficulty, question, next((x for x in examples if x), "")

def find_solution(folder):
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in LANGUAGES]
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
    out = []
    for folder in sorted(ROOT.iterdir(), key=lambda p: p.name):
        if not folder.is_dir() or not re.match(r"^\\d{4}-", folder.name):
            continue
        readme, sol = folder / "README.md", find_solution(folder)
        if not readme.exists() or sol is None:
            continue
        title, diff, question, example = read_readme(readme)
        code = sol.read_text(encoding="utf-8", errors="ignore").replace("\\r\\n","\\n").replace("\\r","\\n").strip()
        time, space = complexity(code)
        out.append({
            "number": re.match(r"^(\\d+)-", folder.name).group(1),
            "title": title, "difficulty": diff, "question": question,
            "example": example, "code": code, "language": LANGUAGES[sol.suffix.lower()],
            "time": time, "space": space
        })
    return sorted(out, key=lambda p: int(p["number"]) if p["number"].isdigit() else 999999)

def code_block(code, index):
    # Use one flowable per source line so long solutions can continue onto
    # another page instead of disappearing when they exceed one page.
    lines = code.splitlines() or [""]
    longest = max(len(x) for x in lines)
    fs = min(8.0, max(5.2, 175 / max(longest, 35)))
    code_style = style(
        f"simple_code_{index}", "SimpleMono", fs, fs * 1.32,
        BLACK
    )
    return [
        Paragraph(xml_escape(line) if line else " ", code_style)
        for line in lines
    ]


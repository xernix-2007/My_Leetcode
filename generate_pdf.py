from pathlib import Path
from html import unescape
from pygments import lex
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.token import Token
from xml.sax.saxutils import escape as xml_escape
import re
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, XPreformatted, Table, TableStyle, Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "LeetCode_Notes.pdf"

LANGUAGES = {
    ".cpp":"C++",".cc":"C++",".cxx":"C++",".c":"C",".py":"Python",".java":"Java",
    ".js":"JavaScript",".ts":"TypeScript",".go":"Go",".rs":"Rust",".cs":"C#",
    ".kt":"Kotlin",".swift":"Swift",".php":"PHP",".rb":"Ruby",
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DejaVu", f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuMono", f"{FONT_DIR}/DejaVuSansMono.ttf"))

PAGE_W, PAGE_H = A4
PURPLE=colors.HexColor("#7026A8"); PURPLE_DARK=colors.HexColor("#4B177C")
MAGENTA=colors.HexColor("#D72C86"); VIOLET=colors.HexColor("#6C2BD9")
BLUE=colors.HexColor("#2477D4"); BLUE_LIGHT=colors.HexColor("#EEF4FF")
BLUE_BORDER=colors.HexColor("#C9DDF8"); NAVY=colors.HexColor("#182A4A")
TEXT=colors.HexColor("#202C4A"); MUTED=colors.HexColor("#66718A")
WHITE=colors.white; SOFT=colors.HexColor("#F7F8FC")
CODE_BG=colors.HexColor("#111827"); CODE_BORDER=colors.HexColor("#263249")
ORANGE=colors.HexColor("#F39A13"); GREEN=colors.HexColor("#22A06B")
PINK_LIGHT=colors.HexColor("#FCEAF5"); MINT_LIGHT=colors.HexColor("#EAF8F3")
LAVENDER=colors.HexColor("#F1EAFE"); PALE_BLUE=colors.HexColor("#EFF7FF")
EASY=colors.HexColor("#F0A116"); MEDIUM=colors.HexColor("#F0A116"); HARD=colors.HexColor("#D84C4C")

def style(name,font="DejaVu",size=8,leading=None,color=TEXT,align=TA_LEFT):
    return ParagraphStyle(name,fontName=font,fontSize=size,leading=leading or size*1.35,textColor=color,alignment=align)

S9=style("S9",size=9); S9B=style("S9B","DejaVu-Bold",9,11)
SMALL=style("SMALL",size=7.2,leading=9,color=MUTED)
TINY=style("TINY",size=6.4,leading=8,color=MUTED)

def p(text,st=S9): return Paragraph(str(text),st)

def strip_html(text):
    text=re.sub(r"<br\s*/?>","\n",text,flags=re.I)
    text=re.sub(r"</p>|</li>|</pre>|</h[1-6]>","\n",text,flags=re.I)
    text=re.sub(r"<[^>]+>","",text); text=unescape(text)
    text=re.sub(r"[ \t]+"," ",text)
    return text.strip()

def read_readme(path):
    raw=path.read_text(encoding="utf-8",errors="ignore")
    h2=re.search(r"<h2>.*?>(.*?)</a></h2>",raw,re.I|re.S) or re.search(r"<h2>(.*?)</h2>",raw,re.I|re.S)
    title=strip_html(h2.group(1)) if h2 else path.parent.name
    diff=re.search(r"<h3>(.*?)</h3>",raw,re.I|re.S)
    difficulty=strip_html(diff.group(1)) if diff else ""
    question=""
    for item in re.findall(r"<p>(.*?)</p>",raw,re.I|re.S):
        candidate=strip_html(item)
        if candidate and not candidate.lower().startswith(("example","constraints","follow-up")):
            question=candidate; break
    examples=[]
    for item in re.findall(r"<pre>(.*?)</pre>",raw,re.I|re.S):
        candidate=strip_html(item)
        if candidate: examples.append(candidate); break
    return title,difficulty,question,examples[0] if examples else ""

def infer_pattern(title,question,code):
    text=f"{title} {question} {code}".lower()
    rules=[
        (r"binary|mid\s*=|lower_bound|upper_bound","Binary Search"),
        (r"unordered_map|unordered_set|set<|map<","Hashing / Set"),
        (r"left.*right|two pointer|while.*left.*right","Two Pointers"),
        (r"window|sliding|substring","Sliding Window"),
        (r"listnode|linked list","Linked List"),
        (r"tree|treenode|inorder|preorder|postorder","Binary Tree"),
        (r"sort\(|sorting","Sorting"),
        (r"dp|dynamic programming|memo","Dynamic Programming"),
        (r"maxprofit|maximum subarray|kadane","Greedy / Kadane"),
        (r"reverse|palindrome|digit","Math / Simulation")]
    for pat,label in rules:
        if re.search(pat,text): return label
    return "Arrays / Implementation"

def complexity(code):
    c=code.replace(" ","")
    if "sort(" in c or ".sort(" in c: return "O(n log n)","O(n) / O(1)"
    if "unordered_set" in c or "unordered_map" in c or "set<" in c: return "O(n) avg.","O(n)"
    if len(re.findall(r"for\s*\([^)]*\)",c))>=2: return "O(n²)","O(1)"
    if "while" in c and "left" in c and "right" in c: return "O(n)","O(1)"
    return "O(n)","O(1)"

def find_solution_file(folder):
    candidates=[p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in LANGUAGES]
    if not candidates: return None
    exact=[p for p in candidates if p.stem.lower()==folder.name.lower()]
    if exact: return sorted(exact)[0]
    named=[p for p in candidates if p.stem.lower()=="solution"]
    if named: return sorted(named)[0]
    return sorted(candidates,key=lambda p:p.name.lower())[0]

def difficulty_color(value):
    v=value.lower()
    if "hard" in v: return HARD
    if "medium" in v: return MEDIUM
    return EASY

def draw_round_rect(c,x,y,w,h,fill,stroke=None,radius=7,sw=.6):
    c.setFillColor(fill); c.setStrokeColor(stroke or fill); c.setLineWidth(sw)
    c.roundRect(x,y,w,h,radius,fill=1,stroke=1 if stroke else 0)

def draw_pill(c,x,y,w,h,text,fill,fs=8):
    draw_round_rect(c,x,y,w,h,fill,radius=h/2)
    c.setFillColor(WHITE); c.setFont("DejaVu-Bold",fs)
    c.drawCentredString(x+w/2,y+h/2-fs*.34,text)

def draw_para(c,text,x,y_top,w,st,max_h=None):
    para=Paragraph(text,st); _,ah=para.wrap(w,max_h or PAGE_H); para.drawOn(c,x,y_top-ah); return ah

def syntax_highlight(code,language):
    names={"C++":"cpp","C":"c","Python":"python","Java":"java","JavaScript":"javascript","TypeScript":"typescript",
           "Go":"go","Rust":"rust","C#":"csharp","Kotlin":"kotlin","Swift":"swift","PHP":"php","Ruby":"ruby"}
    try: lexer=get_lexer_by_name(names.get(language,"text"))
    except Exception: lexer=TextLexer()
    def tc(tok):
        if tok in Token.Comment: return "#6A9955"
        if tok in Token.Keyword or tok in Token.Keyword.Type: return "#C586C0"
        if tok in Token.Name.Class: return "#4EC9B0"
        if tok in Token.Name.Function or tok in Token.Name.Function.Magic: return "#DCDCAA"
        if tok in Token.Name.Builtin: return "#569CD6"
        if tok in Token.Literal.String: return "#CE9178"
        if tok in Token.Literal.Number: return "#B5CEA8"
        return "#D4D4D4"
    return "".join(f'<font color="{tc(tok)}">{xml_escape(val)}</font>' for tok,val in lex(code,lexer))

def draw_code(c,code,language,x,y,w,h,number):
    draw_round_rect(c,x,y,w,h,CODE_BG,stroke=CODE_BORDER,radius=8,sw=.8)
    c.setFillColor(PURPLE)
    c.roundRect(x,y+h-27,w,27,8,fill=1,stroke=0)
    c.rect(x,y+h-27,w,10,fill=1,stroke=0)
    c.setFillColor(WHITE)
    c.setFont("DejaVu-Bold",8.4)
    c.drawString(x+13,y+h-17,f"</>   Solution ({language})")
    c.setFont("DejaVu",6.8)
    c.setFillColor(colors.HexColor("#E7D7F7"))
    c.drawRightString(x+w-13,y+h-17,f"Problem {number}")

    lines=code.splitlines() or [""]
    max_len=max((len(v) for v in lines),default=1)
    # Full-width code area: prefer readability, then reduce size only when necessary.
    fs=min(8.1,max(5.0,(w-26)/(max_len*.55)))
    leading=fs*1.30
    available=h-40
    if len(lines)*leading > available:
        leading=max(4.6,available/max(1,len(lines)))
        fs=max(4.0,leading/1.30)

    code_style=style(f"code_{number}","DejaVuMono",fs,leading,colors.HexColor("#D4D4D4"))
    xp=XPreformatted(syntax_highlight(code,language),code_style)
    _,ah=xp.wrap(w-22,h-38)
    # Keep the first line inside the header and the complete block inside the panel.
    xp.drawOn(c,x+11,y+h-34-ah)

def visual_card(c,pattern,x,y,w,h):
    draw_round_rect(c,x,y,w,h,WHITE,stroke=BLUE_BORDER,radius=7)
    c.setFillColor(PURPLE); c.setFont("DejaVu-Bold",10); c.drawString(x+34,y+h-21,"Visual Representation")
    c.setFont("DejaVu-Bold",15); c.drawString(x+11,y+h-23,"↗")
    cy=y+h/2-3
    if "linked list" in pattern.lower():
        for i,lab in enumerate(["2","4","3"]):
            xx=x+43+i*45; c.setFillColor(BLUE_LIGHT); c.setStrokeColor(BLUE); c.circle(xx,cy+6,10,fill=1,stroke=1)
            c.setFillColor(NAVY); c.setFont("DejaVu-Bold",8); c.drawCentredString(xx,cy+3,lab)
            if i<2:
                c.setStrokeColor(BLUE); c.line(xx+11,cy+6,xx+34,cy+6); c.line(xx+30,cy+9,xx+34,cy+6); c.line(xx+30,cy+3,xx+34,cy+6)
        c.setFillColor(MAGENTA); c.setFont("DejaVu-Bold",7); c.drawString(x+12,y+20,"pattern → nodes → result")
    else:
        xx=x+14
        for i,lab in enumerate(["INPUT","PATTERN","OUTPUT"]):
            ww=[43,55,43][i]; draw_round_rect(c,xx,cy-2,ww,24,[BLUE_LIGHT,LAVENDER,PINK_LIGHT][i],radius=12)
            c.setFillColor([BLUE,PURPLE,MAGENTA][i]); c.setFont("DejaVu-Bold",6.5); c.drawCentredString(xx+ww/2,cy+7,lab)
            if i<2: c.setStrokeColor(MUTED); c.line(xx+ww+4,cy+10,xx+ww+14,cy+10)
            xx+=ww+18

def metric_card(c,x,y,w,h,title,value,fill,accent):
    draw_round_rect(c,x,y,w,h,fill,radius=7); c.setFillColor(accent); c.circle(x+18,y+h/2,11,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont("DejaVu-Bold",8); c.drawCentredString(x+18,y+h/2-3,"✓")
    c.setFillColor(MUTED); c.setFont("DejaVu-Bold",6.6); c.drawString(x+34,y+h-18,title.upper())
    c.setFillColor(NAVY); c.setFont("DejaVu-Bold",11); c.drawString(x+34,y+10,value)

def sidebar(c,p,x,y,w,h):
    draw_round_rect(c,x,y,w,h,colors.HexColor("#F7F8FC"),stroke=colors.HexColor("#E1E6F0"),radius=10,sw=.6)
    c.setFillColor(PURPLE); c.setFont("DejaVu-Bold",12); c.drawString(x+14,y+h-28,f"#{p['number']}")
    c.setFillColor(MUTED); c.setFont("DejaVu",6.3); c.drawString(x+14,y+h-41,"PROBLEM")
    draw_para(c,p["title"],x+14,y+h-55,w-28,style(f"sideTitle_{p['number']}","DejaVu-Bold",9.3,11,NAVY),42)
    c.setStrokeColor(colors.HexColor("#DDE3EE")); c.line(x+14,y+h-112,x+w-14,y+h-112)
    yy=y+h-132
    for label,value,color in [("DIFFICULTY",p["difficulty"] or "Unknown",difficulty_color(p["difficulty"] or "")),("PATTERN",p["pattern"],PURPLE),("LANGUAGE",p["language"],VIOLET)]:
        c.setFillColor(MUTED); c.setFont("DejaVu-Bold",6.2); c.drawString(x+14,yy,label); yy-=13
        if label=="DIFFICULTY":
            draw_pill(c,x+14,yy-2,47,17,value,color,6.2); yy-=29
        else:
            c.setFillColor(TEXT); c.setFont("DejaVu",7.1); v=value[:19]+"…" if len(value)>20 else value; c.drawString(x+14,yy+1,v); yy-=25
        c.setStrokeColor(colors.HexColor("#E0E5EF")); c.line(x+14,yy+8,x+w-14,yy+8)
    c.setFillColor(MUTED); c.setFont("DejaVu-Bold",6.2); c.drawString(x+14,y+112,"QUICK LINKS")
    for i,link in enumerate(["LeetCode","Notes","Similar Problems"]):
        yy=y+95-i*17
        c.setFillColor(PURPLE); c.circle(x+16,yy+1,1.5,fill=1,stroke=0)
        c.setFillColor(TEXT); c.setFont("DejaVu",6.8); c.drawString(x+23,yy,link)
    c.setStrokeColor(colors.HexColor("#E0E5EF")); c.line(x+14,y+45,x+w-14,y+45)
    c.setFillColor(MUTED); c.setFont("DejaVu",6.2); c.drawString(x+14,y+31,"Last revised")
    c.setFillColor(NAVY); c.setFont("DejaVu-Bold",6.8); c.drawString(x+14,y+20,date.today().strftime("%d %b %Y"))
    c.setFillColor(PURPLE); c.setFont("DejaVu",5.9); c.drawString(x+14,y+9,"Pattern → recall → re-implement")

def problem_page(c,p,doc):
    margin=10*mm
    sidebar_w=41*mm
    gap=5*mm
    main_x=margin+sidebar_w+gap
    main_w=PAGE_W-main_x-margin
    content_top=PAGE_H-24*mm

    c.setFillColor(WHITE); c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)

    # Clean editorial header; decorative waves stay away from the text.
    c.setFillColor(PURPLE); c.rect(0,PAGE_H-9*mm,PAGE_W,9*mm,fill=1,stroke=0)
    c.setFillColor(MAGENTA); c.rect(0,PAGE_H-9*mm,38*mm,9*mm,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont("DejaVu-Bold",7.2)
    c.drawString(margin,PAGE_H-6.2*mm,"MY LEETCODE  •  REVISION HANDBOOK")
    c.drawRightString(PAGE_W-margin,PAGE_H-6.2*mm,f"{doc.page:02d}")

    sidebar(c,p,margin,22*mm,sidebar_w,PAGE_H-48*mm)

    x=main_x
    top=content_top
    c.setFillColor(PURPLE); c.setFont("DejaVu-Bold",7.5)
    c.drawString(x,top,f"PROBLEM {p['number']}")

    # Real title wrapping instead of painting one long string off the page.
    title_style=style(f"title_{p['number']}","DejaVu-Bold",22,24,NAVY)
    title_h=draw_para(c,p["title"],x,top-6,main_w,title_style,52)

    pill_y=top-11-title_h-19
    draw_pill(c,x,pill_y,32*mm,19,p["difficulty"] or "Unknown",difficulty_color(p["difficulty"] or ""),7.2)
    draw_pill(c,x+35*mm,pill_y,43*mm,19,p["pattern"],PURPLE,7.0)
    draw_pill(c,x+81*mm,pill_y,27*mm,19,p["language"],NAVY,7.0)

    qtop=pill_y-10
    c.setFillColor(PURPLE); c.setFont("DejaVu-Bold",8.5); c.drawString(x,qtop,"QUESTION")
    qh=55
    qy=qtop-6-qh
    draw_round_rect(c,x,qy,main_w,qh,WHITE,stroke=BLUE_BORDER,radius=6)
    c.setFillColor(MAGENTA); c.circle(x+16,qy+qh-17,7,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont("DejaVu-Bold",7); c.drawCentredString(x+16,qy+qh-20,"✓")
    draw_para(c,p["question"] or "See the original LeetCode statement in the problem README.",
              x+29,qy+qh-10,main_w-41,style(f"q_{p['number']}","DejaVu",8.8,11.3,TEXT),43)

    row_top=qy-10
    card_h=78
    left_w=main_w*.58
    right_w=main_w-left_w-5
    ex_y=row_top-card_h

    draw_round_rect(c,x,ex_y,left_w,card_h,colors.HexColor("#F4F2FF"),stroke=BLUE_BORDER,radius=7)
    c.setFillColor(PURPLE); c.setFont("DejaVu-Bold",10)
    c.drawString(x+33,ex_y+card_h-20,"Example")
    c.setFont("DejaVu-Bold",14); c.drawString(x+11,ex_y+card_h-22,"▣")
    draw_round_rect(c,x+9,ex_y+12,left_w-18,43,WHITE,radius=5)
    draw_para(c,p["example"] or "Input → Output",x+18,ex_y+49,left_w-36,
              style(f"ex_{p['number']}","DejaVuMono",7.1,9.3,TEXT),32)

    visual_card(c,p["pattern"],x+left_w+5,ex_y,right_w,card_h)

    metric_y=ex_y-8-42
    gapm=4
    mw=(main_w-2*gapm)/3
    metric_card(c,x,metric_y,mw,42,"Time Complexity",p["time"],LAVENDER,PURPLE)
    metric_card(c,x+mw+gapm,metric_y,mw,42,"Space Complexity",p["space"],PALE_BLUE,BLUE)
    metric_card(c,x+2*(mw+gapm),metric_y,mw,42,"Pattern",p["pattern"],PINK_LIGHT,MAGENTA)

    # Remove the side boxes. The solution now owns the entire content width and
    # extends slightly lower, which prevents long code from being clipped.
    code_x=x
    code_y=15*mm
    code_w=main_w
    code_h=metric_y-code_y-8
    draw_code(c,p["code"],p["language"],code_x,code_y,code_w,code_h,p["number"])

    c.setFillColor(WHITE); c.setFont("DejaVu",6.5)
    c.drawCentredString(PAGE_W/2,6*mm,"“Smarter Practice. Stronger You.”")
    c.setFont("DejaVu-Bold",7)
    c.drawRightString(PAGE_W-margin,10.5*mm,f"{doc.page:02d}")

def cover_canvas(c,doc):
    # Refined annual-report style cover: cyan frame, white field, controlled asymmetrical waves.
    c.setFillColor(BLUE); c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    c.setFillColor(WHITE); c.roundRect(7*mm,7*mm,PAGE_W-14*mm,PAGE_H-14*mm,6*mm,fill=1,stroke=0)

    # Top layered wave.
    c.setFillColor(PURPLE)
    q=c.beginPath(); q.moveTo(7*mm,PAGE_H-7*mm)
    q.curveTo(45*mm,PAGE_H-13*mm,68*mm,PAGE_H-55*mm,105*mm,PAGE_H-34*mm)
    q.curveTo(139*mm,PAGE_H-15*mm,171*mm,PAGE_H-54*mm,209*mm,PAGE_H-27*mm)
    q.curveTo(218*mm,PAGE_H-20*mm,224*mm,PAGE_H-12*mm,226*mm,PAGE_H-7*mm)
    q.lineTo(7*mm,PAGE_H-7*mm); q.close(); c.drawPath(q,fill=1,stroke=0)
    c.setFillColor(MAGENTA)
    q=c.beginPath(); q.moveTo(7*mm,PAGE_H-7*mm)
    q.curveTo(48*mm,PAGE_H-25*mm,73*mm,PAGE_H-76*mm,111*mm,PAGE_H-49*mm)
    q.curveTo(145*mm,PAGE_H-24*mm,174*mm,PAGE_H-77*mm,214*mm,PAGE_H-45*mm)
    q.curveTo(222*mm,PAGE_H-38*mm,225*mm,PAGE_H-22*mm,226*mm,PAGE_H-7*mm)
    q.lineTo(7*mm,PAGE_H-7*mm); q.close(); c.drawPath(q,fill=1,stroke=0)

    # Shallow lower wave.
    c.setFillColor(PURPLE)
    q=c.beginPath(); q.moveTo(7*mm,7*mm)
    q.curveTo(48*mm,17*mm,72*mm,39*mm,111*mm,25*mm)
    q.curveTo(151*mm,10*mm,180*mm,44*mm,226*mm,17*mm)
    q.lineTo(226*mm,7*mm); q.close(); c.drawPath(q,fill=1,stroke=0)
    c.setFillColor(MAGENTA)
    q=c.beginPath(); q.moveTo(7*mm,7*mm)
    q.curveTo(49*mm,12*mm,74*mm,29*mm,112*mm,19*mm)
    q.curveTo(152*mm,8*mm,181*mm,33*mm,226*mm,13*mm)
    q.lineTo(226*mm,7*mm); q.close(); c.drawPath(q,fill=1,stroke=0)

    c.setFillColor(WHITE); c.setFont("DejaVu-Bold",7)
    c.drawRightString(PAGE_W-15*mm,13*mm,f"{doc.page:02d}")
    c.drawString(15*mm,PAGE_H-13*mm,"XERNIX  •  DSA REVISION")

class ProblemPage(Flowable):
    def __init__(self,problem,doc_ref):
        super().__init__(); self.problem=problem; self.doc_ref=doc_ref; self.width=PAGE_W; self.height=PAGE_H-10*mm
    def wrap(self,availWidth,availHeight): return self.width,self.height
    def draw(self): problem_page(self.canv,self.problem,self.doc_ref[0])

def indexed_problems(problems):
    return sorted(problems,key=lambda q:int(q["number"]) if q["number"].isdigit() else 10**9)

def build():
    problems=[]
    for folder in sorted(ROOT.iterdir(),key=lambda p:p.name):
        if not folder.is_dir() or not re.match(r"^\d{4}-",folder.name): continue
        readme=folder/"README.md"; sol=find_solution_file(folder)
        if not readme.exists() or sol is None: continue
        title,diff,question,example=read_readme(readme); code=sol.read_text(encoding="utf-8",errors="ignore").replace("\r\n","\n").replace("\r","\n").strip()
        t,s=complexity(code)
        problems.append({"number":re.match(r"^(\d+)-",folder.name).group(1),"title":title,"difficulty":diff,"question":question,"example":example,"code":code,"language":LANGUAGES[sol.suffix.lower()],"pattern":infer_pattern(title,question,code),"time":t,"space":s})
    problems=indexed_problems(problems)

    doc=SimpleDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=0,rightMargin=0,topMargin=0,bottomMargin=0,title="My LeetCode Revision Handbook",author="xernix-2007")
    story=[Spacer(1,87*mm),Paragraph("MY LEETCODE",style("coverEy","DejaVu-Bold",10.5,13,PURPLE,TA_CENTER)),Paragraph("REVISION HANDBOOK",style("coverTitle","DejaVu-Bold",27,31,NAVY,TA_CENTER)),Paragraph("Patterns  •  Complexity  •  Solutions  •  Recall",style("coverSub","DejaVu",10.5,14,MUTED,TA_CENTER)),Spacer(1,10*mm),Paragraph(f"<b>{len(problems)}</b> problems",style("coverStat","DejaVu-Bold",17,20,PURPLE,TA_CENTER)),Paragraph("Built for active recall before interviews — understand the pattern, then rebuild the code.",style("coverBody","DejaVu",10,14,TEXT,TA_CENTER)),Spacer(1,7*mm),Paragraph("SMALL STEPS. REPEATED RECALL. STRONGER DSA.",style("coverQuote","DejaVu-Bold",8.5,11,MAGENTA,TA_CENTER)),PageBreak(),
           Spacer(1,20*mm),Paragraph("Revision Index",style("idx","DejaVu-Bold",24,28,PURPLE_DARK)),Paragraph("Find a problem by number, pattern, or difficulty.",style("idxSub","DejaVu",9.5,12,MUTED)),Spacer(1,5*mm)]
    rows=[[p("NO.",S9B),p("PROBLEM",S9B),p("PATTERN",S9B),p("LEVEL",S9B)]]
    for q in problems: rows.append([p(q["number"],SMALL),p(q["title"],S9B),p(q["pattern"],SMALL),p(q["difficulty"] or "—",SMALL)])
    table=Table(rows,colWidths=[18*mm,76*mm,62*mm,28*mm],repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),PURPLE),("TEXTCOLOR",(0,0),(-1,0),WHITE),("GRID",(0,0),(-1,-1),.35,BLUE_BORDER),("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,SOFT]),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    story += [table,PageBreak()]
    doc_ref=[None]
    for i,q in enumerate(problems):
        story.append(ProblemPage(q,doc_ref))
        if i != len(problems)-1: story.append(PageBreak())

    def on_page(c,d):
        doc_ref[0]=d
        if d.page==1: cover_canvas(c,d)
        elif d.page==2:
            c.setFillColor(PURPLE); c.rect(0,PAGE_H-4*mm,PAGE_W,4*mm,fill=1,stroke=0)
            c.setFillColor(NAVY); c.setFont("DejaVu-Bold",7); c.drawString(10*mm,PAGE_H-11*mm,"MY LEETCODE  •  REVISION HANDBOOK"); c.drawRightString(PAGE_W-10*mm,PAGE_H-11*mm,f"{d.page:02d}")
    doc.build(story,onFirstPage=on_page,onLaterPages=on_page)
    print(f"Generated {OUTPUT} with {len(problems)} problems.")

if __name__=="__main__": build()

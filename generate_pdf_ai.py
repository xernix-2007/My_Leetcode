from pathlib import Path
import json, re
from html import unescape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parent; OUTPUT=ROOT/'LeetCode_Notes.pdf'
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuMono','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
W,H=A4; M=14*mm
T=ParagraphStyle('T',fontName='DejaVu-Bold',fontSize=20,leading=23,alignment=TA_CENTER,spaceAfter=7,textColor=colors.HexColor('#17365D'))
Meta=ParagraphStyle('M',fontName='DejaVu-Bold',fontSize=10.5,leading=13,spaceAfter=3)
S=ParagraphStyle('S',fontName='DejaVu-Bold',fontSize=12.5,leading=15,spaceBefore=5,spaceAfter=3,textColor=colors.HexColor('#17365D'))
B=ParagraphStyle('B',fontName='DejaVu',fontSize=11.2,leading=14.2,spaceAfter=4)
Small=ParagraphStyle('Sm',fontName='DejaVu',fontSize=9.3,leading=11.5,textColor=colors.HexColor('#555555'))
Cover=ParagraphStyle('C',fontName='DejaVu-Bold',fontSize=27,leading=33,alignment=TA_CENTER,textColor=colors.HexColor('#17365D'))

def clean(x):
    x=re.sub(r'<br\s*/?>','\n',x,flags=re.I); x=re.sub(r'</p>|</li>|</pre>|</h[1-6]>','\n',x,flags=re.I); x=re.sub(r'<[^>]+>','',x); return re.sub(r'\s+',' ',unescape(x)).strip()
def read(folder):
    r=(folder/'README.md').read_text(encoding='utf-8',errors='ignore'); cf=sorted(folder.glob('*.cpp'))[0]
    m=re.search(r'<h2>.*?>(.*?)</a></h2>',r,re.I|re.S) or re.search(r'<h2>(.*?)</h2>',r,re.I|re.S)
    d=re.search(r'<h3>(.*?)</h3>',r,re.I|re.S); ps=re.findall(r'<p>(.*?)</p>',r,re.I|re.S)
    q=next((clean(p) for p in ps if clean(p) and not clean(p).lower().startswith(('example','constraints','follow-up'))),'')
    ex=next((clean(x) for x in re.findall(r'<pre>(.*?)</pre>',r,re.I|re.S) if clean(x)),'')
    return clean(m.group(1)) if m else folder.name, clean(d.group(1)) if d else '', q, ex, cf.read_text(encoding='utf-8',errors='ignore').strip()
def pattern(t,q,c):
    x=(t+' '+q+' '+c).lower()
    for a,b in [(r'binary|mid\s*=|lower_bound|upper_bound','Binary Search'),(r'unordered_map|unordered_set|set<|map<','Hashing / Set'),(r'left.*right|two pointer','Two Pointers'),(r'window|sliding|substring','Sliding Window'),(r'listnode|linked list','Linked List'),(r'tree|treenode|inorder|preorder|postorder','Binary Tree / Recursion'),(r'sort\(|sorting','Sorting'),(r'dp|dynamic programming|memo','Dynamic Programming'),(r'maxprofit|maximum subarray|kadane','Greedy / Kadane'),(r'reverse|palindrome|digit','Math / Simulation')]:
        if re.search(a,x): return b
    return 'Arrays / Implementation'
def footer(c,d):
    c.saveState(); c.setFont('DejaVu',8.5); c.setFillColor(colors.HexColor('#666666')); c.drawCentredString(W/2,7*mm,f'My_Leetcode • Page {d.page}'); c.restoreState()
def main():
    ps=[]
    for f in sorted(ROOT.iterdir(),key=lambda p:p.name):
        if f.is_dir() and re.match(r'^\d{4}-',f.name) and (f/'README.md').exists() and list(f.glob('*.cpp')):
            t,d,q,e,c=read(f); ai={}
            af=ROOT/'.ai'/f'{f.name}.json'
            if af.exists():
                try: ai=json.loads(af.read_text(encoding='utf-8'))
                except: pass
            ps.append((t,d,q,e,c,pattern(t,q,c),ai))
    story=[Spacer(1,55*mm),Paragraph('My Leetcode',Cover),Spacer(1,7*mm),Paragraph(f'{len(ps)} solved problems • automatically generated',B),Spacer(1,5*mm),Paragraph('Each problem gets one page with your solution and an AI optimization review.',B),PageBreak()]
    for i,(t,d,q,e,c,p,a) in enumerate(ps):
        story += [Paragraph(t,T),Paragraph(f'Difficulty: {d or "—"} &nbsp;&nbsp; | &nbsp;&nbsp; Pattern: {p}',Meta),Paragraph('Question',S),Paragraph(q or 'See the original LeetCode statement in the problem README.',B)]
        if e: story += [Paragraph('Example',S),Preformatted(e,ParagraphStyle('Ex',fontName='DejaVuMono',fontSize=9.2,leading=11,leftIndent=5))]
        story += [Paragraph('Your Approach',S),Paragraph('Your repository solution is shown below. The detected pattern is '+p+'.',B),Paragraph('Your Complexity',S)]
        your='Time: see solution analysis  |  Space: see solution analysis'
        if a: your=a.get('student_complexity',your)
        story.append(Paragraph(your,B))
        lines=c.count('\n')+1; fs=10.0 if lines<=28 else 9.2 if lines<=38 else 8.3 if lines<=50 else 7.5
        cs=ParagraphStyle(f'YC{i}',fontName='DejaVuMono',fontSize=fs,leading=fs+1.7,leftIndent=5,rightIndent=5,borderWidth=.5,borderPadding=5,borderColor=colors.HexColor('#B8C7D9'),backColor=colors.HexColor('#F5F7FA'))
        story += [Preformatted(c,cs,maxLineLength=95)]
        if a:
            story += [Paragraph('🤖 AI OPTIMIZED SOLUTION',S),Paragraph(f'<b>Verdict:</b> {a.get("verdict","—")} &nbsp;&nbsp; <b>Approach:</b> {a.get("optimal_approach","—")}',B),Paragraph(f'<b>{a.get("optimal_complexity","—")}</b>',B),Paragraph('<b>Why it is better:</b> '+a.get('why_better','—'),B),Paragraph('Optimized C++ Code',S)]
            oc=a.get('optimized_code',c); ol=oc.count('\n')+1; ofs=9.0 if ol<=24 else 8.3 if ol<=34 else 7.6
            ocs=ParagraphStyle(f'OC{i}',fontName='DejaVuMono',fontSize=ofs,leading=ofs+1.5,leftIndent=5,rightIndent=5,borderWidth=.5,borderPadding=5,borderColor=colors.HexColor('#A8B8C8'),backColor=colors.HexColor('#F0F4F8'))
            story += [Preformatted(oc,ocs,maxLineLength=95),Paragraph('<b>Key learning:</b> '+a.get('key_learning','—'),B)]
        story += [Paragraph(f'Problem {i+1} of {len(ps)}',Small)]
        if i<len(ps)-1: story.append(PageBreak())
    SimpleDocTemplate(str(OUTPUT),pagesize=A4,rightMargin=M,leftMargin=M,topMargin=11*mm,bottomMargin=12*mm,title='My Leetcode Notes',author='xernix-2007').build(story,onFirstPage=footer,onLaterPages=footer)
    print('Generated',OUTPUT,'with',len(ps),'problems.')
if __name__=='__main__': main()

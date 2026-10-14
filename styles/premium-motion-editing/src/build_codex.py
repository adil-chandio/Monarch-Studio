#!/usr/bin/env python3
"""Build the human codex from canonical chapters; no video generation.

Markdown is canonical. HTML supports Drive -> Google Docs conversion. PDF is
an additional reader-friendly view, not a substitute for the source library.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import urljoin
import markdown
from bs4 import BeautifulSoup,NavigableString

S=Path(__file__).resolve().parents[1]
BASE='https://github.com/adil-chandio/Monarch-Studio/blob/main/styles/premium-motion-editing/knowledge/'

def assemble():
    chapters=sorted((S/'knowledge').glob('[0-9][0-9]_*.md'))
    intro='''# WF-05 · Premium Motion Editing\n\n## Complete operating codex · foundation v1.0\n\n**User policy locked 15 October 2026:** V5 clean editorial direction + accepted V6 depth/motion/transition/sound. **No V6 bottom caption pills or active-word lower strip by default.**\n\nThis is a source-backed production library: creative DNA, metaphors, motion, typography, narration, cleanup, engineering, QA, recovery and cross-platform operation. Historical source/evidence is preserved alongside the new reusable approved profile.\n\nNo newly rendered full-length combined-policy master is claimed. Technical validity, creative fidelity and user acceptance are distinct.\n\n## Contents\n\n'''
    index=['# WF-05 knowledge index','', 'Read the approved profile and FRESH_CHAT first. Historical V6 captions are not the current default.','']
    for p in chapters:
        title=p.read_text().splitlines()[0].lstrip('# ').strip()
        intro+=f'- [{title}]({p.name})\n';index.append(f'- [{title}]({p.name})')
    index += ['', '- [Complete codex](MASTER_CODEX.md)','- [Source inventory](../records/SOURCE_INVENTORY.json)','- [Coverage audit](../data/coverage.json)','- [Verified platform links](../data/links.json)']
    (S/'knowledge/INDEX.md').write_text('\n'.join(index)+'\n')
    content=intro+'\n\n'+'\n\n---\n\n'.join(p.read_text().strip() for p in chapters)
    content+='\n\n## End of canonical codex\n\nWF05_CODEX_END_20261015 · Policy wf05-clean-editorial-20261015 · V6 lower caption pills rejected.\n'
    path=S/'knowledge/MASTER_CODEX.md';path.write_text(content)
    return path,content

def make_html(text,out):
    body=markdown.markdown(text,extensions=['tables','fenced_code','sane_lists'])
    soup=BeautifulSoup(body,'html.parser')
    for link in soup.find_all('a',href=True):
        href=link['href']
        if not href.startswith(('http://','https://','#','mailto:')):link['href']=urljoin(BASE,href)
    digest=hashlib.sha256(text.encode()).hexdigest()
    html='''<!doctype html><html><head><meta charset="utf-8"><title>WF-05 · Premium Motion Editing — HUB & Complete Codex</title><style>
body{font-family:Arial,sans-serif;color:#24183c;font-size:10.5pt;line-height:1.5}h1{color:#38204f;font-size:23pt;margin-top:26pt}h2{color:#674596;font-size:15pt;margin-top:18pt}h3{color:#38204f;font-size:12pt}table{border-collapse:collapse;width:100%;font-size:8.5pt}td,th{border:1px solid #d8cfe7;padding:6pt;vertical-align:top}th{background:#ebe4f5}code{font-family:Courier New,monospace;font-size:9pt}blockquote{border-left:3pt solid #7954a5;padding-left:10pt}a{color:#59338e}
</style></head><body>'''+str(soup)+f'<p>WF05_CODEX_SHA256={digest}</p></body></html>'
    out.write_text(html);return str(soup),digest

def make_pdf(html,out):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Preformatted,KeepTogether
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.colors import HexColor,white
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from xml.sax.saxutils import escape
    fonts=S/'assets/fonts/document'
    pdfmetrics.registerFont(TTFont('Book',str(fonts/'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('BookBold',str(fonts/'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('BookItalic',str(S/'assets/fonts/BarlowCondensed-MediumItalic.ttf')))
    pdfmetrics.registerFont(TTFont('Mono',str(fonts/'DejaVuSansMono.ttf')))
    pdfmetrics.registerFont(TTFont('Display',str(S/'assets/fonts/Anton-Regular.ttf')))
    pdfmetrics.registerFontFamily('Book',normal='Book',bold='BookBold',italic='BookItalic',boldItalic='BookBold')
    body=ParagraphStyle('body',fontName='Book',fontSize=9.1,leading=14.2,textColor=HexColor('#292239'),spaceAfter=8,splitLongWords=True)
    h1=ParagraphStyle('chapter',parent=body,fontName='BookBold',fontSize=19,leading=24,textColor=HexColor('#38234f'),spaceBefore=18,spaceAfter=12,keepWithNext=True)
    h2=ParagraphStyle('sub',parent=body,fontName='BookBold',fontSize=12.4,leading=17,textColor=HexColor('#6b4694'),spaceBefore=13,spaceAfter=7,keepWithNext=True)
    h3=ParagraphStyle('smallhead',parent=h2,fontSize=10.7,leading=15)
    cell=ParagraphStyle('cell',parent=body,fontSize=7.2,leading=10.5,spaceAfter=2,wordWrap='CJK')
    small=ParagraphStyle('small',parent=body,fontSize=8,leading=12)
    code=ParagraphStyle('code',parent=body,fontName='Mono',fontSize=7.1,leading=10)
    def inline(node):
        if isinstance(node,NavigableString):return escape(str(node))
        if node.name in ['strong','b']:return '<b>'+''.join(inline(x) for x in node.children)+'</b>'
        if node.name in ['em','i']:return '<i>'+''.join(inline(x) for x in node.children)+'</i>'
        if node.name=='code':return '<font name="Mono">'+escape(node.get_text())+'</font>'
        if node.name=='a':return '<a href="'+escape(node.get('href',''),{'"':'&quot;'})+'" color="#603c91">'+''.join(inline(x) for x in node.children)+'</a>'
        if node.name=='br':return '<br/>'
        return ''.join(inline(x) for x in node.children)
    story=[Spacer(1,690),PageBreak()]
    soup=BeautifulSoup(html,'html.parser');chapter_seen=False
    for node in soup.children:
        if isinstance(node,NavigableString):continue
        if node.name=='h1':
            title=node.get_text()
            if title.startswith(tuple(f'{i:02d} ·' for i in range(1,18))):
                if chapter_seen:story.append(PageBreak())
                chapter_seen=True
            story.append(Paragraph(inline(node),h1))
        elif node.name in ['h2','h3','h4']:story.append(Paragraph(inline(node),h2 if node.name=='h2' else h3))
        elif node.name=='p':story.append(Paragraph(inline(node),body))
        elif node.name in ['ul','ol']:
            for i,li in enumerate(node.find_all('li',recursive=False),1):story.append(Paragraph((f'{i}. ' if node.name=='ol' else '• ')+inline(li),body))
        elif node.name=='blockquote':
            story.append(Paragraph(inline(node),ParagraphStyle('quote',parent=body,leftIndent=12,borderColor=HexColor('#9f85bf'),borderWidth=.7,borderPadding=9,backColor=HexColor('#f2edf7'))))
        elif node.name=='pre':
            text=node.get_text();lines=[]
            for line in text.splitlines():
                while len(line)>98:lines.append(line[:98]);line=line[98:]
                lines.append(line)
            story.append(Preformatted('\n'.join(lines),code));story.append(Spacer(1,8))
        elif node.name=='table':
            rows=[]
            for tr in node.find_all('tr'):
                rows.append([Paragraph(inline(td),cell) for td in tr.find_all(['td','th'],recursive=False)])
            if rows:
                n=max(map(len,rows));widths=[507/n]*n
                if n==5:widths=[22,64,64,151,206]
                elif n==2:widths=[133,374]
                elif n==4:widths=[47,166,221,73]
                table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
                table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e9e2f2')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.35,HexColor('#d8cce5')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story+=[table,Spacer(1,12)]
        elif node.name=='hr':story.append(Spacer(1,10))
    def cover(c,doc):
        c.saveState();c.setFillColor(HexColor('#e7e2f5'));c.rect(0,0,595,842,fill=1,stroke=0)
        c.setStrokeColor(HexColor('#bda9d9'));c.setLineWidth(1.1);c.ellipse(270,505,630,775,stroke=1,fill=0);c.ellipse(345,435,665,690,stroke=1,fill=0)
        c.setFillColor(HexColor('#68438f'));c.setFont('BookBold',11);c.drawString(44,780,'MONARCH STUDIO  /  PERMANENT STYLE LIBRARY')
        c.setFillColor(HexColor('#281b40'));c.setFont('Display',64);c.drawString(42,674,'WF—05')
        for text,y in [('PREMIUM',548),('MOTION',466),('EDITING',384)]:c.setFont('Display',76);c.drawString(42,y,text)
        c.setFont('Book',14);c.drawString(44,324,'The complete operating codex')
        c.setFillColor(HexColor('#694492'));c.setFont('BookBold',10);c.drawString(44,280,'CREATIVE DNA  ·  ENGINEERING  ·  QA  ·  RECOVERY')
        p=Paragraph('V5 clean editorial direction + accepted V6 motion.<br/><b>No V6 bottom caption pills or active-word strip.</b>',ParagraphStyle('coverpolicy',fontName='Book',fontSize=12,leading=19,textColor=HexColor('#281b40')));p.wrapOn(c,490,100);p.drawOn(c,44,186)
        c.setFont('Book',9);c.drawString(44,119,'Policy locked 15 October 2026  ·  Foundation v1.0')
        c.drawString(44,98,'Source-backed knowledge. Historical versions preserved.')
        c.drawString(44,77,'No new full-length hybrid master claimed in this documentation task.')
        c.restoreState()
    def page(c,doc):
        c.saveState();c.setStrokeColor(HexColor('#d8cfe7'));c.line(44,802,551,802);c.setFillColor(HexColor('#756883'));c.setFont('Book',7.6);c.drawString(44,811,'WF-05  /  PREMIUM MOTION EDITING');c.drawRightString(551,811,'CLEAN EDITORIAL POLICY · 15 OCT 2026');c.line(44,42,551,42);c.drawString(44,28,'Full source, receipts and current links accompany this codex.');c.drawRightString(551,28,str(doc.page));c.restoreState()
    doc=SimpleDocTemplate(str(out),pagesize=(595,842),leftMargin=44,rightMargin=44,topMargin=54,bottomMargin=53,title='WF-05 Premium Motion Editing — Complete Codex',author='Monarch Studio')
    doc.build(story,onFirstPage=cover,onLaterPages=page)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=Path('.runtime/wf05-publication'));ap.add_argument('--pdf',action='store_true');a=ap.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
    path,text=assemble();html,digest=make_html(text,a.output_dir/'WF05_Complete_Codex.html')
    if a.pdf:make_pdf(html,a.output_dir/'WF05_Premium_Motion_Editing_Codex.pdf')
    report={'canonical':str(path),'words':len(text.split()),'chapters':17,'sha256':digest,'html':str(a.output_dir/'WF05_Complete_Codex.html'),'pdf':str(a.output_dir/'WF05_Premium_Motion_Editing_Codex.pdf') if a.pdf else None}
    (a.output_dir/'CODEX_BUILD.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()

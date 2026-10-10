#!/usr/bin/env python3
"""Compile the entire project — every document, every source file, every
visual reference — into one PDF with a real table of contents."""
import os, re, html, textwrap
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, Image as RLImage,
                                PageBreak, KeepTogether, HRFlowable)
from reportlab.platypus.tableofcontents import TableOfContents
from PIL import Image as PILImage

ROOT = '/home/user'
OUT = os.path.join(ROOT, 'MONARCH_STICKMAN_MOTION_ENGINE_COMPLETE.pdf')
DJ = '/usr/share/fonts/truetype/dejavu/'

CV = '/usr/local/lib/python3.13/site-packages/cv2/qt/fonts/'
for nm, fn in (('DJ', 'DejaVuSans.ttf'), ('DJ-B', 'DejaVuSans-Bold.ttf'),
               ('DJ-I', 'DejaVuSans-Oblique.ttf'), ('DJ-BI', 'DejaVuSans-BoldOblique.ttf'),
               ('MN', 'DejaVuSansMono.ttf'), ('MN-B', 'DejaVuSansMono-Bold.ttf')):
    for base in (DJ, CV):
        if os.path.exists(base + fn):
            pdfmetrics.registerFont(TTFont(nm, base + fn))
            break
    else:
        raise SystemExit('missing font ' + fn)
pdfmetrics.registerFontFamily('DJ', normal='DJ', bold='DJ-B', italic='DJ-I',
                              boldItalic='DJ-BI')

INK = colors.HexColor('#1a1816')
ACC = colors.HexColor('#b22c20')
BLU = colors.HexColor('#1c52be')
SOFT = colors.HexColor('#6e675d')
CODEBG = colors.HexColor('#f4f1e9')
RULE = colors.HexColor('#d8d2c4')
PAPER = colors.HexColor('#faf8f2')

PW, PH = A4
LM, RM, TM, BM = 17 * mm, 15 * mm, 18 * mm, 16 * mm
CW = PW - LM - RM

S = {}
S['h1'] = ParagraphStyle('h1', fontName='DJ-B', fontSize=19, leading=23, textColor=ACC,
                         spaceBefore=4, spaceAfter=9)
S['h2'] = ParagraphStyle('h2', fontName='DJ-B', fontSize=14, leading=18, textColor=INK,
                         spaceBefore=13, spaceAfter=6)
S['h3'] = ParagraphStyle('h3', fontName='DJ-B', fontSize=11, leading=14.5, textColor=BLU,
                         spaceBefore=10, spaceAfter=4)
S['h4'] = ParagraphStyle('h4', fontName='DJ-B', fontSize=9.6, leading=13, textColor=INK,
                         spaceBefore=8, spaceAfter=3)
S['p'] = ParagraphStyle('p', fontName='DJ', fontSize=8.9, leading=13.2, textColor=INK,
                        spaceAfter=5, alignment=TA_LEFT)
S['li'] = ParagraphStyle('li', parent=S['p'], leftIndent=11, bulletIndent=2, spaceAfter=2.6)
S['li2'] = ParagraphStyle('li2', parent=S['li'], leftIndent=24, bulletIndent=14)
S['quote'] = ParagraphStyle('quote', parent=S['p'], leftIndent=11, textColor=SOFT,
                            fontName='DJ-I', borderPadding=0)
S['code'] = ParagraphStyle('code', fontName='MN', fontSize=7.3, leading=9.4,
                           textColor=colors.HexColor('#23201c'))
S['codeln'] = ParagraphStyle('codeln', fontName='MN', fontSize=6.3, leading=8.4,
                             textColor=colors.HexColor('#23201c'))
S['tc'] = ParagraphStyle('tc', fontName='DJ', fontSize=7.4, leading=9.6, textColor=INK)
S['th'] = ParagraphStyle('th', fontName='DJ-B', fontSize=7.4, leading=9.6,
                         textColor=colors.white)
S['cap'] = ParagraphStyle('cap', fontName='DJ-I', fontSize=7.6, leading=10,
                          textColor=SOFT, alignment=TA_CENTER, spaceBefore=3)
S['cover_t'] = ParagraphStyle('ct', fontName='DJ-B', fontSize=29, leading=34,
                              textColor=INK, alignment=TA_CENTER)
S['cover_s'] = ParagraphStyle('cs', fontName='DJ', fontSize=12, leading=17,
                              textColor=SOFT, alignment=TA_CENTER)
S['part'] = ParagraphStyle('part', fontName='DJ-B', fontSize=26, leading=31,
                           textColor=ACC, alignment=TA_LEFT)
S['partn'] = ParagraphStyle('partn', fontName='DJ-B', fontSize=11, leading=14,
                            textColor=SOFT, alignment=TA_LEFT)

# ───────────────────────────── text sanitising
_EMOJI = re.compile(
    '[\U0001F000-\U0001FAFF\U00002190-\U000021FF\U0001F1E6-\U0001F1FF'
    '\u200d\ufe0f\ufe0e\u20e3\u2B00-\u2BFF\u2600-\u27BF]')
_KEEP = {'\u2192': '->', '\u2190': '<-', '\u2194': '<->', '\u21d2': '=>',
         '\u2713': 'v', '\u2714': 'v', '\u2717': 'x', '\u2718': 'x',
         '\u2705': '[PASS]', '\u274c': '[FAIL]', '\u26a0': '[!]',
         '\u2022': '\u00b7', '\u25a0': '#', '\u25cf': '\u00b7'}


def clean(t):
    if not t:
        return ''
    for k, v in _KEEP.items():
        t = t.replace(k, v)
    t = _EMOJI.sub('', t)
    return t.replace('\u00a0', ' ')


def esc(t):
    return html.escape(clean(t), quote=False)


def inline(t):
    """Markdown inline -> reportlab mini-HTML."""
    t = clean(t)
    out, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c == '`':
            j = t.find('`', i + 1)
            if j > 0:
                out.append('<font face="MN" size="7.8" color="#8a2d1e">'
                           + html.escape(t[i + 1:j], quote=False) + '</font>')
                i = j + 1
                continue
        if t.startswith('**', i):
            j = t.find('**', i + 2)
            if j > 0:
                out.append('<b>' + inline(t[i + 2:j]) + '</b>')
                i = j + 2
                continue
        if c == '*' and not t.startswith('**', i):
            j = t.find('*', i + 1)
            if 0 < j and '\n' not in t[i:j]:
                out.append('<i>' + inline(t[i + 1:j]) + '</i>')
                i = j + 1
                continue
        out.append(html.escape(c, quote=False))
        i += 1
    return ''.join(out)


def wrapcode(line, width=108):
    if len(line) <= width:
        return [line]
    ind = len(line) - len(line.lstrip())
    pieces = textwrap.wrap(line, width=width, subsequent_indent=' ' * (ind + 2),
                           break_long_words=True, break_on_hyphens=False,
                           drop_whitespace=False) or ['']
    return pieces


def codeblock(lines, numbered=False, start=1):
    rows, st = [], S['codeln'] if numbered else S['code']
    for k, ln in enumerate(lines):
        for piece in wrapcode(ln.rstrip('\n'), 112 if numbered else 104):
            txt = html.escape(clean(piece).replace('\t', '    '), quote=False) or '&nbsp;'
            if numbered:
                rows.append([Paragraph('<font color="#a9a194">%4d</font>' % (start + k),
                                       st), Paragraph(txt, st)])
            else:
                rows.append([Paragraph(txt, st)])
    if not rows:
        return []
    if numbered:
        t = Table(rows, colWidths=[12 * mm, CW - 12 * mm - 4 * mm])
    else:
        t = Table(rows, colWidths=[CW - 4 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODEBG),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 0.4), ('BOTTOMPADDING', (0, 0), (-1, -1), 0.4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBEFORE', (0, 0), (0, -1), 1.6, ACC),
    ]))
    return [Spacer(1, 3), t, Spacer(1, 5)]


def mdtable(block):
    rows = []
    for ln in block:
        cells = [c.strip() for c in ln.strip().strip('|').split('|')]
        if all(re.fullmatch(r':?-{2,}:?', c or '-') for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return []
    ncol = max(len(r) for r in rows)
    rows = [r + [''] * (ncol - len(r)) for r in rows]
    data = [[Paragraph(inline(c), S['th'] if i == 0 else S['tc']) for c in r]
            for i, r in enumerate(rows)]
    w0 = CW / ncol
    widths = [w0] * ncol
    if ncol > 2:
        widths[0] = w0 * 1.25
        rest = (CW - widths[0]) / (ncol - 1)
        widths[1:] = [rest] * (ncol - 1)
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), INK),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PAPER]),
        ('GRID', (0, 0), (-1, -1), 0.4, RULE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2.6), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.6),
    ]))
    return [Spacer(1, 4), t, Spacer(1, 7)]


class H(Paragraph):
    """Heading that registers itself with the TOC."""
    def __init__(self, text, style, level, key):
        Paragraph.__init__(self, text, style)
        self._lvl, self._key, self._raw = level, key, re.sub(r'<[^>]+>', '', text)

    def draw(self):
        Paragraph.draw(self)
        self.canv.bookmarkPage(self._key)
        self.canv.addOutlineEntry(self._raw[:90], self._key, self._lvl, 0)


_uid = [0]


def key():
    _uid[0] += 1
    return 'k%d' % _uid[0]


def md2flow(text, base=0, toc_depth=2):
    """Markdown -> flowables. base shifts heading levels for TOC nesting."""
    F = []
    lines = text.split('\n')
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i]
        st = ln.strip()

        if st.startswith('```'):
            j = i + 1
            buf = []
            while j < n and not lines[j].strip().startswith('```'):
                buf.append(lines[j]); j += 1
            F += codeblock(buf)
            i = j + 1
            continue

        if (st.startswith('|') and i + 1 < n
                and re.match(r'^\s*\|[\s:|-]+\|\s*$', lines[i + 1])):
            j = i
            blk = []
            while j < n and lines[j].strip().startswith('|'):
                blk.append(lines[j]); j += 1
            F += mdtable(blk)
            i = j
            continue

        if re.fullmatch(r'(-{3,}|\*{3,}|_{3,})', st):
            F.append(Spacer(1, 3))
            F.append(HRFlowable(width='100%', thickness=0.7, color=RULE))
            F.append(Spacer(1, 5))
            i += 1
            continue

        m = re.match(r'^(#{1,6})\s+(.*)$', st)
        if m:
            lvl = len(m.group(1))
            txt = inline(m.group(2))
            sty = S['h1'] if lvl == 1 else S['h2'] if lvl == 2 else S['h3'] if lvl == 3 else S['h4']
            tl = base + min(lvl, 3) - 1
            if lvl <= toc_depth:
                F.append(H(txt, sty, tl, key()))
            else:
                F.append(Paragraph(txt, sty))
            i += 1
            continue

        if st.startswith('>'):
            buf = []
            while i < n and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip().lstrip('>').strip()); i += 1
            F.append(Paragraph(inline(' '.join(buf)), S['quote']))
            continue

        m = re.match(r'^(\s*)[-*+]\s+(.*)$', ln)
        if m:
            deep = len(m.group(1)) >= 2
            body = m.group(2)
            cb = re.match(r'^\[([ xX])\]\s*(.*)$', body)
            bullet = '\u00b7'
            if cb:
                bullet = '[x]' if cb.group(1).lower() == 'x' else '[&nbsp;]'
                body = cb.group(2)
            F.append(Paragraph(inline(body), S['li2'] if deep else S['li'],
                               bulletText=bullet))
            i += 1
            continue

        m = re.match(r'^(\s*)(\d+)[.)]\s+(.*)$', ln)
        if m:
            F.append(Paragraph(inline(m.group(3)), S['li'],
                               bulletText=m.group(2) + '.'))
            i += 1
            continue

        if not st:
            i += 1
            continue

        buf = [st]
        i += 1
        while i < n:
            s2 = lines[i].strip()
            if (not s2 or s2.startswith(('#', '>', '|', '```'))
                    or re.match(r'^\s*([-*+]|\d+[.)])\s+', lines[i])
                    or re.fullmatch(r'(-{3,}|\*{3,}|_{3,})', s2)):
                break
            buf.append(s2); i += 1
        F.append(Paragraph(inline(' '.join(buf)), S['p']))
    return F


def picture(path, caption, maxh=205 * mm):
    # embed the downscaled JPEG twin if one exists: the 5 MB source PNGs are
    # far above print resolution and quadrupled the file size for no gain
    alt = os.path.join(ROOT, 'build/pdfimg',
                       os.path.basename(path).replace('.png', '.jpg'))
    if os.path.exists(alt):
        path = alt
    im = PILImage.open(path)
    w, h = im.size
    sc = min(CW / w, maxh / h)
    out = [Spacer(1, 4), RLImage(path, w * sc, h * sc)]
    if caption:
        out.append(Paragraph(esc(caption), S['cap']))
    out.append(Spacer(1, 7))
    return out


def part_page(num, title, blurb):
    return [PageBreak(),
            Spacer(1, 52 * mm),
            Paragraph('PART %s' % num, S['partn']),
            Spacer(1, 3),
            H(esc(title), S['part'], 0, key()),
            Spacer(1, 5),
            HRFlowable(width='42%', thickness=2.4, color=ACC, hAlign='LEFT'),
            Spacer(1, 9),
            Paragraph(esc(blurb), ParagraphStyle('pb', parent=S['p'], fontSize=10,
                                                 leading=15, textColor=SOFT)),
            PageBreak()]


def doc_section(title, path, note=None, toc_depth=2):
    F = [PageBreak(), H(esc(title), S['h1'], 1, key())]
    F.append(Paragraph('<font face="MN" size="7.4" color="#6e675d">source: %s</font>'
                       % esc(os.path.relpath(path, ROOT)), S['p']))
    if note:
        F.append(Paragraph('<i>%s</i>' % esc(note), S['quote']))
    F.append(HRFlowable(width='100%', thickness=0.7, color=RULE))
    F.append(Spacer(1, 6))
    F += md2flow(open(path, encoding='utf-8').read(), base=2, toc_depth=toc_depth)
    return F


def code_section(title, path, note=None):
    src = open(path, encoding='utf-8').read().split('\n')
    F = [PageBreak(), H(esc(title), S['h2'], 1, key())]
    F.append(Paragraph('<font face="MN" size="7.4" color="#6e675d">%s &nbsp;&nbsp;'
                       '%d lines &nbsp;&nbsp; %d bytes</font>'
                       % (esc(os.path.relpath(path, ROOT)), len(src),
                          os.path.getsize(path)), S['p']))
    if note:
        F.append(Paragraph('<i>%s</i>' % esc(note), S['quote']))
    F.append(Spacer(1, 4))
    CH = 130
    for s0 in range(0, len(src), CH):
        F += codeblock(src[s0:s0 + CH], numbered=True, start=s0 + 1)
    return F


# ───────────────────────────── page furniture
def page_bg(c, d):
    c.saveState()
    c.setFillColor(colors.white)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)
    pn = c.getPageNumber()
    if pn > 1:
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        c.line(LM, PH - TM + 6 * mm, PW - RM, PH - TM + 6 * mm)
        c.setFont('DJ', 6.6)
        c.setFillColor(SOFT)
        c.drawString(LM, PH - TM + 7.6 * mm,
                     'MONARCH  \u00b7  PREMIUM 2D MOTION EDIT ENGINE  \u00b7  '
                     'STICKMAN STYLE B')
        c.drawRightString(PW - RM, PH - TM + 7.6 * mm, 'v4.1')
        c.line(LM, BM - 4 * mm, PW - RM, BM - 4 * mm)
        c.setFont('DJ-B', 7.6)
        c.setFillColor(INK)
        c.drawRightString(PW - RM, BM - 9 * mm, str(pn))
        c.setFont('DJ', 6.6)
        c.setFillColor(SOFT)
        c.drawString(LM, BM - 9 * mm, 'stickman_money_37s_v9.mp4  \u00b7  '
                                      'sha256 30a5f761d3f14ad6')
    c.restoreState()


class Doc(BaseDocTemplate):
    """Headings notify the TOC here; the canvas has no notify() of its own."""
    def afterFlowable(self, f):
        if isinstance(f, H):
            self.notify('TOCEntry',
                        (f._lvl, f._raw, self.page, f._key))


def build():
    doc = Doc(OUT, pagesize=A4, leftMargin=LM, rightMargin=RM,
              topMargin=TM, bottomMargin=BM,
              title='Monarch - Premium 2D Motion Edit Engine (Complete Dossier)',
              author='Monarch YT Automation', subject='Stickman Style B')
    frame = Frame(LM, BM, CW, PH - TM - BM, id='n', leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=page_bg)])

    st = []

    # ── cover
    st += [Spacer(1, 38 * mm),
           Paragraph('MONARCH', ParagraphStyle('x', parent=S['cover_s'], fontSize=13,
                                               textColor=ACC, fontName='DJ-B')),
           Spacer(1, 6),
           Paragraph('PREMIUM 2D<br/>MOTION EDIT ENGINE', S['cover_t']),
           Spacer(1, 7),
           Paragraph('Complete Dossier \u00b7 Stickman Style B \u00b7 v4.1', S['cover_s']),
           Spacer(1, 9),
           HRFlowable(width='38%', thickness=2.2, color=ACC, hAlign='CENTER'),
           Spacer(1, 9),
           Paragraph('Every document, every measured defect, every fix, every '
                     'constant and every line of source produced while building '
                     'the 37-second vertical explainer, the 16:9 episode and the '
                     'four SHADE-era shorts (POWER v1, SHADE v2, IZZAT 90 s, IZZAT v2 75 s) '
                     '\u2014 compiled verbatim.',
                     ParagraphStyle('cb', parent=S['cover_s'], fontSize=9.6,
                                    leading=14.5))]
    meta = [['FINAL DELIVERABLE', 'stickman_money_37s_v9.mp4'],
            ['FORMAT', '1080 x 1920  \u00b7  30 fps  \u00b7  37.00 s exact  \u00b7  H.264 High@4.0'],
            ['AUDIO', 'AAC-LC 192 kbps 48 kHz stereo  \u00b7  -11.7 LUFS  \u00b7  TP -0.4 dBFS'],
            ['SIZE / HASH', '11,292,519 bytes  \u00b7  sha256 30a5f761d3f14ad6'],
            ['BUILD LINEAGE', 'v2 \u2192 v4 \u2192 v5 \u2192 v6 \u2192 v7 \u2192 v8 \u2192 v9'],
            ['DOCUMENTED DEFECTS', '23 root-caused, fixed and numerically verified'],
            ['SCOPE RULE', 'ADDITIVE ONLY \u2014 Style A image-compile pipeline untouched'],
            ['EPISODE 16:9', 'stickman_wide_episode_full.mp4 \u00b7 263.5 s \u00b7 34 scenes \u00b7 ledger 24\u201338'],
            ['POWER v1 (42 s)', 'stickman_power_42s.mp4 \u00b7 sha256 4c5a5c79c4408386 \u00b7 18/18 gates \u00b7 ledger 39\u201345'],
            ['SHADE v2 (42 s)', 'shade_power_42s.mp4 \u00b7 sha256 3a0de99bc85e1caa \u00b7 18/18 gates \u00b7 ledger 46\u201349'],
            ['IZZAT (90 s)', 'shade_respect_90s.mp4 \u00b7 2700 f \u00b7 sha256 f3d0f1a21ec59b00 \u00b7 18/18 gates \u00b7 ledger 50\u201356'],
            ['IZZAT v2 (75 s)', 'shade_respect_v2.mp4 \u00b7 2256 f \u00b7 md5 8d91be52ab969e0b23f21bf6bab0df85 \u00b7 19/19 gates \u00b7 ledger 57\u201362']]
    mt = Table([[Paragraph('<b>%s</b>' % esc(a), S['tc']), Paragraph(esc(b), S['tc'])]
                for a, b in meta], colWidths=[42 * mm, CW - 42 * mm])
    mt.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, RULE),
        ('BACKGROUND', (0, 0), (0, -1), PAPER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    st += [Spacer(1, 12 * mm), mt, PageBreak()]

    # ── contents
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle('t0', fontName='DJ-B', fontSize=10.6, leading=17,
                       textColor=ACC, spaceBefore=8),
        ParagraphStyle('t1', fontName='DJ-B', fontSize=8.6, leading=13,
                       leftIndent=9, textColor=INK),
        ParagraphStyle('t2', fontName='DJ', fontSize=8, leading=11.6,
                       leftIndent=20, textColor=colors.HexColor('#45413b')),
        ParagraphStyle('t3', fontName='DJ', fontSize=7.4, leading=10.6,
                       leftIndent=32, textColor=SOFT)]
    st += [Paragraph('CONTENTS', S['h1']),
           HRFlowable(width='100%', thickness=1.4, color=ACC),
           Spacer(1, 7), toc]

    # ── PART I
    st += part_page('I', 'THE SKILL',
                    'The transferable skill document: style router, the complete '
                    'mistake ledger with root causes and numeric proof, the 3D '
                    'character rig, the forensic method, platform laws, the audio '
                    'engine, the QA gate and the ten laws.')
    st += doc_section('Skill: Premium 2D Motion Edit Engine (v3.0)',
                      f'{ROOT}/MONARCH_SKILL_MOTION_EDIT.md',
                      'This is the file to add to the Monarch repo. Purely additive.',
                      toc_depth=2)

    # ── PART II
    st += part_page('II', 'THE FORENSIC AUDIT',
                    'What measuring the delivered file actually found. Eighteen '
                    'defects across three severity tiers, each with the measurement '
                    'that exposed it and the fix that closed it.')
    st += doc_section('Forensic Audit of v7', f'{ROOT}/FORENSIC_AUDIT_V7.md',
                      'Produced by decoding the delivered mp4 and measuring it. '
                      'Nothing here was judged by eye.')

    # ── PART III
    st += part_page('III', 'BUILD NOTES',
                    'The chronological engineering record, v4 through v9. Each pass '
                    'lists what changed, why, and the before/after numbers that '
                    'prove it worked.')
    for t, f, nt in (
            ('v4 \u2014 Density Pass', 'VIDEO_V4_NOTES.md',
             'The build the client rejected for being over-stuffed.'),
            ('v5 \u2014 Clean Pass', 'VIDEO_V5_NOTES.md',
             'Locked vertical grid, ASMR engine, approved direction.'),
            ('v6 \u2014 Shaded Character', 'VIDEO_V6_NOTES.md',
             'Two-pass silhouette, scalloped-polygon fingers, eroded shading mask.'),
            ('v7 \u2014 Real Human Rig (3D)', 'VIDEO_V7_NOTES.md',
             'The reversed foot fix and the move from paper doll to 3D skeleton.'),
            ('v8 \u2014 Forensic Fix Pass', 'VIDEO_V8_NOTES.md',
             'Safe area, contrast, de-strobe, stereo width, spectral rebalance.'),
            ('v9 \u2014 Final Polish', 'VIDEO_V9_NOTES.md',
             'Prop micro-float, kinetic emphasis, CTA sheen, subsurface warmth.')):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            st += doc_section(t, p, nt, toc_depth=3)

    # ── PART IV
    st += part_page('IV', 'THE REPRODUCTION BIBLE',
                    'The Tier-0 reconstruction manual carried forward from the v4 '
                    'era: every constant, every coordinate, every synth parameter, '
                    'every ffmpeg command. Reproduced verbatim.')
    for t, f, nt in (
            ('Character Specification', 'CHARACTER_SPEC.md',
             'Superseded in places by the v7 3D rig in Part I, retained verbatim.'),
            ('Master Prompt V4 \u2014 Verified Edition', 'MASTER_PROMPT_V4.md',
             'The most complete of the four master-prompt snapshots. V1-V3 are '
             'earlier states of this same document and remain in the workspace.')):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            st += doc_section(t, p, nt, toc_depth=2)

    # ── PART V
    st += part_page('V', 'SOURCE CODE',
                    'The complete, running v9 source. Three files produce the film: '
                    'the character renderer, the scene renderer, and the audio '
                    'engine. Listed in full with line numbers.')
    for t, f, nt in (
            ('toon.py \u2014 3D Character Renderer', 'src/toon.py',
             'The 3D skeleton, perspective projection, depth sorting, shading '
             'stack, scalloped-polygon hands, poses and expressions.'),
            ('clean.py \u2014 Scene Renderer', 'src/clean.py',
             'Layout grid, six scenes, transitions, sub-pixel camera, typography, '
             'secondary-motion wrapper, shard entry point.'),
            ('make_asmr.py \u2014 Audio Engine', 'src/make_asmr.py',
             'Dual-bus synthesis, the silk plate, 248 events, M/S widening, '
             'loudness-hole pad swells.'),
            ('toonsheet.py \u2014 Character Sheet Builder', 'src/toonsheet.py', None),
            ('makepdf.py \u2014 This Document\u2019s Builder', 'src/makepdf.py', None)):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            st += code_section(t, p, nt)

    # ── PART VI
    st += part_page('VI', 'VISUAL REFERENCE',
                    'The character sheet, the QA contact sheets and the pixel-zoom '
                    'inspections that drove the craft fixes.')
    st.append(PageBreak())
    st.append(H('Visual Reference Plates', S['h1'], 1, key()))
    for f, cap in (
            ('toon_character_sheet.png',
             'Plate 1 \u2014 Character sheet: front views, expression studies, '
             'full-body pose studies (v9 shaded 3D rig).'),
            ('_probe.png',
             'Plate 2 \u2014 QA contact sheet: one frame from each of the six '
             'scenes of the final v9 render.'),
            ('_zoom.png',
             'Plate 3 \u2014 1.35x pixel-zoom inspection used to find the hand, '
             'knee, shoe and prop-depth defects.'),
            ('_t.png',
             'Plate 4 \u2014 Pose strip: ten poses rendered side by side to verify '
             'the 3D rig, the 3/4 yaw and the corrected foot.'),
            ('_cta.png',
             'Plate 5 \u2014 CTA pill at 2x with the travelling specular sheen.'),
            ('character_sheet_1_identity.png', 'Plate 6 \u2014 Identity sheet (legacy).'),
            ('character_sheet_2_expressions.png',
             'Plate 7 \u2014 Expression sheet (legacy).'),
            ('character_sheet_3_poses.png', 'Plate 8 \u2014 Pose sheet (legacy).'),
            ('character_sheet_4_cast.png', 'Plate 9 \u2014 Cast sheet (legacy).')):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            st += picture(p, cap)

    # ── PART VII
    st += part_page('VII', 'DATA APPENDIX',
                    'The ASMR event ledger and the build manifest, reproduced as '
                    'data so the bed and the build can be audited event by event.')
    st.append(PageBreak())
    st.append(H('ASMR Event Ledger', S['h1'], 1, key()))
    st.append(Paragraph('Every cue in the bed: time, tag, gain, pan. 248 events.',
                        S['p']))
    led = os.path.join(ROOT, 'ASMR_EVENT_LEDGER.csv')
    if os.path.exists(led):
        rows = [r.split(',') for r in open(led).read().strip().split('\n')]
        hdr, body = rows[0], rows[1:]
        CHUNK = 46
        for s0 in range(0, len(body), CHUNK):
            data = [[Paragraph('<b>%s</b>' % esc(c), S['th']) for c in hdr]]
            data += [[Paragraph(esc(c), S['tc']) for c in r]
                     for r in body[s0:s0 + CHUNK]]
            t = Table(data, colWidths=[CW / len(hdr)] * len(hdr), repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), INK),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PAPER]),
                ('GRID', (0, 0), (-1, -1), 0.3, RULE),
                ('TOPPADDING', (0, 0), (-1, -1), 1.6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.6),
            ]))
            st += [t, Spacer(1, 5)]

    bm = os.path.join(ROOT, 'BUILD_MANIFEST.json')
    if os.path.exists(bm):
        st.append(PageBreak())
        st.append(H('Build Manifest', S['h1'], 1, key()))
        st += codeblock(open(bm).read().split('\n'))


    # ── PART VIII  (added v4.1)
    st += part_page('VIII', 'LONG-FORM 16:9',
                    'The second skill document and the two 16:9 builds: the 53 s '
                    'persistence hook and the 263.5 s episode "The Slowest Predator" '
                    '(34 scenes, 5 acts). Ledger 24\u201338.')
    for t, f, nt in (
            ('Skill: Long-form 16:9 Engine', 'MONARCH_SKILL_LONGFORM_16x9.md',
             'Continues the ledger of Part I into wide-frame, multi-minute work.'),
            ('Script \u2014 Persistence Hook', 'SCRIPT_HOOK_PERSISTENCE.md', None),
            ('Wide Hook \u2014 Build Notes (53 s)', 'VIDEO_WIDE_NOTES.md',
             'The first 16:9 build: layout, pacing and the hook mux chain.'),
            ('Episode \u2014 Build Notes (263.5 s)', 'VIDEO_EPISODE_NOTES.md',
             'Shards, bed, mux, gate; the master that must be regenerated from source.')):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            st += doc_section(t, p, nt, toc_depth=2)

    # ── PART IX  (added v4.1)
    st += part_page('IX', 'THE SHADE-ERA SHORTS',
                    'Three vertical shorts on the same engine, each measured against '
                    'the same eighteen gates: POWER v1 (42 s, stickman), SHADE v2 (the '
                    'same film remade with the user\u2019s hooded hero and the hybrid '
                    'charcoal/paper look) and IZZAT (90 s, cinematic layer, new voice). '
                    'Ledger 39\u201356 is in Part I, \u00a713\u2013\u00a715.')
    for t, f, nt in (
            ('Script \u2014 "How to Become a Powerful Man"', 'SCRIPT_POWER.md', None),
            ('POWER v1 \u2014 Build Notes (42 s)', 'VIDEO_POWER_NOTES.md',
             'Voice fitted by cutting pauses, picture cut to the voice, 18 gates.'),
            ('SHADE v2 \u2014 Build Notes (42 s remake)', 'VIDEO_SHADE_NOTES.md',
             'SHADE on the toon rig, the diagonal seam as a character, re-derived sliver gate.'),
            ('Script \u2014 "Log Aapki Izzat Kyun Nahi Karte"', 'SCRIPT_RESPECT.md', None),
            ('IZZAT \u2014 Build Notes (90 s)', 'VIDEO_RESPECT_NOTES.md',
             'Nine chapters, cinematic layer, voice-01, four builds to 18/18.')):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            st += doc_section(t, p, nt, toc_depth=3)

    # ── PART X  (added v4.1)
    st += part_page('X', 'SOURCE CODE II',
                    'Everything that runs after v9: the 16:9 renderers and mux, the '
                    'POWER pipeline, the SHADE character and hybrid layer, the IZZAT '
                    'renderer with its cinematic layer, the audio beds, the mux chains, '
                    'the gates and the build scripts. Listed in full with line numbers.')
    for t, f, nt in (
            ('wide.py \u2014 16:9 Hook Renderer', 'src/wide.py', None),
            ('wide_full.py \u2014 Episode Renderer', 'src/wide_full.py', None),
            ('wide_audio.py / wide_full_audio.py \u2014 16:9 Beds', 'src/wide_audio.py', None),
            ('wide_full_audio.py', 'src/wide_full_audio.py', None),
            ('mux_full.sh / mux_hook.sh / gate_full.py', 'src/mux_full.sh', None),
            ('mux_hook.sh', 'src/mux_hook.sh', None),
            ('gate_full.py', 'src/gate_full.py', None),
            ('vo_fit.py \u2014 Voice Fitting (pause cap, no atempo)', 'src/vo_fit.py', None),
            ('timeline_power.py \u2014 Picture Cut to the Voice', 'src/timeline_power.py', None),
            ('power.py \u2014 POWER v1 Renderer', 'src/power.py',
             'caption_fit, blends, camera bounds, six scenes.'),
            ('make_asmr_power.py \u2014 POWER Bed', 'src/make_asmr_power.py', None),
            ('mux_power.sh \u2014 Locked Mix Chain', 'src/mux_power.sh', None),
            ('gate_power.py \u2014 The Eighteen Gates', 'src/gate_power.py', None),
            ('shade.py \u2014 SHADE Character on the 3D Rig', 'src/shade.py', None),
            ('hybrid.py \u2014 Charcoal/Paper Seam', 'src/hybrid.py', None),
            ('power2.py \u2014 SHADE v2 Renderer', 'src/power2.py', None),
            ('gate_shade.py \u2014 Re-derived Sliver Gate', 'src/gate_shade.py', None),
            ('timeline_respect.py \u2014 90 s Timeline', 'src/timeline_respect.py', None),
            ('respect.py \u2014 IZZAT Renderer (cinematic layer)', 'src/respect.py',
             'dolly, parallax silhouettes, shafts, dust, nine scenes, bounded sprite cache.'),
            ('make_asmr_respect.py \u2014 IZZAT Bed', 'src/make_asmr_respect.py', None),
            ('mux_respect.sh \u2014 Mix Chain with De-esser and Padded VO Bus', 'src/mux_respect.sh', None),
            ('gate_respect.py', 'src/gate_respect.py', None),
            ('build_all.sh / build_power.sh / build_shade.sh / build_respect.sh', 'build_all.sh', None),
            ('build_power.sh', 'build_power.sh', None),
            ('build_shade.sh', 'build_shade.sh', None),
            ('build_respect.sh', 'build_respect.sh', None),
            ('build_respect_resume.sh', 'build_respect_resume.sh', None),
            ('timeline_respect2.py \u2014 IZZAT v2: the Voice Sets the Length (75.19 s)', 'src/timeline_respect2.py', None),
            ('respect2.py \u2014 IZZAT v2 Shots, 15-kind Transition Library and PLAN', 'src/respect2.py',
             '16 insert compositions over the v1 scenes, 33 shots, quintic ease, soft-edge wedge, window CLI.'),
            ('make_asmr_respect2.py \u2014 IZZAT v2 Bed (no floor, one cue per kind)', 'src/make_asmr_respect2.py', None),
            ('mux_respect2.sh \u2014 v1 Chain + VO Low-mid Trims', 'src/mux_respect2.sh', None),
            ('gate_respect2.py \u2014 Nineteen Gates (shot-frame jerk + per-transition cap)', 'src/gate_respect2.py', None),
            ('patch_windows.py / splice_windows.py \u2014 Window Re-render and Streaming Splice', 'src/patch_windows.py', None),
            ('splice_windows.py', 'src/splice_windows.py', None),
            ('build_respect2.sh / build_respect2_b.sh / finish_respect2.sh', 'build_respect2.sh', None),
            ('build_respect2_b.sh', 'build_respect2_b.sh', None),
            ('finish_respect2.sh', 'finish_respect2.sh', None)):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            st += code_section(t, p, nt)

    # ── PART XI  (added v4.1)
    st += part_page('XI', 'VISUAL REFERENCE II',
                    'SHADE character sheet, the SHADE v2, IZZAT and IZZAT v2 contact sheets '
                    'generated from the delivered files.')
    st.append(PageBreak())
    st.append(H('Visual Reference Plates II', S['h1'], 1, key()))
    for f, cap in (
            ('shade_character_sheet.png',
             'Plate 10 \u2014 SHADE character sheet: the user\u2019s hooded black-suit hero on the toon 3D rig.'),
            ('shade_scene1_preview.png',
             'Plate 11 \u2014 Hybrid look preview: charcoal/paper seam, extruded type, SHADE.'),
            ('shade_power_contact.png',
             'Plate 12 \u2014 SHADE v2 contact sheet from the delivered shade_power_42s.mp4.'),
            ('shade_respect_contact.png',
             'Plate 13 \u2014 IZZAT contact sheet: 30 stills, 0.6\u201385.5 s, from the delivered shade_respect_90s.mp4.'),
            ('shade_respect_v2_contact.png',
             'Plate 14 \u2014 IZZAT v2 contact sheet: the 33 shot mid-frames of the delivered shade_respect_v2.mp4 (75.19 s).')):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            st += picture(p, cap)

    # ── PART XII  (added v4.1)
    st += part_page('XII', 'DATA APPENDIX II',
                    'The POWER and IZZAT ASMR ledgers, the POWER build manifest, and the '
                    'session record with the resume state \u2014 the exact stop point of '
                    'the project.')
    for title, led, blurb in (
            ('ASMR Event Ledger \u2014 POWER', 'ASMR_POWER_LEDGER.csv',
             'Every cue in the POWER bed (shared by SHADE v2): time, tag, gain, pan.'),
            ('ASMR Event Ledger \u2014 IZZAT', 'ASMR_RESPECT_LEDGER.csv',
             'Every cue in the IZZAT bed, including the tail air added in build 3.')):
        lp = os.path.join(ROOT, led)
        if not os.path.exists(lp):
            continue
        st.append(PageBreak())
        st.append(H(title, S['h1'], 1, key()))
        rows = [r.split(',') for r in open(lp).read().strip().split('\n')]
        hdr, body = rows[0], rows[1:]
        st.append(Paragraph(esc(blurb) + ' %d events.' % len(body), S['p']))
        CHUNK = 46
        for s0 in range(0, len(body), CHUNK):
            data = [[Paragraph('<b>%s</b>' % esc(c), S['th']) for c in hdr]]
            data += [[Paragraph(esc(c), S['tc']) for c in r[:len(hdr)]] +
                     [Paragraph('', S['tc'])] * max(0, len(hdr) - len(r))
                     for r in body[s0:s0 + CHUNK]]
            t = Table(data, colWidths=[CW / len(hdr)] * len(hdr), repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), INK),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PAPER]),
                ('GRID', (0, 0), (-1, -1), 0.3, RULE),
                ('TOPPADDING', (0, 0), (-1, -1), 1.6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.6),
            ]))
            st += [t, Spacer(1, 5)]
    bmp = os.path.join(ROOT, 'BUILD_MANIFEST_POWER.json')
    if os.path.exists(bmp):
        st.append(PageBreak())
        st.append(H('Build Manifest \u2014 POWER', S['h1'], 1, key()))
        st += codeblock(open(bmp).read().split('\n'))
    for t, f, nt in (
            ('Session Record \u2014 Monarch Stickman Animation', 'MONARCH_STICKMAN_ANIMATION_SESSION_LOG.md',
             'Prompt \u2192 response \u2192 result, turn by turn, with every id, hash and dead end.'),
            ('Resume State', 'RESUME_STATE.md',
             'The exact stop point; read after the session record.')):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            st += doc_section(t, p, nt, toc_depth=2)

    st.append(PageBreak())
    st.append(H('Colophon', S['h1'], 1, key()))
    st += md2flow(
        'This dossier was generated directly from the workspace by '
        '`src/makepdf.py`, which parses each Markdown document and source file '
        'and lays it out with ReportLab. Nothing was retyped or summarised: every '
        'document appears exactly as it exists on disk.\n\n'
        '**Final deliverable** `stickman_money_37s_v9.mp4` \u2014 1080x1920, 30 fps, '
        '37.00 s exact, 11,292,519 bytes, sha256 prefix `30a5f761d3f14ad6`, '
        '-11.7 LUFS integrated, true peak -0.4 dBFS, decode clean.\n\n'
        '**Later deliverables (v4.1 of this dossier)** \u2014 `stickman_wide_episode_full.mp4` '
        '(16:9, 263.5 s), `stickman_wide_hook_53s.mp4`, `stickman_power_42s.mp4` '
        '(sha256 prefix `4c5a5c79c4408386`), `shade_power_42s.mp4` (`3a0de99bc85e1caa`) and '
        '`shade_respect_90s.mp4` (2700 frames, 90.000 s, `f3d0f1a21ec59b00`), every one of them '
        'passing the same eighteen measured gates. The ledger now runs 1\u201356.\n\n'
        '**Scope rule** \u2014 everything here is ADDITIVE. The existing Monarch '
        'stickman pipeline (generate still images, compile, apply zoom and '
        'transitions and captions, export) is untouched and remains the default '
        'route. The engine documented here is a sibling option, selected only when '
        'a brief demands true character animation or frame-exact voiceover sync.',
        base=2)

    doc.multiBuild(st)
    print('wrote', OUT, os.path.getsize(OUT), 'bytes')


if __name__ == '__main__':
    build()

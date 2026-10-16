#!/usr/bin/env python3
"""Subset the included OFL Montserrat font into real Three.js glyph outlines.
The text is extruded geometry, not a flat caption with a faux-3D shadow.
"""
import json
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
ROOT=Path(__file__).resolve().parents[1]
font=TTFont(ROOT/'assets/fonts/Montserrat-VF.ttf')
if 'fvar' in font:font=instantiateVariableFont(font,{'wght':600},inplace=False)
glyphs=font.getGlyphSet();cmap=font.getBestCmap();scale=1000/font['head'].unitsPerEm
class Pen(BasePen):
 def __init__(self):super().__init__(glyphs);self.parts=[]
 def p(self,xy):return ' '.join(str(round(n*scale,3)) for n in xy)
 def _moveTo(self,p):self.parts+=['m',self.p(p)]
 def _lineTo(self,p):self.parts+=['l',self.p(p)]
 def _qCurveToOne(self,c,p):self.parts+=['q',self.p(p),self.p(c)]
 def _curveToOne(self,c1,c2,p):self.parts+=['b',self.p(p),self.p(c1),self.p(c2)]
 def _closePath(self):pass
 def _endPath(self):pass
result={}
for char in sorted(set('KAANTAHI. ?')):
 name=cmap[ord(char)];g=glyphs[name];pen=Pen();g.draw(pen);bounds=BoundsPen(glyphs);g.draw(bounds);bb=bounds.bounds or (0,0,0,0)
 result[char]={'ha':font['hmtx'][name][0]*scale,'x_min':bb[0]*scale,'x_max':bb[2]*scale,'o':' '.join(pen.parts)}
obj={'glyphs':result,'familyName':'Montserrat Cinema 600','ascender':font['hhea'].ascent*scale,'descender':font['hhea'].descent*scale,'underlinePosition':-100,'underlineThickness':50,'boundingBox':{'xMin':-100,'xMax':1500,'yMin':-300,'yMax':1200},'resolution':1000,'original_font_information':'Montserrat OFL1.1; subset/600-weight conversion for KAANTA Cinema v4. Included font license remains applicable.'}
(ROOT/'assets/fonts/Montserrat-Cinema.typeface.json').write_text(json.dumps(obj,separators=(',',':'))+'\n')
print('Exported glyph outlines:',','.join(result))

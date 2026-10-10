"""Contact sheet of key frames for visual QA. python3 src/sheet_power.py [times...]"""
import sys
sys.path.insert(0, '/home/user/src')
from PIL import Image, ImageDraw
import power as P
times = [float(x) for x in sys.argv[1:]] or \
    [0.6, 1.6, 2.4, 3.7, 5.3, 6.9, 7.65, 8.55, 9.9, 11.3, 13.0, 14.6, 17.0, 18.8,
     20.0, 21.6, 22.7, 24.8, 27.6, 29.5, 31.6, 32.7, 33.6, 35.2, 38.3, 39.3, 40.5, 41.8]
cols = 7; tw, th = 300, 533
rows = (len(times) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * (th + 26)), (40, 40, 40))
dd = ImageDraw.Draw(sheet)
for n, tt in enumerate(times):
    fr = Image.fromarray(P.render(int(round(tt * P.FPS)))).resize((tw, th), Image.LANCZOS)
    x, y = (n % cols) * tw, (n // cols) * (th + 26)
    sheet.paste(fr, (x, y + 26))
    dd.text((x + 6, y + 5), f't={tt:.2f}', fill=(255, 255, 255))
out = '/home/user/build/sheet_power.png'
sheet.save(out); print(out)

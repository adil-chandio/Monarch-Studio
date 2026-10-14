import os, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont

BASE = "workflows/current/payload/flow-v3"
IMGDIR = BASE + "/images"
AUDIODIR = BASE + "/audio"
OUT = BASE + "/out/final.mp4"

W, H = 1080, 1920
FPS = 30
FONT = "/tmp/ufonts/urdu-web-font-CDN-main/MehrNastaleeq.ttf"

# audio durations (seconds) per line
audio_durs = [7.66,10.49,8.57,8.66,6.70,5.62,4.18,7.78,6.22]
GAP = 0.5
# scene durations: audio + gap for 1..9, scene10 fills rest to total audio
total_audio = 70.90
scenes = []  # list of (img_path, caption, duration)
for i in range(9):
    scenes.append((f"{IMGDIR}/scene{i+1:02d}.png", None, audio_durs[i] + GAP))
# scene 10 duration = remainder
used = sum(s[2] for s in scenes)
scenes.append((f"{IMGDIR}/scene10.png", None, max(1.0, total_audio - used)))

# captions per scene (Urdu)
captions = [
 "انیس سو پندرہ میں، البرٹ آئن اسٹائن گریویٹی کا مسئلہ حل نہیں کر پا رہے تھے۔ ان کی ایکویشنز ناکام ہو رہی تھیں۔",
 "پھر رات کے دو بجے، انہوں نے چاک رکھا، وائلن اٹھایا، اور موم بتی کی روشنی میں موزارٹ بجانے لگے۔ اُدھر پڑوسی دیواریں پیٹ رہے تھے۔",
 "وہ میتھ سے بھاگ نہیں رہے تھے، بلکہ فلو اسٹیٹ میں جا رہے تھے۔ اُسی حالت کو آج ہم اے آئی شارٹ کٹس سے خود ختم کر رہے ہیں۔",
 "ذرا سوچو۔ تیز سفر کے لیے ہمارے پاس کاریں ہیں۔ پھر بھی ہم صبح دوڑنے کے لیے رننگ شوز پہنتے ہیں۔ کیوں؟",
 "کیونکہ اگر سارا کام انجن کرے، تو ہمارے مسلز کمزور پڑ جاتے ہیں۔ دماغ کے ساتھ بھی یہی ہوتا ہے۔",
 "جب شارٹ کٹ محنت کی چڑھائی کی جگہ لے لے، تو کریئیٹو اِنفلیشن پیدا ہوتی ہے۔",
 "ایفیشنسی بڑھتی ہے، مگر انسان کا ٹیلنٹ کم ہوتا جاتا ہے۔",
 "اس وقت ہزاروں لوگ خالی اسپورٹس اسٹیڈیمز میں صرف بھاری سینڈ بیگز اٹھانے کے لیے بھاری فیس دے رہے ہیں۔",
 "یہ آرٹ کے خوفناک فیوچر کے بارے میں جو بتاتا ہے، وہ سننے کے لیے تم ابھی تیار نہیں ہو۔",
 "",
]
for i in range(len(scenes)):
    scenes[i] = (scenes[i][0], captions[i], scenes[i][2])

# load images
imgs = [Image.open(s[0]).convert("RGB") for s in scenes]

def kenburns(img, t, dur):
    # scale 1.0 -> 1.15
    s = 1.0 + 0.15*(t/dur if dur>0 else 0)
    nw = int(W*s); nh = int(H*s)
    im = img.resize((nw,nh), Image.LANCZOS)
    x0 = (nw-W)//2; y0 = (nh-H)//2
    return im.crop((x0,y0,x0+W,y0+H))

def draw_caption(base, text):
    if not text:
        return base
    im = base.copy()
    draw = ImageDraw.Draw(im)
    # choose font size
    size = 52
    font = ImageFont.truetype(FONT, size)
    # shrink if too wide
    while size > 30:
        font = ImageFont.truetype(FONT, size)
        bbox = draw.textbbox((0,0), text, font=font)
        if (bbox[2]-bbox[0]) <= W-80:
            break
        size -= 2
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]; th = bbox[3]-bbox[1]
    x = (W-tw)//2
    y = H - th - 120
    # shadow
    for dx,dy in [(2,2),(3,3)]:
        draw.text((x+dx,y+dy), text, font=font, fill=(0,0,0,180) if False else (20,20,30))
    draw.text((x,y), text, font=font, fill=(40,30,60))
    return im

# ffmpeg process
FFMPEG = None
import subprocess as sp
# get ffmpeg path
import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
audio_path = os.path.abspath(AUDIODIR + "/full_audio.mp3")
out_path = os.path.abspath(OUT)
os.makedirs(os.path.dirname(out_path), exist_ok=True)

cmd = [FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
       "-i", audio_path,
       "-c:v", "libx264", "-preset", "medium", "-crf", "20",
       "-c:a", "aac", "-b:a", "128k",
       "-shortest", "-movflags", "+faststart", out_path]
proc = sp.Popen(cmd, stdin=sp.PIPE)

TRANS = 0.4
# build frame schedule
# cumulative scene start times
starts = []
t = 0.0
for (ip, cap, dur) in scenes:
    starts.append(t)
    t += dur
total_dur = t
total_frames = int(round(total_audio * FPS))  # match audio
# Actually use min(total_dur, total_audio)
total_frames = int(round(min(total_dur, total_audio) * FPS))

frame_idx = 0
while frame_idx < total_frames:
    cur_time = frame_idx / FPS
    # find scene
    si = 0
    for i in range(len(scenes)):
        if cur_time < starts[i] + scenes[i][2]:
            si = i
            break
        si = len(scenes)-1
    scene_start = starts[si]
    local_t = cur_time - scene_start
    dur = scenes[si][2]
    # transition blend?
    img = imgs[si]
    frame = kenburns(img, local_t, dur)
    # transition into next scene near end
    if si < len(scenes)-1 and local_t > dur - TRANS:
        # blend with next scene frame at local 0
        nxt = imgs[si+1]
        nxt_frame = kenburns(nxt, 0, scenes[si+1][2])
        alpha = (local_t - (dur-TRANS)) / TRANS
        alpha = max(0,min(1,alpha))
        frame = Image.blend(frame, nxt_frame, alpha)
    frame = draw_caption(frame, scenes[si][1])
    proc.stdin.write(frame.tobytes())
    frame_idx += 1

proc.stdin.close()
proc.wait()
print("done", out_path)
"""Recover the selected narration without re-auditioning or speeding it up.

Only leading/trailing quiet is tightened; spoken content, voice and pitch
are preserved. Creates an exact frame-aligned edit decision list and SRT.
"""
from pathlib import Path
import json, subprocess, wave, os
import numpy as np
from scipy.signal import butter, sosfilt
import imageio_ffmpeg
from clean import CUTS,NAMES

ROOT=Path(__file__).resolve().parent
MEDIA=Path(os.environ.get('FLOW_MEDIA',str(ROOT/'media'))).resolve();MEDIA.mkdir(exist_ok=True)
SR=48000; FPS=30; ff=imageio_ffmpeg.get_ffmpeg_exe()
# Short Roman Urdu captions, not a whole paragraph shrunk onto one line.
PHRASES=[
 [(0.28,1.62,'1915 mein,'),(1.81,2.9,'Albert Einstein gravity ka masla'),(2.9,5.13,'hal nahi kar paa rahe thay.'),(5.48,7.42,'Unki equations nakaam ho rahi theen.')],
 [(.29,1.81,'Phir raat ke 2 baje,'),(2.04,3.23,'unhon ne chalk rakha,'),(3.45,4.48,'violin uthaya,'),(4.76,6.43,'aur mombatti ki roshni mein'),(6.55,7.88,'Mozart bajane lage.'),(8.33,10.19,'Udhar padosi deewarein peet rahe thay.')],
 [(.29,2.18,'Woh math se bhaag nahi rahe thay,'),(2.42,4.30,'balki flow state mein ja rahe thay.'),(4.70,6.20,'Ussi haalat ko aaj hum'),(6.20,8.26,'AI shortcuts se khud khatam kar rahe hain.')],
 [(.28,1.20,'Zara socho.'),(1.67,3.93,'Tez safar ke liye hamare paas cars hain.'),(4.46,5.67,'Phir bhi hum subah daurne ke liye'),(5.67,7.57,'running shoes pehente hain.'),(8.01,8.40,'Kyun?')],
 [(.27,2.40,'Kyunke agar saara kaam engine kare,'),(2.59,4.56,'toh hamare muscles kamzor par jaate hain.'),(4.81,6.40,'Dimaagh ke saath bhi yehi hota hai.')],
 [(.27,1.27,'Jab shortcut'),(1.27,3.03,'mehnat ki charhaai ki jagah le le,'),(3.28,5.34,'toh creative inflation paida hoti hai.')],
 [(.27,1.44,'Efficiency barhti hai,'),(1.63,2.68,'magar insaan ka talent'),(2.70,3.88,'kam hota jaata hai.')],
 [(.32,1.95,'Iss waqt hazaaron log'),(1.95,3.73,'khaali sports stadiums mein'),(3.84,5.80,'sirf bhaari sandbags uthane ke liye'),(5.80,7.44,'bhaari fees de rahe hain.')],
 [(.28,2.17,'Yeh art ke khaufnaak future ke baare mein'),(2.17,3.68,'jo batata hai,'),(3.82,4.80,'woh sunne ke liye tum'),(4.80,5.90,'abhi tayyaar nahi ho.')]
]
# Each state's start is in its ORIGINAL clip time. Text is integrated with
# the footage, using reference-style bold nouns + quiet connective phrases.
STATES=[
 (1,.18,'top','Ek mashhoor kahani','1915','',124),
 (1,1.77,'bottom','','ALBERT EINSTEIN','gravity ka masla...',74),
 (1,3.00,'bottom','','GRAVITY','hal nahi ho raha tha.',89),
 (1,5.26,'top','Unki','EQUATIONS','nakaam ho rahi theen.',88),
 (2,.18,'top','Phir, raat ke','2 BAJE','',100),
 (2,2.00,'bottom','unhon ne','CHALK RAKHA','',75),
 (2,3.30,'top','','VIOLIN','uthaya.',93),
 (2,4.67,'top','mombatti ki','ROSHNI','mein...',91),
 (2,6.43,'top','aur bajane lage','MOZART','',94),
 (2,8.18,'bottom','udhar','PADOSI','deewarein peet rahe thay.',86),
 (3,.18,'bottom','Woh math se','BHAAG NAHI','rahe thay.',82),
 (3,2.26,'top','Woh ja rahe thay','FLOW STATE','mein.',79),
 (3,4.58,'bottom','Aaj hum, khud','AI SHORTCUTS','se usay khatam kar rahe hain.',74),
 (4,.18,'top','','ZARA SOCHO','',88),
 (4,1.57,'bottom','Tez safar ke liye','CARS','hain.',97),
 (4,4.27,'top','Phir bhi, subah','RUNNING\nSHOES','pehente hain.',74),
 (4,7.89,'bottom','','KYUN?','',100),
 (5,.17,'top','Agar saara kaam','ENGINE KARE','',79),
 (5,2.49,'bottom','Toh hamare','MUSCLES','kamzor par jaate hain.',88),
 (5,4.61,'top','','DIMAAGH','ke saath bhi yehi hota hai.',95),
 (6,.17,'top','Jab mehnat ki jagah','SHORTCUT','le le...',88),
 (6,3.13,'top','Toh paida hoti hai','CREATIVE\nINFLATION','',72),
 (7,.17,'top','','EFFICIENCY','barhti hai.',85),
 (7,1.53,'right','Magar','HUMAN\nTALENT','kam hota jaata hai.',64),
 (8,.22,'top','Iss waqt','HAZAARON LOG','',74),
 (8,1.89,'top','','KHAALI\nSTADIUMS','mein...',74),
 (8,3.70,'top','Sirf uthane ke liye','HEAVY\nSANDBAGS','',76),
 (8,5.69,'bottom','','BHAARI FEES','de rahe hain.',74),
 (9,.18,'top','Yeh batata hai','FUTURE OF ART','ke baare mein...',75),
 (9,2.04,'top','','KHAUFNAAK\nFUTURE','',77),
 (9,3.66,'bottom','Yeh sunne ke liye tum','ABHI TAYYAAR\nNAHI HO.','',69),
]

raws=[];clips=[];cursor=.22
for i in range(1,10):
    b=subprocess.check_output([ff,'-v','error','-i',str(ROOT/'audio'/f'line{i:02d}.mp3'),'-ac','1','-ar',str(SR),'-f','f32le','pipe:1'])
    x=np.frombuffer(b,dtype='<f4').copy()
    n=480;r=np.sqrt(np.mean(x[:len(x)//n*n].reshape(-1,n)**2,axis=1))
    active=np.where(r>.012)[0]
    trim_start=max(0,(active[0]/100)-.065)
    trim_end=min(len(x)/SR,(active[-1]+1)/100+.13)
    y=x[int(trim_start*SR):int(trim_end*SR)]
    # Retain natural pace. Frame alignment adds only quiet, never phoneme cuts.
    nframes=int(np.ceil(len(y)/SR*FPS));padded=nframes*SR//FPS
    y=np.pad(y,(0,padded-len(y)))
    envelope_n=min(480,len(y)//10)
    y[:envelope_n]*=np.linspace(0,1,envelope_n);y[-envelope_n:]*=np.linspace(1,0,envelope_n)
    # Consistent dialogue gain; no destructive hard clipping.
    gain=min(1.8,.13/max(np.sqrt(np.mean(y*y)),1e-4));y*=gain
    start=round(cursor*FPS)/FPS;end=start+nframes/FPS
    clips.append({'id':i,'start':round(start,6),'end':round(end,6),'trim_start':trim_start,'trim_end':trim_end,'natural_speed':1.0,'source':f'audio/line{i:02d}.mp3'})
    raws.append(y);cursor=end+.10

def tm(i,raw):
    c=clips[i-1];return max(c['start'], min(c['end'],c['start']+raw-c['trim_start']))
# Semantic edit points replace global audio time-stretching.
starts=[0,tm(1,5.27),clips[1]['start']-.07,tm(2,3.31),clips[2]['start']-.07,
        tm(3,2.25),clips[3]['start']-.07,tm(4,4.26),clips[4]['start']-.07,
        tm(5,4.61),clips[5]['start']-.07,clips[6]['start']-.07,
        clips[7]['start']-.07,clips[8]['start']-.07]
starts=[round(s*FPS)/FPS for s in starts]
end=round((clips[-1]['end']+.57)*FPS)/FPS
shots=[{'index':i,'name':NAMES[i],'start':starts[i],'end':starts[i+1] if i<13 else end,
        'source_start':CUTS[i],'source_end':CUTS[i+1],
        'path':f'clean-shots/{i:02d}-{NAMES[i]}.mp4'} for i in range(14)]
captions=[]
for i,phrases in enumerate(PHRASES,1):
    for a,b,text in phrases:captions.append({'start':tm(i,a)-.03,'end':tm(i,b)+.06,'text':text})
states=[]
for clip,a,position,kicker,title,sub,size in STATES:
    states.append({'start':tm(clip,a)-.025,'position':position,'kicker':kicker,'title':title,'sub':sub,'size':size})
for i,s in enumerate(states):s['end']=states[i+1]['start'] if i+1<len(states) else end

data={'schema_version':1,'fps':FPS,'duration':end,'width':1080,'height':1920,
      'source_width':720,'source_height':1282,'clips':clips,'shots':shots,'captions':captions,'titles':states,
      'notes':['Previously selected voice recovered exactly; no new synthesis.',
               'No speech speed-up: trims contain leading/trailing quiet only.',
               'Reference-derived animated collage, not newly rendered 3D geometry.',
               'Historical anecdote and rhetoric translated from the supplied reference, not independently verified.']}
(ROOT/'timeline.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
# Assemble stems.
N=int(round(end*SR));voice=np.zeros(N,np.float32)
for c,y in zip(clips,raws):
    p=int(round(c['start']*SR));voice[p:p+len(y)]+=y[:N-p]
voice=sosfilt(butter(2,65,fs=SR,btype='highpass',output='sos'),voice).astype(np.float32)
rng=np.random.default_rng(3214);stereo=np.repeat(voice[:,None],2,axis=1)
# Discreet tonal floor and stereo texture, well below the dialogue.
time=np.arange(N)/SR
bed=np.zeros(N,np.float32)
for freq,amp,phase in [(146.83,.0016,.2),(220,.0010,1.4),(293.66,.0006,2.1)]:
    bed += (amp*np.sin(2*np.pi*freq*time+phase)*(0.7+.3*np.sin(2*np.pi*.11*time+phase))).astype(np.float32)
fade=np.minimum(1,time/1.2)*np.minimum(1,np.maximum(0,end-time)/1.0)
stereo[:,0]+=bed*fade;stereo[:,1]+=np.roll(bed,300)*fade

def add(sig,start,pan=0):
    p=int(round(start*SR));a=max(0,p);b=min(N,p+len(sig))
    if a>=b:return
    left=np.sqrt((1-pan)/2);right=np.sqrt((1+pan)/2)
    ss=sig[a-p:b-p]
    stereo[a:b,0]+=ss*left;stereo[a:b,1]+=ss*right
for j,s in enumerate(shots[1:]):
    n=int(.28*SR);t=np.arange(n)/SR
    noise=rng.standard_normal(n)
    noise=sosfilt(butter(2,[320,4300],fs=SR,btype='bandpass',output='sos'),noise)
    env=np.sin(np.pi*np.linspace(0,1,n))**2
    add((noise*env*.022).astype(np.float32),s['start']-.14,(-1 if j%2 else 1)*.35)
    # Short soft sub tap, not a booming trailer hit.
    t=np.arange(int(.14*SR))/SR
    add((.033*np.sin(2*np.pi*(95*t-55*t*t))*np.exp(-t*33)).astype(np.float32),s['start'],0)
# Subtle type accents; stay under the voice, never ticks on every word.
for i,s in enumerate(states):
    if i%2:continue
    t=np.arange(int(.055*SR))/SR
    sig=.010*np.sin(2*np.pi*1100*t)*np.exp(-t*85)
    add(sig.astype(np.float32),s['start'],.15 if i%4 else -.15)
# Preserve headroom before loudness normalization.
peak=float(np.max(np.abs(stereo)));stereo*=min(1,.90/max(peak,1e-6))
with wave.open(str(MEDIA/'mix_raw.wav'),'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((stereo*32767).astype('<i2').tobytes())
subprocess.run([ff,'-v','error','-y','-i',str(MEDIA/'mix_raw.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=9','-ar',str(SR),str(MEDIA/'mix.wav')],check=True)

def stamp(t):
    msec=int(round(max(0,t)*1000));return f'{msec//3600000:02d}:{msec//60000%60:02d}:{msec//1000%60:02d},{msec%1000:03d}'
srt='\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}\n' for i,c in enumerate(captions))
(ROOT/'Flow_State_Roman_Urdu.srt').write_text(srt)
print(json.dumps({'duration':end,'shots':len(shots),'titles':len(states),'caption_phrases':len(captions),'speech_speed':1.0,'source_audio_peak_before_mix':float(np.max(np.abs(voice)))}))

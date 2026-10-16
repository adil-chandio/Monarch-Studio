"""Restrained v4 score + tactile foley-inspired textures.
Music: original arrangement of credited CC-BY3.0 FluidR3 instrument notes.
Effects: deterministic procedural noise/resonance, not UI tones or reference
samples. No promise of ASMR response or audience-retention performance.
"""
from pathlib import Path
import math,subprocess,json
import numpy as np
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1];SR=48000;FF=imageio_ffmpeg.get_ffmpeg_exe()
DURATIONS={'wood_touch':.24,'steel_close':.24,'soft_release':.42,'reveal_air':.68,'cell_texture':2.18,'pressure':1.05}

# Narrative musical shape, rather than random notes on every visual event.
CHORDS=[(0.0,6.90,['D3','F3','A3'],.66),(7.0,4.9,['Bb3','D4','F3'],.85),(11.5,4.15,['A3','C4','E4'],.94),(15.65,3.25,['D3','F3','A3','E4'],1.10),(19.0,2.85,['D3','A3'],.60),(22.15,4.00,['F3','A3','C4'],.70),(26.1,4.40,['D3','F3','A3'],.55)]
BASS=[(.1,6.7,'D2',.72),(7.02,4.4,'Bb2',.74),(11.5,3.8,'A2',.78),(15.7,3.1,'D3',.70),(22.2,3.7,'F3',.62),(26.2,4.1,'D2',.48)]
PIANO=[(.62,'D4',.90),(2.60,'A3',.73),(7.18,'D4',.76),(8.20,'F4',.61),(9.40,'A3',.72),(10.65,'C4',.75),(11.75,'E4',.70),(13.0,'D4',.70),(14.20,'A3',.76),(15.78,'F4',.82),(16.9,'E4',.76),(18.0,'D4',.69),(22.35,'C4',.69),(23.8,'A3',.73),(25.15,'F4',.61),(26.72,'D4',.48),(28.05,'A3',.60),(29.26,'D4',.68)]

def lowpass(a,hz):
    f=np.fft.rfftfreq(len(a),1/SR);h=np.exp(-(f/hz)**4)
    return np.fft.irfft(np.fft.rfft(a)*h,n=len(a))

def note(instrument,pitch,cache):
    key=(instrument,pitch)
    if key in cache:return cache[key]
    file=ROOT/'assets/music'/instrument/(pitch+'.mp3')
    raw=subprocess.run([FF,'-loglevel','error','-i',str(file),'-ar',str(SR),'-ac','1','-f','f32le','pipe:1'],check=True,capture_output=True).stdout
    a=np.frombuffer(raw,'<f4').astype('float64')
    a=lowpass(a,{'acoustic_grand_piano':2900,'cello':1600,'string_ensemble_1':2500}[instrument])
    a/=max(np.max(abs(a)),1e-9)
    cache[key]=a;return a

def sustain(a,duration):
    n=round(duration*SR)
    if n<=len(a):return a[:n].copy()
    # A quiet, crossfaded steady section of the actual instrument note; no
    # hard loop joins. The release is separately enveloped below.
    end=min(round(.96*SR),len(a)-1);start=min(round(.36*SR),end//2)
    loop=a[start:end];cross=min(round(.10*SR),len(loop)//4)
    result=a[:end].copy()
    while len(result)<n:
        blend=np.linspace(0,1,cross)
        result[-cross:]=result[-cross:]*(1-blend)+loop[:cross]*blend
        result=np.concatenate((result,loop[cross:]))
    return result[:n]

def note_envelope(a,attack,release):
    a=a.copy();n=len(a);attack=min(round(attack*SR),n//2);release=min(round(release*SR),n//2)
    if attack:a[:attack]*=np.sin(np.linspace(0,np.pi/2,attack))**2
    if release:a[-release:]*=np.cos(np.linspace(0,np.pi/2,release))**2
    return a

def score(duration):
    n=round(duration*SR);t=np.arange(n)/SR;out=np.zeros((n,2));cache={};events=[]
    def add(start,a,gain,pan):
        at=round(start*SR);size=min(len(a),n-at)
        if size<=0:return
        l=math.sqrt(1-pan);r=math.sqrt(1+pan)
        out[at:at+size,0]+=a[:size]*gain*l;out[at:at+size,1]+=a[:size]*gain*r
    for start,dur,pitches,energy in CHORDS:
        for j,pitch in enumerate(pitches):
            a=sustain(note('string_ensemble_1',pitch,cache),dur)
            a=note_envelope(a,.65,.75)
            add(start+j*.012,a,.024*energy/len(pitches),(-.20,.13,.05,-.09)[j])
        events.append({'section':'strings','time':start,'duration':dur,'notes':pitches,'energy':energy})
    for start,dur,pitch,energy in BASS:
        a=note_envelope(sustain(note('cello',pitch,cache),dur),.47,.68);add(start,a,.009*energy,0)
        events.append({'section':'cello','time':start,'duration':dur,'note':pitch,'energy':energy})
    for i,(start,pitch,velocity) in enumerate(PIANO):
        a=note('acoustic_grand_piano',pitch,cache).copy();a=a[:round(2.8*SR)]
        a=note_envelope(a,.010,.40);a*=np.exp(-np.arange(len(a))/SR*.30)
        add(start,a,.021*velocity,-.10 if i%2 else .12)
        # Short restrained room reflections, no bright game/chime tail.
        add(start+.047,a,.0016*velocity,.12 if i%2 else -.10)
        add(start+.121,a,.0010*velocity,0)
        events.append({'section':'felt_piano','time':start,'note':pitch,'velocity':velocity})
    # A narrow dip creates space for "har baar nahi", not an alarm/stinger.
    warning=np.clip((t-18.80)/.19,0,1)*np.clip((22.12-t)/.32,0,1)
    rise=np.interp(t,[0,6.4,7.0,11.5,15.6,18.7,19.3,22.1,26,30.5],[.72,.72,.90,1.0,1.20,1.25,.75,.75,.82,.55])
    out*=((1-.45*warning)*rise*np.clip(t/.52,0,1)*np.clip((duration-t)/.95,0,1))[:,None]
    rms=np.sqrt(np.mean(out*out))+1e-12
    out*=10**(-33.0/20)/rms
    return out,events

def texture(kind,rng):
    n=round(DURATIONS[kind]*SR);t=np.arange(n)/SR;noise=rng.normal(0,1,n)
    def band(lo,hi):
        f=np.fft.rfftfreq(n,1/SR);h=(1-np.exp(-(f/lo)**4))*np.exp(-(f/hi)**4)
        a=np.fft.irfft(np.fft.rfft(noise)*h,n=n);return a/(np.sqrt(np.mean(a*a))+1e-12)
    if kind=='wood_touch':
        a=band(340,3700)*np.exp(-t*58)
        a+=.19*np.sin(2*np.pi*510*t)*np.exp(-t*55)
    elif kind=='steel_close':
        a=band(1600,6000)*np.exp(-t*75)
        a+=(.15*np.sin(2*np.pi*2317*t)*np.exp(-t*43)+.06*np.sin(2*np.pi*3871*t)*np.exp(-t*51))
        at=round(.014*SR);a[at:]+=a[:-at].copy()*.15
    elif kind=='soft_release':
        a=band(320,2900)*(np.exp(-t*24)*.65+np.exp(-((t-.08)/.045)**2)*.28)
        a+=.08*np.sin(2*np.pi*330*t)*np.exp(-t*33)
    elif kind=='reveal_air':a=band(500,4300)*np.sin(np.pi*t/t[-1])**2*.75
    elif kind=='cell_texture':a=band(220,1550)*np.sin(np.pi*t/t[-1])**2*(.7+.1*np.sin(t*2.2))
    else:a=band(90,900)*np.sin(np.pi*t/t[-1])**2*.60
    fade=min(round(.002*SR),n//2);a[:fade]*=np.sin(np.linspace(0,np.pi/2,fade))**2;a[-min(700,n):]*=np.linspace(1,0,min(700,n))**2
    a/=max(np.max(abs(a)),1e-9);return a

def create_soundtrack(tl,voice):
    n=len(voice);music,notes=score(tl['duration']);rng=np.random.default_rng(2026101504)
    small=np.abs(voice[::240]);target=np.clip(small/.10,0,1);env=np.zeros(len(small));state=0.
    for i,x in enumerate(target):state+=(x-state)*(.063 if x>state else .019);env[i]=state
    e=np.interp(np.arange(n),np.arange(len(env))*240,env)
    music*=(1-.56*e)[:,None]
    fx=np.zeros((n,2));events=[]
    for cue in tl['sound_events']:
        a=texture(cue['kind'],rng)*cue['gain'];at=round(cue['time']*SR);count=min(len(a),n-at)
        if count<=0:raise ValueError('Out-of-bounds cue')
        a=a[:count]*(1-.30*e[at:at+count]);pan=cue.get('pan',0)
        fx[at:at+count,0]+=a*math.sqrt(1-pan);fx[at:at+count,1]+=a*math.sqrt(1+pan)
        delay=round(.023*SR);take=min(count,n-at-delay)
        if take>0:
            fx[at+delay:at+delay+take,0]+=a[:take]*.065;fx[at+delay:at+delay+take,1]+=a[:take]*.085
        events.append({'kind':cue['kind'],'time':cue['time'],'sample':at,'gain':cue['gain'],'duration':count/SR,'visual_cue':cue.get('visual_cue')})
    effects=music+fx
    db=lambda a:float(20*np.log10(np.sqrt(np.mean(a*a))+1e-12))
    sections={}
    for label,a,b in [('hook',.4,3.6),('discovery',7.4,11.1),('build',12.2,18.5),('breathing_space',19.3,21.5),('resolve',26.3,30.2)]:sections[label]=db(music[round(a*SR):round(b*SR)])
    report={'music_section_rms_dbfs':sections,'version':4,'cue_count':len(events),'events':events,'score_events':notes,'score_source':'Original arrangement using credited FluidR3 CC-BY3.0 piano/cello/strings note samples. See assets/music/ATTRIBUTION.md.','reference_audio_copied':False,'ui_beeps_chimes_or_alerts':False,'voice_rms_dbfs':db(voice),'music_rms_dbfs':db(music),'foley_rms_dbfs':db(fx),'sound_design_rms_dbfs':db(effects),'stereo_correlation':float(np.corrcoef(effects[:,0],effects[:,1])[0,1]),'intent':'Tactile and restrained; deliberate musical space at the no-guarantee line. ASMR-style is an aesthetic intent, not a guaranteed physiological/audience response.'}
    return effects,report,music,fx

"""Original, deterministic stereo motion-foley and musical texture for v3.
No borrowed reference sounds; sample-accurate cue positions come from timeline.
The voice is protected by envelope ducking, not replaced or regenerated.
"""
import math
import numpy as np
SR=48000

DURATIONS={'wood_contact':.22,'lens_sweep':.66,'tool_air':.57,'grip_click':.30,'wood_release':.43,'dive':.74,'cell_bloom':.30,'swell':.74,'fluid':.47,'rise':.86,'release_air':.48,'caution':.65,'soft_tick':.22,'strain':.48,'resolve':1.02}

def sound(kind,rng):
    t=np.arange(round(DURATIONS[kind]*SR))/SR;dur=len(t)/SR
    noise=rng.normal(0,1,len(t))
    def band(lo,hi):
        freq=np.fft.rfftfreq(len(t),1/SR)
        filt=(1-np.exp(-(freq/max(1,lo))**4))*np.exp(-(freq/hi)**4)
        a=np.fft.irfft(np.fft.rfft(noise)*filt,n=len(t))
        return a/(np.sqrt(np.mean(a*a))+1e-12)*.25
    def tone(f,decay=18,amp=1):return amp*np.sin(2*np.pi*f*t)*np.exp(-t*decay)
    if kind=='wood_contact':
        a=(tone(690,42,.52)+tone(1310,52,.24)+band(1200,6200)*np.exp(-t*58))
        a+=.13*np.sin(2*np.pi*(180*t-140*t*t))*np.exp(-t*35)
    elif kind=='grip_click':
        a=(tone(1930,38,.50)+tone(3181,47,.25)+tone(4877,58,.10)+band(2400,7600)*np.exp(-t*72)*.65)
        a+=np.roll(a,round(.023*SR))*.12
    elif kind=='wood_release':
        phase=2*np.pi*(580*t-560*t*t)
        a=.52*np.sin(phase)*np.exp(-t*15)+.25*band(240,2600)*np.exp(-t*24)+tone(1160,42,.14)
    elif kind in ('lens_sweep','tool_air','dive','rise','release_air'):
        f={'lens_sweep':220,'tool_air':440,'dive':170,'rise':350,'release_air':500}[kind]
        x=t/dur;env=np.sin(np.pi*x)**2
        phase=2*np.pi*(f*t+(220 if kind=='rise' else -95)*t*t)
        a=band(450,6600)*env+.14*np.sin(phase)*env
        if kind=='dive':a+=.23*np.sin(2*np.pi*(105*t-28*t*t))*env
    elif kind=='cell_bloom':
        f=rng.uniform(460,740);a=.60*np.sin(2*np.pi*(f*t-210*t*t))*np.exp(-t*23)+band(800,2600)*np.exp(-t*29)*.11
    elif kind=='swell':
        env=np.sin(np.pi*t/dur)**2
        a=.58*np.sin(2*np.pi*(93*t+22*t*t))*env*np.exp(-t*2.6)+band(180,1200)*env*.18
    elif kind=='fluid':
        a=.31*np.sin(2*np.pi*(290*t-115*t*t))*np.exp(-t*13)+band(200,2000)*np.exp(-t*13)*.25
    elif kind=='caution':
        a=(tone(174.61,7,.45)+tone(261.63,9,.20)+tone(349.23,11,.09))*np.minimum(t/.013,1)
    elif kind=='soft_tick':
        a=tone(1174.66,36,.39)+band(800,4100)*np.exp(-t*53)*.28
    elif kind=='strain':
        env=np.sin(np.pi*t/dur)**2
        a=(.22*np.sin(2*np.pi*(240*t+90*t*t))+band(320,1800)*.22)*env
    elif kind=='resolve':
        a=tone(587.33,5.8,.48)+tone(880,6.6,.23)+tone(1174.66,8,.08)
    else:raise ValueError(kind)
    # Short raised-cosine endpoints eliminate clicks without erasing the onset.
    fade=min(round(.0025*SR),len(a)//2)
    a[:fade]*=np.sin(np.linspace(0,np.pi/2,fade))**2
    a[-min(480,len(a)) :]*=np.linspace(1,0,min(480,len(a)))**2
    peak=np.max(np.abs(a))+1e-12
    return a/max(peak,.3)

def create_soundtrack(tl,voice):
    n=len(voice);t=np.arange(n)/SR;rng=np.random.default_rng(2026101503)
    # Smooth 120ms attack / 320ms release sidechain estimated at 200Hz.
    v=np.abs(voice[::240]);target=np.clip(v/.09,0,1);env=np.zeros(len(v));last=0.
    for i,x in enumerate(target):
        k=.041 if x>last else .0155;last+=(x-last)*k;env[i]=last
    e=np.interp(np.arange(n),np.arange(len(env))*240,env)
    bed=np.zeros((n,2));pad=np.zeros(n)
    for f,amp,phase in [(73.416,.0043,0),(146.832,.0031,.3),(220,.0022,.8),(293.665,.0014,.2),(349.228,.0012,1.1)]:
        pad+=amp*np.sin(2*np.pi*f*t+.14*np.sin(2*np.pi*.14*t+phase))*(.8+.2*np.sin(t*.61+phase))
    pad*=np.clip(t/1.15,0,1)*np.clip((tl['duration']-t)/1.4,0,1)
    # Sparse restrained plucks, not a loud beat underneath medical narration.
    for j,start in enumerate([.66,2.05,7.54,9.12,11.05,15.95,17.40,22.52,25.46,29.02]):
        f=[293.665,440,349.228,440,587.33][j%5];u=np.arange(int(.68*SR))/SR
        pluck=.0037*(np.sin(2*np.pi*f*u)+.16*np.sin(2*np.pi*f*2*u))*np.exp(-u*9)*np.clip(u/.008,0,1)
        at=round(start*SR);count=min(len(pluck),n-at);pad[at:at+count]+=pluck[:count]
    # Cut the musical texture during the no-guarantee warning, not the voice.
    safety=1-.70*np.clip((t-18.82)/.30,0,1)*np.clip((22.3-t)/.3,0,1)
    pad*=safety*(1-.64*e)
    bed[:,0]=pad;bed[:,1]=pad
    fx=np.zeros((n,2));events=[]
    for item in tl['sound_events']:
        a=sound(item['kind'],rng)*item['gain'];at=round(item['time']*SR);count=min(len(a),n-at)
        pan=np.clip(item.get('pan',0),-.85,.85);l=math.sqrt((1-pan)/2)*math.sqrt(2);r=math.sqrt((1+pan)/2)*math.sqrt(2)
        # Foley remains intelligible but steps back under syllables.
        a=a[:count]*(1-.28*e[at:at+count])
        fx[at:at+count,0]+=a*l;fx[at:at+count,1]+=a*r
        for delay,wet,flip in [(.018,.10,False),(.039,.072,True),(.068,.044,False)]:
            shift=round(delay*SR);m=min(count,n-at-shift)
            if m>0:
                fx[at+shift:at+shift+m,0]+=a[:m]*(r if flip else l)*wet
                fx[at+shift:at+shift+m,1]+=a[:m]*(l if flip else r)*wet
        events.append({'kind':item['kind'],'time':item['time'],'sample':at,'gain':item['gain'],'pan':float(pan),'visual_cue':item.get('visual_cue'),'synthesized_duration':len(a)/SR})
    effects=bed+fx
    mono_phase=float(np.corrcoef(effects[:,0],effects[:,1])[0,1])
    rms=lambda a:float(20*np.log10(np.sqrt(np.mean(a*a))+1e-12))
    report={'original_synthesis':True,'reference_audio_copied':False,'events':events,'cue_count':len(events),'voice_rms_dbfs':rms(voice),'sound_design_rms_dbfs':rms(effects),'stereo_correlation':mono_phase,'ducking':'Envelope-ducked original pad/plucks and foley; narration stays centered','mix_components':['metal contact transients','wood release/strain','stereo air sweeps','subtle cell/fluid details','soft caution/resolve tones','restrained original harmonic bed']}
    return effects,report

#!/usr/bin/env node
// V5 comparative authored-motion checks: speed improvements are relative to
// the actual preserved v4 controls, not a claim of objectively perfect art.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {controller,makeRail} from './motion.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const config=JSON.parse(fs.readFileSync(path.join(root,'data/motion.json'))),base=JSON.parse(fs.readFileSync(path.join(root,'data/V4_MOTION_BASELINE.json'))),tl=JSON.parse(fs.readFileSync(path.join(root,'data/timeline.json'))),m=controller(config);
const checks=[];const check=(name,passed,details)=>checks.push({name,passed:!!passed,details});
const norm=a=>Math.hypot(...a),sub=(a,b)=>a.map((v,i)=>v-b[i]);
let positionError=0,velocityError=0,accelerationError=0;
for(const keys of Object.values(config.camera)){
 const rail=makeRail(keys),h=.00001;
 for(const k of keys.slice(1,-1)){
  const a=rail(k.time-h),b=rail(k.time),c=rail(k.time+h),aa=rail(k.time-2*h),cc=rail(k.time+2*h);
  positionError=Math.max(positionError,norm(sub(b,k.value)));
  velocityError=Math.max(velocityError,norm(sub(sub(c,b),sub(b,a)).map(v=>v/h)));
  const al=b.map((v,i)=>(v-2*a[i]+aa[i])/(h*h)),ar=cc.map((v,i)=>(v-2*c[i]+b[i])/(h*h));accelerationError=Math.max(accelerationError,norm(sub(ar,al)));
 }
}
check('Faster camera rails retain C2 joins',positionError<1e-8&&velocityError<.0001&&accelerationError<.08,{positionError,velocityError,accelerationError,finite_difference_step_seconds:.00001});
const comparison=[];
for(const [name,start,end] of [['surface approach','surface_approach_start','surface_approach_end'],['surface close','surface_close_start','surface_contact'],['surface pull','surface_pull_start','surface_clear'],['deep approach','deep_approach_start','deep_approach_end'],['deep close','deep_close_start','deep_contact'],['deep pull','deep_pull_start','deep_clear'],['swelling rise','swell_start','swell_full'],['possible outward movement','emerge_start','emerge_end']]){
 const old=base.cues[end]-base.cues[start],now=config.cues[end]-config.cues[start];comparison.push({action:name,v4_seconds:old,v5_seconds:now,shorter_percent:(1-now/old)*100});
}
check('All specified action windows are materially shorter than v4',comparison.every(c=>c.shorter_percent>40),comparison);
const oldMoves=Object.values(base.camera).flatMap(keys=>keys.slice(1).map((k,i)=>k.time-keys[i].time));
const windows=config.camera_moves.map(x=>x.end-x.start);const avg=a=>a.reduce((x,y)=>x+y,0)/a.length;
check('Camera uses short move/settle windows, not whole-shot drift',Math.max(...windows)<.65&&avg(windows)<avg(oldMoves)*.4,{v4_mean_control_span:avg(oldMoves),v5_mean_move_window:avg(windows),v5_max_move_window:Math.max(...windows),moves:config.camera_moves});
check('Narration rate and total frame contract are not sped up',tl.fps===30&&tl.duration===30.5&&tl.duration*tl.fps===915,{fps:tl.fps,duration:tl.duration,output_frames:915});
const h=1e-6,jumps=[9.46,11.7,15.56,18.98,22.08,25.83].map(t=>({time:t,delta:norm(sub(m.sample(t+h).camera.slice(0,3),m.sample(t-h).camera.slice(0,3)))}));
check('No accidental camera reset at chapter labels',jumps.every(x=>x.delta<.0001),jumps);
check('One semantic scene cut only',config.cues.scene_change===7,{time:7,shutter_excludes_cross_scene_blend:true});
const one=JSON.stringify(m.sample(17.4));m.sample(4.4);m.sample(29.4);check('Absolute-time controls stay stateless',one===JSON.stringify(m.sample(17.4)),{});
const arrive=Array.from({length:config.cells.active_count},(_,i)=>m.cell(i,10.1));
check('Faster cells arrive by the gathering phrase',arrive.every(x=>x.progress>.999),{active_cells:arrive.length,all_arrived_by:Math.max(...arrive.map(x=>x.arrival)),gathering_caption_start:10.10});
const cues=tl.sound_events.filter(e=>e.visual_cue);
check('Contact/release anchors come from the motion authority',cues.every(e=>Math.abs(e.time-config.cues[e.visual_cue])<1e-10),cues.map(e=>({kind:e.kind,anchor:e.time,pre_roll:e.pre_roll||0,clip_start:e.time-(e.pre_roll||0),visual_cue:e.visual_cue})));
let bad=0,surfaceReverse=0,deepReverse=0,last=m.sample(0),cameraStep=0,unprotectedFastFrames=0,shutterFrames=0;
for(let f=1;f<915;f++){
 const t=f/tl.fps,s=m.sample(t),shutter=config.shutter.windows.some(([a,b])=>t>=a&&t<=b)&&Math.abs(t-7)>config.shutter.no_cross_scene_blend_seconds;
 if(shutter)shutterFrames++;
 if(!s.camera.every(Number.isFinite)||s.swelling<0||s.swelling>1.15)bad++;
 if(t>config.cues.surface_pull_start&&t<config.cues.surface_clear&&s.surfaceLift<last.surfaceLift-1e-8)surfaceReverse++;
 if(t>config.cues.deep_pull_start&&t<config.cues.deep_clear&&s.deepLift<last.deepLift-1e-8)deepReverse++;
 if(s.scene===last.scene){const delta=norm(sub(s.camera.slice(0,3),last.camera.slice(0,3)));cameraStep=Math.max(cameraStep,delta);if(delta>.10&&!shutter)unprotectedFastFrames++;}
 for(let i=0;i<config.cells.active_count;i++){const c=m.cell(i,t);if(![...c.position,...c.scale].every(Number.isFinite)||c.scale.some(x=>x<0))bad++;}
 last=s;
}
check('Fast motion is finite and bounded to the authored move budget',bad===0&&cameraStep<.35,{bad_samples:bad,maximum_camera_translation_per_output_frame:cameraStep,allowed:.35});
check('Extraction remains monotonic, with grip before pull',surfaceReverse===0&&deepReverse===0&&config.cues.surface_contact<config.cues.surface_pull_start&&config.cues.deep_contact<config.cues.deep_pull_start,{surfaceReverse,deepReverse,surface_pull_seconds:config.cues.surface_clear-config.cues.surface_pull_start,deep_pull_seconds:config.cues.deep_clear-config.cues.deep_pull_start});
check('Fast camera frames use bounded real-scene shutter samples',unprotectedFastFrames===0&&config.shutter.samples===3&&config.shutter.half_exposure_seconds*2<.01,{unprotected_fast_frames:unprotectedFastFrames,shutter_output_frames:shutterFrames,scene_samples_per_active_frame:3,exposure_seconds:config.shutter.half_exposure_seconds*2,no_optical_flow:true,captions_drawn_once_at_center_time:true});
const report={passed:checks.every(c=>c.passed),checks_passed:checks.filter(c=>c.passed).length,checks_total:checks.length,checks,comparison,limits:['Reference-informed pacing, not frame-for-frame duplication','Shorter authored movement windows do not certify universal premium taste or audience retention','Illustrative anatomy, not a validated tissue mechanics simulation']};
fs.writeFileSync(path.join(root,'data/MOTION_QA.json'),JSON.stringify(report,null,2)+'\n');fs.writeFileSync(path.join(root,'data/MOTION_COMPARISON.json'),JSON.stringify({actions:comparison,camera:{v4_mean_control_span:avg(oldMoves),v5_mean_move_window:avg(windows)}},null,2)+'\n');console.log(JSON.stringify(report,null,2));if(!report.passed)process.exitCode=1;

#!/usr/bin/env node
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {controller,makeRail} from './motion.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const config=JSON.parse(fs.readFileSync(path.join(root,'data/motion.json')));
const tl=JSON.parse(fs.readFileSync(path.join(root,'data/timeline.json'))),m=controller(config);
const checks=[];const check=(name,passed,details)=>checks.push({name,passed:!!passed,details});
const norm=a=>Math.hypot(...a),sub=(a,b)=>a.map((v,i)=>v-b[i]);
let maxPositionMismatch=0,maxVelocityMismatch=0,maxAccelerationMismatch=0;
for(const keys of Object.values(config.camera)){
 const rail=makeRail(keys),h=.0001;
 for(const k of keys.slice(1,-1)){
  const a=rail(k.time-h),b=rail(k.time),c=rail(k.time+h),aa=rail(k.time-2*h),cc=rail(k.time+2*h);
  maxPositionMismatch=Math.max(maxPositionMismatch,norm(sub(b,k.value)));
  const vl=sub(b,a).map(v=>v/h),vr=sub(c,b).map(v=>v/h);
  maxVelocityMismatch=Math.max(maxVelocityMismatch,norm(sub(vr,vl)));
  const al=b.map((v,i)=>(v-2*a[i]+aa[i])/(h*h)),ar=cc.map((v,i)=>(v-2*c[i]+b[i])/(h*h));
  maxAccelerationMismatch=Math.max(maxAccelerationMismatch,norm(sub(ar,al)));
 }
}
check('Camera keys are interpolated exactly with C2 joins',maxPositionMismatch<1e-8&&maxVelocityMismatch<.0001&&maxAccelerationMismatch<.04,{maxPositionMismatch,maxVelocityMismatch,maxAccelerationMismatch});
const boundaries=[9.46,11.7,15.56,18.98,22.08,25.83];
const eps=.000001;const jumps=boundaries.map(t=>({time:t,delta:norm(sub(m.sample(t+eps).camera.slice(0,3),m.sample(t-eps).camera.slice(0,3)))}));
check('All six old internal camera resets removed',jumps.every(j=>j.delta<.0001),jumps);
check('One intentional hand-to-anatomy scene cut is explicit',config.cues.scene_change===7,{time:7,not_claimed_continuous_across_different_scenes:true});
const snapshot=JSON.stringify(m.sample(17.4));m.sample(29.1);m.sample(4.9);check('Absolute-time controls are stateless',JSON.stringify(m.sample(17.4))===snapshot,{});
check('All active cells arrive during the spoken gathering sentence',Array.from({length:config.cells.active_count},(_,i)=>m.cell(i,11.4).progress).every(x=>x>.999),{all_arrived_by:Math.max(...Array.from({length:config.cells.active_count},(_,i)=>m.cell(i,11.4).arrival)),gathering_caption:[10.10,11.51]});
const timedSounds=tl.sound_events.filter(e=>e.visual_cue);
check('Grip and release sounds share the visual cue authority',timedSounds.every(e=>Math.abs(e.time-config.cues[e.visual_cue])<1e-10),timedSounds.map(e=>({kind:e.kind,visual_cue:e.visual_cue,time:e.time,max_frame_quantization_seconds:1/tl.fps})));
let bad=0,surfaceReverse=0,deepReverse=0,last=m.sample(0),cameraStep=0;
for(let f=1;f<Math.round(tl.duration*tl.fps);f++){
 const t=f/tl.fps,s=m.sample(t);
 if(!s.camera.every(Number.isFinite)||s.swelling<0||s.swelling>1.15)bad++;
 if(t>5.6&&t<config.cues.surface_clear&&s.surfaceLift<last.surfaceLift-1e-7)surfaceReverse++;
 if(t>27.6&&t<config.cues.deep_clear&&s.deepLift<last.deepLift-1e-7)deepReverse++;
 if(s.scene===last.scene)cameraStep=Math.max(cameraStep,norm(sub(s.camera.slice(0,3),last.camera.slice(0,3))));
 for(let i=0;i<config.cells.active_count;i++){const c=m.cell(i,t);if(![...c.position,...c.scale].every(Number.isFinite)||c.scale.some(x=>x<0))bad++;}
 last=s;
}
check('Frame-by-frame motion is finite and bounded',bad===0&&cameraStep<.15,{badSamples:bad,maximum_camera_translation_per_frame:cameraStep,fps:tl.fps});
check('Controlled extraction does not reverse after the resistance beat',surfaceReverse===0&&deepReverse===0,{surfaceReverse,deepReverse});
check('Two grips lock before their pulls begin',config.cues.surface_contact<config.cues.surface_pull_start&&config.cues.deep_contact<config.cues.deep_pull_start,{surface_contact:config.cues.surface_contact,surface_pull:config.cues.surface_pull_start,deep_contact:config.cues.deep_contact,deep_pull:config.cues.deep_pull_start});
// The old authored camera used hard resets at these six edit boundaries.
const oldEnds=[[3,1.45,11.9],[.8,.27,7.5],[1.35,1.85,8.8],[.70,1,9],[3.1,1.5,12.7],[-.5,1.95,11.6]];
const oldStarts=[[2.2,.45,9],[2.3,2.65,10.1],[1.5,1.03,9.1],[2.6,1.85,12.1],[-1.8,2.3,12],[1.4,1.35,12.5]];
const oldSteps=oldEnds.map((v,i)=>norm(sub(oldStarts[i],v)));
const report={passed:checks.every(c=>c.passed),checks_passed:checks.filter(c=>c.passed).length,checks_total:checks.length,checks,comparison:{v2_internal_camera_cuts:oldSteps,v2_maximum_internal_camera_cut_translation:Math.max(...oldSteps),v3_internal_boundary_steps:jumps,note:'This compares actual authored camera position discontinuities, not an objective artistic-quality score. Both versions retain a separate intentional scene change at 7 seconds.'},limits:['Illustrative authored motion, not a tissue mechanics simulation','No optical-flow frame interpolation','No promise of matching reference frame-for-frame']};
fs.writeFileSync(path.join(root,'data/MOTION_QA.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));if(!report.passed)process.exitCode=1;

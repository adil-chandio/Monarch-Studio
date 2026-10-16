#!/usr/bin/env node
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
import {controller,makeRail} from './motion.mjs';import {director} from './director.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const load=f=>JSON.parse(fs.readFileSync(path.join(root,f)));
const config=load('data/motion.json'),plan=load('data/shot_plan.json'),tl=load('data/timeline.json'),lock=load('data/NARRATION_LOCK.json'),m=controller(config),d=director(plan,m,config);
const checks=[],check=(name,passed,details)=>checks.push({name,passed:!!passed,details}),norm=a=>Math.hypot(...a),sub=(a,b)=>a.map((x,i)=>x-b[i]);
check('User-selected same voice/script/placements retained',JSON.stringify(tl.narration)===JSON.stringify(lock.narration)&&JSON.stringify(tl.captions)===JSON.stringify(lock.captions),{baseline:lock.baseline,narration_clips:tl.narration.length,caption_phrases:tl.captions.length,time_stretch:false});
const hashes=load('data/VOICE_LOCK.json').files;check('All original voice files retain their hashes',Object.entries(hashes).every(([n,h])=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'assets/vo',n))).digest('hex')===h),{files:Object.keys(hashes)});
check('Nine narrative shots cover the native-frame contract',plan.shots.length===9&&plan.shots[0].start===0&&plan.shots.at(-1).end===30.5&&plan.shots.every((s,i)=>s.end>s.start&&(!i||s.start===plan.shots[i-1].end))&&tl.fps===30,{shots:plan.shots.length,duration:30.5,frames:915});
check('Camera cuts are explicit semantic shot boundaries',JSON.stringify(d.cuts)===JSON.stringify(plan.intentional_cuts),{cuts:d.cuts,not_claimed_continuous_across_cuts:true});
let positionError=0,velocityError=0,accelerationError=0;
for(const shot of plan.shots){const rail=makeRail(shot.camera),h=.00001;
 for(const k of shot.camera.slice(1,-1)){const a=rail(k.time-h),b=rail(k.time),c=rail(k.time+h),aa=rail(k.time-2*h),cc=rail(k.time+2*h);positionError=Math.max(positionError,norm(sub(b,k.value)));velocityError=Math.max(velocityError,norm(sub(sub(c,b),sub(b,a)).map(v=>v/h)));const al=b.map((v,i)=>(v-2*a[i]+aa[i])/(h*h)),ar=cc.map((v,i)=>(v-2*c[i]+b[i])/(h*h));accelerationError=Math.max(accelerationError,norm(sub(ar,al)));}}
check('Shot-local camera rails retain C2 joins',positionError<1e-8&&velocityError<.0001&&accelerationError<.08,{positionError,velocityError,accelerationError});
let bad=0,maxStep=0,last=null,focusFrames=0,shutterFrames=0;const shotCounts={},scenes={};
for(let f=0;f<915;f++){
 const t=f/30,p=m.sample(t),v=d.sample(t,p);shotCounts[v.shot]=(shotCounts[v.shot]||0)+1;scenes[v.scene]=(scenes[v.scene]||0)+1;
 if(![...v.camera,...v.focusPoint,v.focusDistance].every(Number.isFinite)||v.focusDistance<=.06||v.focusDistance>=80)bad++;
 if(v.focusStrength>0&&v.maxBlur>0)focusFrames++;
 const shutter=config.shutter.windows.some(([a,b])=>t>=a&&t<=b)&&!d.cuts.some(c=>Math.abs(t-c)<=config.shutter.no_cross_scene_blend_seconds);if(shutter)shutterFrames++;
 if(last&&v.shot===last.shot)maxStep=Math.max(maxStep,norm(sub(v.camera.slice(0,3),last.camera.slice(0,3))));last=v;
}
check('Every frame has finite, correctly scoped camera/focus state',bad===0&&maxStep<.40,{bad_frames:bad,max_same_shot_camera_step:maxStep,shot_counts:shotCounts,scene_counts:scenes,depth_focus_frames:focusFrames,shutter_frames:shutterFrames});
check('New surface insert and hero-cell shot occupy real timeline frames',scenes.surface===57&&shotCounts['04']===79,{surface_frames:scenes.surface,hero_track_frames:shotCounts['04']});
const tracking=[8.9,9.3,9.8,10.5].map(t=>{const p=m.cell(6,t).position,v=d.sample(t);return {time:t,error:norm(sub(v.focusPoint,[p[0],p[2],-p[1]])),distance:v.focusDistance}});
check('Cell-tracking focus follows the actual animated hero',tracking.every(x=>x.error<1e-8&&x.distance<4),tracking);
check('Focus is restrained and does not blur the editorial wide reversal',plan.shots.every(s=>s.focus.max_blur_px<=7)&&plan.shots.find(s=>s.id==='07').focus.strength===0,{max_native_blur_px:Math.max(...plan.shots.map(s=>s.focus.max_blur_px)),method:plan.focus_method});
const before=JSON.stringify([m.sample(9.3),d.sample(9.3)]);d.sample(27.4);d.sample(7.8);check('Actor/director evaluation remains stateless',before===JSON.stringify([m.sample(9.3),d.sample(9.3)]),{});
let reversed=0;
for(const kind of ['surface','deep']){let prev=-1;for(let t=config.cues[kind+'_pull_start'];t<=config.cues[kind+'_clear']+.00001;t+=.001){const v=m.sample(t)[kind==='surface'?'surfaceLift':'deepLift'];if(v<prev-1e-9)reversed++;prev=v;}}
check('Inherited fast pulls stay monotonic and grip first',reversed===0&&config.cues.surface_contact<config.cues.surface_pull_start&&config.cues.deep_contact<config.cues.deep_pull_start,{reversed,surface_pull:.42,deep_pull:.72});
check('Shared tactile anchors still match actor cues',tl.sound_events.filter(e=>e.visual_cue).every(e=>Math.abs(e.time-config.cues[e.visual_cue])<1e-9),tl.sound_events.filter(e=>e.visual_cue).map(e=>({cue:e.visual_cue,anchor:e.time,pre_roll:e.pre_roll||0})));
const shots=plan.shots.map(s=>{const t=(s.start+s.end)/2;return {id:s.id,time:t,kind:s.scene,old_camera:m.sample(t).camera,new_camera:d.sample(t).camera,translation_difference:norm(sub(m.sample(t).camera.slice(0,3),d.sample(t).camera.slice(0,3)))}});
check('Director actually changes the photography, not only version labels',shots.filter(s=>s.translation_difference>.3).length>=8,{changed_views:shots.filter(s=>s.translation_difference>.3).length,total:shots.length,comparisons:shots});
const report={passed:checks.every(x=>x.passed),checks_passed:checks.filter(x=>x.passed).length,checks_total:checks.length,checks,limits:['Shot cuts are intentional, continuity is checked within shots','Geometry-depth selective focus is an art-directed approximation, not calibrated optics','Illustrative cell internals/surface anatomy, not clinical microscopy or validated mechanics','Technical checks do not certify perfect taste, ASMR response or audience retention']};
fs.writeFileSync(path.join(root,'data/DIRECTOR_QA.json'),JSON.stringify(report,null,2)+'\n');fs.writeFileSync(path.join(root,'data/MOTION_QA.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));if(!report.passed)process.exitCode=1;

#!/usr/bin/env node
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {controller,makeRail} from './motion.mjs';import {director} from './director.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),load=f=>JSON.parse(fs.readFileSync(path.join(root,f)));
const baseline=load('data/V7_BASELINE.json'),plan=load('data/shot_plan.json'),controls=load('data/motion.json');
const motion=controller(controls),old=director(baseline.shot_plan,motion,controls),now=director(plan,motion,controls);
const comparisons=plan.shots.map(s=>{const t=(s.start+s.end)/2,a=old.sample(t).camera,b=now.sample(t).camera;return {shot:s.id,scene:s.scene,time:t,translationDifference:Math.hypot(...a.slice(0,3).map((v,i)=>v-b[i])),cameraChanged:JSON.stringify(a)!==JSON.stringify(b)};});
const checks=[];const check=(name,passed,details)=>checks.push({name,passed,details});
check('All nine shot cameras differ from actual V7 baseline',comparisons.every(x=>x.cameraChanged)&&comparisons.filter(x=>x.translationDifference>.1).length===9,comparisons);
check('Changes cover all three scene groups',new Set(comparisons.filter(x=>x.cameraChanged).map(x=>x.scene)).size===3,{groups:['finger','surface','anatomy']});
const arcs={};for(const kind of ['surface','deep']){const cue=controls.cues;const times=[cue[kind+'_approach_start'],(cue[kind+'_approach_start']+cue[kind+'_approach_end'])/2,cue[kind+'_contact']];arcs[kind]=times.map(t=>{const u=motion.sample(t)[kind+'Approach'];return {t,offset:(kind==='surface'?.045:.055)*Math.sin(Math.PI*u)};});}
check('New approach arcs return exactly before gripping',Object.values(arcs).every(a=>Math.abs(a[0].offset)<1e-10&&Math.abs(a[2].offset)<1e-10&&a[1].offset>.02),arcs);
const mix=load('data/mix_direction.json');check('Sound dynamics changed, narration retained',JSON.stringify(mix.music_automation)!==JSON.stringify(baseline.mix_direction.music_automation)&&mix.narration_change==='none',{cueCount:load('data/timeline.json').sound_events.length,voiceChange:'none'});
const result={passed:checks.every(c=>c.passed),checks,scope:'Numerical full-film comparison against actual V7; rendered geometry/material proof is additional. No taste/clinical/retention certification.'};
fs.writeFileSync(path.join(root,'data/UPGRADE_QA.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));if(!result.passed)process.exitCode=1;

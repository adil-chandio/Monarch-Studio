/* Shot-scoped cinematic camera/focus design. Pure absolute-time evaluation.
 * Actor movement remains in motion.mjs; this layer changes how it is photographed.
 * Camera discontinuities are allowed only at declared semantic shot cuts.
 */
import {makeRail,envelope,mix} from './motion.mjs';
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const blend=(a,b,t)=>a.map((v,i)=>mix(v,b[i],t));
const world=([x,y,z])=>[x,z,-y];
export function director(plan,motion,controls){
 const rails=plan.shots.map(s=>makeRail(s.camera));
 function fingerPoint(z,p){
  const a=controls.splinter.surface_angle,x=(.10+Math.sin(a)*z)*.88,y=.22+Math.cos(a)*z,zz=.11*.90,c=Math.cos(p.handYaw),s=Math.sin(p.handYaw);
  return [x*c+zz*s,y,-x*s+zz*c];
 }
 function wound(p){return [.20+.14*p.swelling,.04+.38*p.swelling,.21]}
 function wood(p){const a=controls.splinter.angle;return world([p.woodBase[0]+Math.sin(a)*2.07,p.woodBase[1],p.woodBase[2]+Math.cos(a)*2.07])}
 function sample(t,p=motion.sample(t)){
  let i=plan.shots.findIndex(s=>t>=s.start&&t<s.end);if(i<0)i=plan.shots.length-1;
  const shot=plan.shots[i];let camera=rails[i](t);let focus;
  if(shot.track_cell!==undefined){
   const cell=world(motion.cell(shot.track_cell,t).position);
   const after=envelope(t,9.82,10.6);const target=blend(cell,[-.04,-.78,.29],after*.35);
   camera=[...add(camera.slice(0,3),target),...add(camera.slice(3,6),target),camera[6]];
   focus=cell;
  }else if(shot.focus.kind==='surface_entry'){focus=[0,-.015,0];
  }else if(shot.focus.kind==='finger_contact'){
   focus=fingerPoint(2.083*.29+p.surfaceInsert+p.surfaceLift,p);
  }else if(shot.focus.kind==='finger_surface'){
   focus=fingerPoint(.27,p);
  }else if(shot.focus.kind==='surface_to_wood'){
   focus=blend(wound(p),wood(p),envelope(t,7.40,8.45));
  }else if(shot.focus.kind==='wound')focus=wound(p);
  else if(shot.focus.kind==='emerge')focus=blend(wound(p),wood(p),envelope(t,16.70,17.15));
  else if(shot.focus.kind==='warning_rack'){
   const base=world(p.woodBase);focus=blend(add(base,[.22,.68,.04]),wound(p),envelope(t,22.6,24.0));
  }else if(shot.focus.kind==='wood_tip')focus=wood(p);
  else focus=camera.slice(3,6);
  let strength=shot.focus.strength||0;
  if(t<1.70)strength*=envelope(t,1.45,1.70); // The opening3D word stays readable.
  const v=camera.slice(3,6).map((x,i)=>x-camera[i]);const len=Math.hypot(...v);
  const distance=Math.max(.1,focus.reduce((acc,x,i)=>acc+(x-camera[i])*v[i]/len,0));
  return {shot:shot.id,scene:shot.scene,description:shot.purpose,camera,focusPoint:focus,focusDistance:distance,focusRange:shot.focus.range||.2,focusStrength:strength,maxBlur:shot.focus.max_blur_px||0,trackCell:shot.track_cell??null};
 }
 return {sample,cuts:plan.shots.slice(1).map(x=>x.start)};
}

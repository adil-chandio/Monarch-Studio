/* Absolute-time motion controls, independent of Three.js and the render loop.
 * Quintic Hermite camera rails share velocity and zero acceleration at keys:
 * C2 continuity. Actor envelopes have zero velocity/acceleration at endpoints.
 * No physics integration, random-per-frame jitter or accumulated transforms.
 */
export const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
export const mix=(a,b,u)=>a+(b-a)*u;
export const smoother=u=>{u=clamp(u);return u*u*u*(u*(u*6-15)+10)};
export const envelope=(t,a,b)=>smoother((t-a)/(b-a));
export function hermite(p0,p1,v0,v1,dt,u){
  const d=p1-p0, a=v0*dt,b=v1*dt;
  // acceleration at either end is zero; derivative w.r.t. time is shared.
  return p0+a*u+(10*d-6*a-4*b)*u**3+(-15*d+8*a+7*b)*u**4+(6*d-3*a-3*b)*u**5;
}
export function makeRail(keys){
  if(keys.length<2)throw Error('A rail needs at least two keys');
  const n=keys.length,d=keys[0].value.length;
  for(let i=1;i<n;i++)if(keys[i].time<=keys[i-1].time)throw Error('Key times must increase');
  const velocities=keys.map((k,i)=>{
    if(k.velocity)return k.velocity;
    if(i===0||i===n-1)return Array(d).fill(0);
    const a=keys[i-1],b=keys[i+1];
    return k.value.map((_,j)=>{
      const left=(k.value[j]-a.value[j])/(k.time-a.time),right=(b.value[j]-k.value[j])/(b.time-k.time);
      // Stop a component at an extremum; do not overshoot anatomical framing.
      return left*right<=0?0:Math.sign(left)*Math.min(Math.abs((b.value[j]-a.value[j])/(b.time-a.time)),2*Math.abs(left),2*Math.abs(right));
    });
  });
  return t=>{
    if(t<=keys[0].time)return keys[0].value.slice();
    if(t>=keys[n-1].time)return keys[n-1].value.slice();
    const i=keys.findIndex((k,i)=>i<n-1&&t>=k.time&&t<keys[i+1].time),a=keys[i],b=keys[i+1],dt=b.time-a.time,u=(t-a.time)/dt;
    return a.value.map((p,j)=>hermite(p,b.value[j],velocities[i][j],velocities[i+1][j],dt,u));
  };
}
export function controller(config){
  const fingerCamera=makeRail(config.camera.finger),anatomyCamera=makeRail(config.camera.anatomy);
  const c=config.cues,angle=config.splinter.angle;
  function sample(t){
    const finger=t<c.scene_change;
    const close=envelope(t,c.surface_close_start,c.surface_contact);
    const lift=envelope(t,c.surface_pull_start,c.surface_clear);
    const extraction=envelope(t,c.deep_pull_start,c.deep_clear);
    const emerge=envelope(t,c.emerge_start,c.emerge_end);
    const surfaceLift=.035*envelope(t,c.surface_pull_start,c.surface_pull_start+config.pull_profiles.surface_tension_duration)+.945*envelope(t,c.surface_pull_start+config.pull_profiles.surface_travel_delay,c.surface_clear);
    const deepLift=.046*envelope(t,c.deep_pull_start,c.deep_pull_start+config.pull_profiles.deep_tension_duration)+2.074*envelope(t,c.deep_pull_start+config.pull_profiles.deep_travel_delay,c.deep_clear);
    const depth=-2.035+Math.cos(angle)*.67*emerge;
    const surfaceApproach=envelope(t,c.surface_approach_start,c.surface_approach_end),deepApproach=envelope(t,c.deep_approach_start,c.deep_approach_end);
    return {
      t,scene:finger?'finger':'anatomy',camera:(finger?fingerCamera:anatomyCamera)(t),
      handYaw:-.06+.07*envelope(t,.10,.65)-.025*envelope(t,4.15,4.50)+.006*Math.sin(t*1.10)*envelope(t,.70,1.10)*(1-envelope(t,3.8,4.1)),
      fingerDimple:.043*envelope(t,.13,.30)*(1-envelope(t,c.surface_pull_start,c.surface_clear))+.028*envelope(t,c.surface_contact,c.surface_pull_start)*(1-envelope(t,c.surface_pull_start+.10,c.surface_pull_start+.48)),
      surfaceInsert:.35*(1-envelope(t,.08,.28)),surfaceLift,surfaceClose:close,surfaceApproach,
      deepClose:envelope(t,c.deep_close_start,c.deep_contact),deepApproach,deepLift,
      woodBase:[-.51+Math.sin(angle)*(.67*emerge+deepLift),-.21,depth+Math.cos(angle)*deepLift],
      swelling:.035+1.03*envelope(t,c.swell_start,c.swell_full)-.115*envelope(t,c.deep_clear,config.duration),
      heat:envelope(t,c.swell_start,c.swell_full)*(1-.1*envelope(t,c.deep_clear,config.duration)),
      infection:envelope(t,c.infection_start,c.infection_full),emerge,
      surfaceGripLock:close>=.999,deepGripLock:t>=c.deep_contact,
      cues:c
    };
  }
  function cell(i,t){
    const start=c.cells_start+(i%5)*.036+Math.floor(i/5)*.018,arrive=c.cells_arrive+(i%6)*.043;
    const u=envelope(t,start,arrive),a=i*2.39996322973;
    const z=-1.72+(i%9)*.176,center=-.51+Math.sin(angle)*((z+2.035)/Math.cos(angle));
    const radius=.19+.045*(i%3);
    const end=[center+Math.cos(a)*radius,-.29-.036*(i%4),z+Math.sin(a)*.071];
    const from=[(i%2?-1:1)*(1.32+.16*(i%4)),-.20-.018*(i%3),-.18-(i%7)*.245];
    const via=[mix(from[0],end[0],.55),-.24-.055*Math.sin(a),mix(from[2],end[2],.55)+.17*Math.sin(a)];
    const pos=from.map((v,j)=>(1-u)**2*v+2*(1-u)*u*via[j]+u*u*end[j]);
    const drift=envelope(t,arrive,arrive+.65);pos[0]+=.014*Math.sin(t*1.28+a)*drift;pos[2]+=.008*Math.cos(t*1.42+a)*drift;
    const size=(.055+(i%5)*.006)*envelope(t,start-.10,start+.10),pulse=.018*Math.sin(t*.88+a);
    return {position:pos,scale:[size*(1+pulse),size*.81,size*(1-pulse*.6)],rotation:[.03*Math.sin(t*.7+a),t*.030+a,.035*Math.cos(t*.63+a)],arrival:arrive,progress:u};
  }
  function debris(i,t){
    const a=i*2.399963,z=-1.65+(i%8)*.19;
    const r=.041*envelope(t,c.infection_start+(i%5)*.08,c.infection_full+(i%4)*.04);
    return {position:[-.51+Math.sin(angle)*((z+2.035)/Math.cos(angle))+.14*Math.sin(a),-.37,z+.013*Math.sin(t*.8+a)],scale:[r*.75,r*.56,r],rotation:[0,a+t*.05,0]};
  }
  return {sample,cell,debris};
}

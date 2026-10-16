/* Monarch Studio · WF-02 · KAANTA
 * Existing project cutaway: Drive 1yfu7tZGut9LWcXidALvRlB9LdfxpMPM3.
 * New procedural finger, lighting, corrective morph normals, cameras,
 * annotations and edit. Deterministic time, no sampled scene plates.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { FXAAShader } from 'three/addons/shaders/FXAAShader.js';
import {controller, envelope, smoother} from './motion.mjs';

const params = new URLSearchParams(location.search);
const W = Number(params.get('w') || 1080), H = W * 16 / 9;
const stage = document.querySelector('#stage');
stage.style.width = W + 'px'; stage.style.height = H + 'px';
const timeline = await (await fetch('./data/timeline.json')).json();
const controls=await (await fetch('./data/motion.json')).json();
const motion=controller(controls);
await document.fonts.load('800 60px Montserrat');
await document.fonts.ready;
const renderer = new THREE.WebGLRenderer({antialias:false, alpha:true, preserveDrawingBuffer:true});
renderer.setSize(W,H); renderer.setPixelRatio(1); renderer.setClearColor(0,0);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.04;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.domElement.style.zIndex='1';
const bg = document.createElement('canvas'), hud=document.createElement('canvas');
for(const c of [bg,hud]) {c.width=W;c.height=H;c.style.width=W+'px';c.style.height=H+'px';}
bg.style.zIndex='0';hud.style.zIndex='2';
stage.append(bg,renderer.domElement,hud);
const b=bg.getContext('2d',{willReadFrequently:true}),ctx=hud.getContext('2d',{willReadFrequently:true});
const S=W/1080;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(32,W/H,.06,80);
const composer = new EffectComposer(renderer);
composer.setSize(W,H);
composer.addPass(new RenderPass(scene,camera));
composer.addPass(new OutputPass());
const fxaa=new ShaderPass(FXAAShader);fxaa.material.uniforms.resolution.value.set(1/W,1/H);composer.addPass(fxaa);
renderer.info.autoReset=false;
const pmrem = new THREE.PMREMGenerator(renderer);
const room = new RoomEnvironment();
scene.environment=pmrem.fromScene(room,.08).texture;
scene.environmentIntensity=.38;room.dispose();pmrem.dispose();
scene.add(new THREE.HemisphereLight('#b6e2ee','#5c2920',.64));
const key = new THREE.DirectionalLight('#ffe4d2',2.7);
key.position.set(-4.5,6,7); key.target.position.set(0,-1,0);
key.castShadow=true;key.shadow.mapSize.set(1024,1024);
Object.assign(key.shadow.camera,{left:-5,right:5,top:5,bottom:-5,near:.5,far:22});
key.shadow.bias=-.0003;key.shadow.normalBias=.022;key.shadow.radius=3;
scene.add(key,key.target);
const fill=new THREE.DirectionalLight('#81c9f0',.72);fill.position.set(4,2,5);scene.add(fill);
const rim=new THREE.DirectionalLight('#8fe2f5',2.3);rim.position.set(3,3,-5);scene.add(rim);
const soft=new THREE.PointLight('#ef9d75',5,14,2);soft.position.set(-2,-1,3);scene.add(soft);

const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const ease=smoother;
const range=(t,a,b)=>ease((t-a)/(b-a));
const lerp=THREE.MathUtils.lerp;
const vec=(a)=>new THREE.Vector3(...a);
let seed=40217;
const rnd=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296};

// Independently authored procedural albedo and pore/ridge bump maps.
function tissueTexture(kind='skin') {
  const c=document.createElement('canvas');c.width=c.height=512;
  const x=c.getContext('2d'),im=x.createImageData(512,512);
  const bump=document.createElement('canvas');bump.width=bump.height=512;
  const bx=bump.getContext('2d'),bi=bx.createImageData(512,512);
  for(let j=0;j<512;j++)for(let i=0;i<512;i++){
    const u=i/512,v=j/512,n=rnd()-.5;
    const dist=Math.sqrt((u-.49)**2*.83+(v-.53)**2*1.65);
    const ridge=Math.sin(dist*255+Math.sin(u*12)*.85+Math.sin(v*8));
    const crease=Math.pow(.5+.5*ridge,7),noisy=n*9+Math.sin(u*62+v*34)*1.2;
    const rgb=kind==='dermis'?[182,83,77]:kind==='finger'?[204,139,110]:[204,140,111];
    const at=(j*512+i)*4;
    for(let k=0;k<3;k++){im.data[at+k]=rgb[k]+noisy-crease*(kind==='dermis'?0:3);bi.data[at+k]=128+ridge*31+n*32;}
    im.data[at+3]=bi.data[at+3]=255;
  }
  x.putImageData(im,0,0);bx.putImageData(bi,0,0);
  const map=new THREE.CanvasTexture(c),bmap=new THREE.CanvasTexture(bump);
  map.colorSpace=THREE.SRGBColorSpace;map.anisotropy=4;bmap.anisotropy=4;
  return {map,bumpMap:bmap};
}
const skinTex=tissueTexture('skin'),dermisTex=tissueTexture('dermis'),fingerTex=tissueTexture('finger');
const skinMat=new THREE.MeshPhysicalMaterial({...skinTex,roughness:.43,metalness:0,bumpScale:.019,clearcoat:.10,clearcoatRoughness:.42});
const fingerMat=new THREE.MeshPhysicalMaterial({...fingerTex,roughness:.46,metalness:0,bumpScale:.012,clearcoat:.07,clearcoatRoughness:.5});
const steel=new THREE.MeshStandardMaterial({color:'#d9e3e9',metalness:.95,roughness:.19,envMapIntensity:2.15,emissive:'#17232c',emissiveIntensity:.22});
const gltf=await new GLTFLoader().loadAsync('./assets/models/cutaway.glb');
const anatomy=gltf.scene;scene.add(anatomy);
// Reuse the source meshes, but v3 actors are driven by explicit C2 controls.
// The v2 sampled clip remains preserved in the unchanged GLB, not layered over these controls.
const heatUniform={value:0};
function addHeat(mat,kind){
  mat.onBeforeCompile=shader=>{
    shader.uniforms.uHeat=heatUniform;
    shader.vertexShader='varying vec3 vAnatomy;\n'+shader.vertexShader;
    shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvAnatomy=position;');
    shader.fragmentShader='uniform float uHeat;varying vec3 vAnatomy;\n'+shader.fragmentShader;
    const q=kind==='dermis'?'vec2(vAnatomy.x + 0.05, (vAnatomy.z + 0.65)*0.65)':'vec2(vAnatomy.x - 0.08, vAnatomy.y*0.65)';
    shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>\nfloat heat=exp(-dot(${q},${q})*2.35)*uHeat;diffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.43,0.009,0.006),heat*.93);`);
  };
  mat.customProgramCacheKey=()=>`heat-${kind}`;
}
addHeat(skinMat,'skin');
const dermMat=new THREE.MeshPhysicalMaterial({...dermisTex,roughness:.49,clearcoat:.08,bumpMap:dermisTex.bumpMap,bumpScale:.008});addHeat(dermMat,'dermis');
const named={};
anatomy.traverse(o=>{
  if(!o.isMesh)return; named[o.name]=o;o.castShadow=true;o.receiveShadow=true;
  const n=o.name;
  if(n==='skin_top'||n==='skin_front')o.material=skinMat;
  else if(n==='dermis')o.material=dermMat;
  else if(n==='fat_layer')o.material=new THREE.MeshStandardMaterial({color:'#a35b26',roughness:.8});
  else if(n.startsWith('fat_'))o.material=new THREE.MeshPhysicalMaterial({color:n.charCodeAt(n.length-1)%2?'#e7ad4e':'#d79335',roughness:.45,clearcoat:.05});
  else if(n==='basal')o.material=new THREE.MeshStandardMaterial({color:'#8f4538',roughness:.7});
  else if(n.startsWith('basal_cell'))o.material=new THREE.MeshStandardMaterial({color:'#cd917c',roughness:.56});
  else if(n==='collagen')o.material=new THREE.MeshStandardMaterial({color:'#d99d86',roughness:.78});
  else if(n==='artery')o.material=new THREE.MeshPhysicalMaterial({color:'#a93028',roughness:.33,clearcoat:.16});
  else if(n==='vein')o.material=new THREE.MeshPhysicalMaterial({color:'#3a648a',roughness:.39,clearcoat:.12});
  else if(n==='sweat_ducts')o.material=new THREE.MeshStandardMaterial({color:'#c59155',roughness:.53});
  else if(n.startsWith('tweezer'))o.material=steel;
  else if(n.startsWith('immune'))o.material=new THREE.MeshPhysicalMaterial({color:n.charCodeAt(n.length-1)%2?'#e6e7d5':'#d7dfd1',roughness:.37,clearcoat:.12,clearcoatRoughness:.4});
  else if(n.startsWith('debris'))o.material=new THREE.MeshStandardMaterial({color:'#d8c58d',roughness:.72});
  if(o.geometry.morphAttributes.position?.length){
    // The recovered asset has POSITION morphs but no NORMAL morphs. Add
    // exact endpoint normal deltas so swelling is shaded as a dome.
    const geom=o.geometry;
    geom.computeVertexNormals();
    geom.morphAttributes.normal=geom.morphAttributes.position.map(attr=>{
      const p=geom.attributes.position;const work=new THREE.BufferGeometry();
      const vals=new Float32Array(p.count*3);
      for(let i=0;i<vals.length;i++)vals[i]=p.array[i]+attr.array[i];
      work.setAttribute('position',new THREE.BufferAttribute(vals,3));work.setIndex(geom.index.clone());work.computeVertexNormals();
      const n=new Float32Array(vals.length);
      for(let i=0;i<n.length;i++)n[i]=work.attributes.normal.array[i]-geom.attributes.normal.array[i];
      work.dispose();return new THREE.BufferAttribute(n,3);
    });
  }
});


// Hardware instancing preserves every animated cell transform while replacing
// >150 repetitive draw calls with four batches. Critical on a software GPU.
const instanceBatches=[];
function instanceGroup(names,dynamic=false){
  const objects=names.map(n=>named[n]);if(!objects.length)return;
  const mat=objects[0].material.clone();mat.color.set('#ffffff');
  const batch=new THREE.InstancedMesh(objects[0].geometry,mat,objects.length);
  batch.name='Batch_'+names[0];batch.castShadow=true;batch.receiveShadow=true;batch.frustumCulled=false;
  objects[0].parent.add(batch);
  objects.forEach((o,i)=>{batch.setColorAt(i,o.material.color);o.visible=false});
  const update=()=>{objects.forEach((o,i)=>{o.updateMatrix();batch.setMatrixAt(i,o.matrix)});batch.instanceMatrix.needsUpdate=true};
  update();if(dynamic)instanceBatches.push({update});
}
const keys=Object.keys(named);
instanceGroup(keys.filter(n=>/^fat_\d+$/.test(n)));
instanceGroup(keys.filter(n=>n.startsWith('basal_cell')));
instanceGroup(keys.filter(n=>n.startsWith('immune_')),true);
instanceGroup(keys.filter(n=>n.startsWith('debris_')),true);

// Procedural fingertip; palmar skin has no hair follicles. No face/identity asset.
const hand=new THREE.Group();scene.add(hand);
function fingerGeometry(){
  const pos=[],uv=[],ix=[],N=100,R=100;
  for(let j=0;j<=R;j++){
    const t=j/R,y=lerp(-4.65,.49,t);
    let rad=.65-.10*ease((y+3)/2.7)+.043*Math.exp(-(((y+1.90)/.27)**2));
    if(y>-.13)rad=.55*Math.sqrt(Math.max(0,1-((y+.13)/.62)**2));
    rad=Math.max(.001,rad);
    for(let i=0;i<=N;i++){
      const a=i/N*Math.PI*2;const bend=.1*Math.sin((y+4.65)*.50);
      const crease=1-.022*Math.exp(-(((y+1.85)/.046)**2))-.018*Math.exp(-(((y+2.04)/.038)**2));
      pos.push(bend+Math.cos(a)*rad*crease,y,Math.sin(a)*rad*.87*crease);
      uv.push(i/N,t);
      if(j<R&&i<N){const q=j*(N+1)+i;ix.push(q,q+N+1,q+1,q+1,q+N+1,q+N+2);}
    }
  }
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ix);g.computeVertexNormals();return g;
}
const finger=new THREE.Mesh(fingerGeometry(),fingerMat);finger.castShadow=true;finger.receiveShadow=true;hand.add(finger);
const fingerRest=finger.geometry.attributes.position.array.slice();
const fingerWeights=new Float32Array(fingerRest.length/3);
for(let i=0;i<fingerWeights.length;i++){const [x,y,z]=fingerRest.slice(i*3,i*3+3);fingerWeights[i]=Math.exp(-((x-.10)**2+(z-.11)**2)/.045)*envelope(y,-.12,.38);}
function deformFinger(dimple){const pos=finger.geometry.attributes.position;for(let i=0;i<pos.count;i++)pos.array[i*3+1]=fingerRest[i*3+1]-dimple*fingerWeights[i];pos.needsUpdate=true;finger.geometry.computeVertexNormals();}
function ellipsoid(p,sc,mat){const m=new THREE.Mesh(new THREE.SphereGeometry(1,40,28),mat);m.position.set(...p);m.scale.set(...sc);m.castShadow=true;m.receiveShadow=true;hand.add(m);return m;}
ellipsoid([-.08,-4.5,-.38],[1.42,1.35,.71],fingerMat);
const curl=ellipsoid([-.87,-3.46,-.42],[.48,.9,.47],fingerMat);curl.rotation.z=-.15;
const thumb=ellipsoid([.83,-3.65,.16],[.55,.95,.46],fingerMat);thumb.rotation.z=-.83;
// Joint creases are shallow physical tubes, not painted black outlines.
for(let j=0;j<3;j++){
  const pts=[];for(let i=0;i<=35;i++){
    const x=-.44+i/35*.9, yy=-1.89-j*.11+.08*(x/.5)**2;
    pts.push(new THREE.Vector3(x+.1,yy,Math.sqrt(Math.max(.01,.55**2-x*x))*.87+.003));
  }
  const line=new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts),35,.0045,5,false),new THREE.MeshStandardMaterial({color:'#ac7059',roughness:.85}));hand.add(line);
}
// Fingerprint micro-ridges are carried by the procedural bump map.
const handToolRoot=new THREE.Group();handToolRoot.position.set(.10,.22,.11);handToolRoot.rotation.set(-Math.PI/2,0,0);hand.add(handToolRoot);
const handAxis=new THREE.Group();handAxis.rotation.y=-.23;handToolRoot.add(handAxis);
const handSplinter=new THREE.Mesh(named.splinter.geometry,named.splinter.material);handSplinter.scale.set(.25,.25,.29);handSplinter.castShadow=true;handAxis.add(handSplinter);
// New joined, beveled forceps. Gap is a real deformation, not scaling a pair
// of floating rods. Both actors share the splinter's axis through the grip.
function jawGeometry(side,gap){
  const pos=[],ix=[],uv=[],N=48,R=8,L=2.64,w=.032,d=.015,b=.005;
  const ring=[[-w+b,-d],[w-b,-d],[w,-d+b],[w,d-b],[w-b,d],[-w+b,d],[-w,d-b],[-w,-d+b]];
  for(let j=0;j<=N;j++){
    const u=j/N,cx=side*(.04+(gap-.04)*(1-u)**3+.25*Math.sin(Math.PI*u));
    const dx=side*(-3*(gap-.04)*(1-u)**2+.25*Math.PI*Math.cos(Math.PI*u)),nz=-dx/Math.hypot(dx,L),nx=L/Math.hypot(dx,L);
    for(let k=0;k<R;k++){pos.push(cx+nx*ring[k][0],ring[k][1],u*L+nz*ring[k][0]);uv.push(k/R,u);if(j<N){const a=j*R+k,c=j*R+(k+1)%R;ix.push(a,c,a+R,c,c+R,a+R);}}
  }
  for(let k=1;k<R-1;k++){ix.push(0,k+1,k);const a=N*R;ix.push(a,a+k,a+k+1);}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ix);g.computeVertexNormals();return g;
}
const woodPositions=named.splinter.geometry.attributes.position;
let minGripX=Infinity,maxGripX=-Infinity;
for(let i=0;i<woodPositions.count;i++)if(woodPositions.getZ(i)>2.055){minGripX=Math.min(minGripX,woodPositions.getX(i));maxGripX=Math.max(maxGripX,woodPositions.getX(i));}
const rawGripCenter=(minGripX+maxGripX)/2,rawGripHalf=(maxGripX-minGripX)/2;
function forceps(scale,woodScale){
  const g=new THREE.Group();g.scale.setScalar(scale);
  const goal=rawGripHalf*woodScale/scale;
  let closed=goal+.031;
  for(let i=0;i<10;i++){const slope=(-3*(closed-.04)+.25*Math.PI)/2.64;closed=goal+.032/Math.sqrt(1+slope*slope);}
  const jaws=[-1,1].map(side=>{const geo=jawGeometry(side,closed);const m=new THREE.Mesh(geo,steel);m.castShadow=true;m.receiveShadow=true;g.add(m);return {mesh:m,side};});
  const bridge=new THREE.Mesh(new THREE.CylinderGeometry(.021,.021,.13,14),steel);bridge.rotation.z=Math.PI/2;bridge.position.set(0,0,2.65);bridge.castShadow=true;g.add(bridge);
  const matrices=jaws.map(j=>j.mesh.geometry.attributes.position.array.slice());
  function setClosed(u){
    const gap=closed+.215*(1-u);
    jaws.forEach((j,k)=>{
      const pos=j.mesh.geometry.attributes.position;
      for(let i=0;i<pos.count;i++){const v=Math.floor(i/8)/48;pos.array[i*3]=matrices[k][i*3]+j.side*(gap-closed)*(1-v)**3;}
      pos.needsUpdate=true;j.mesh.geometry.computeVertexNormals();
    });
  }
  return {group:g,setClosed,closedGap:closed,scale,goalHalf:goal*scale};
}
const surfaceForceps=forceps(.60,.25);handAxis.add(surfaceForceps.group);
const deepForceps=forceps(.86,.57);named.splinter.parent.add(deepForceps.group);
named.tweezer_L.visible=false;named.tweezer_R.visible=false;

// Warm translucent inflammatory pocket. It is explanatory, not measured fluid.
const pocket=new THREE.Mesh(new THREE.SphereGeometry(1,44,30),new THREE.MeshPhysicalMaterial({color:'#d7b77d',roughness:.46,transparent:true,opacity:.0,depthWrite:false,clearcoat:.07}));
pocket.position.set(-.13,-.78,.115);pocket.scale.set(.34,.81,.045);anatomy.add(pocket);
// Projection-based, editorial arrows are labelled 'possible' rather than forces.
const accent='#80e3eb',white='#f5f4ee',muted='#b0c8d2',warm='#ffd08b';
function text(str,x,y,size=36,color=white,weight=600,align='left'){
  ctx.fillStyle=color;ctx.font=`${weight} ${size}px Montserrat`;ctx.textAlign=align;ctx.textBaseline='alphabetic';ctx.fillText(str,x,y);
}
function line(x1,y1,x2,y2,col=accent,width=2){ctx.strokeStyle=col;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();}
function roundBox(x,y,w,h,r,fill,stroke){ctx.beginPath();ctx.roundRect(x,y,w,h,r);if(fill){ctx.fillStyle=fill;ctx.fill()}if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=1.5;ctx.stroke()}}
function projected(v){const p=vec(v).project(camera);return[(p.x*.5+.5)*1080,(-p.y*.5+.5)*1920];}
function leader(label,world,x,y,opacity=1){const p=projected(world);ctx.globalAlpha=.87*opacity;line(p[0],p[1],x,y,'#c5e4eaaa',1.7);ctx.beginPath();ctx.arc(p[0],p[1],4,0,Math.PI*2);ctx.fillStyle=accent;ctx.fill();roundBox(x-8,y-32,ctx.measureText(label).width+24,44,8,'#082436cd');text(label,x+4,y,23,white,600);ctx.globalAlpha=1;}
function background(t){
  b.save();b.scale(S,S);
  const g=b.createRadialGradient(565,680,10,510,860,1240);
  g.addColorStop(0,t<7?'#4094ae':'#35829b');g.addColorStop(.5,'#174a64');g.addColorStop(1,'#071b2c');
  b.fillStyle=g;b.fillRect(0,0,1080,1920);
  b.strokeStyle='#80dce80b';b.lineWidth=1;
  for(let i=0;i<16;i++){const y=260+i*103+(t*6)%103;b.beginPath();b.moveTo(0,y);b.lineTo(1080,y-105);b.stroke();}
  b.restore();
}
function pose(t){
  const p=motion.sample(t),v=p.camera;
  anatomy.visible=p.scene==='anatomy';hand.visible=p.scene==='finger';
  camera.position.set(v[0],v[1],v[2]);camera.lookAt(v[3],v[4],v[5]);camera.fov=v[6];camera.updateProjectionMatrix();
  if(p.scene==='finger'){
    hand.rotation.y=p.handYaw;deformFinger(p.fingerDimple);
    handSplinter.position.z=p.surfaceInsert+p.surfaceLift;
    const tool=surfaceForceps.group;
    tool.visible=t>=controls.cues.surface_approach_start;
    tool.position.set(rawGripCenter*.25+.12*(1-p.surfaceApproach),0,2.083*.29+1.50*(1-p.surfaceApproach)+p.surfaceLift);
    surfaceForceps.setClosed(p.surfaceClose);
  }else{
    named.splinter.position.set(...p.woodBase);named.splinter.rotation.set(0,controls.splinter.angle,0);named.splinter.scale.set(.57,.74,1);
    named.skin_top.morphTargetInfluences[0]=p.swelling;named.skin_front.morphTargetInfluences[0]=p.swelling;
    for(let i=0;i<32;i++){const c=motion.cell(i,t),o=named['immune_'+i];o.position.set(...c.position);o.scale.set(...c.scale);o.rotation.set(...c.rotation);}
    for(let i=0;i<18;i++){const c=motion.debris(i,t),o=named['debris_'+i];o.position.set(...c.position);o.scale.set(...c.scale);o.rotation.set(...c.rotation);}
    for(const batch of instanceBatches)batch.update();
    const tool=deepForceps.group;
    tool.visible=t>=controls.cues.deep_approach_start;
    tool.rotation.set(0,controls.splinter.angle,0);
    const along=2.083+1.30*(1-p.deepApproach),x=rawGripCenter*.57+.15*(1-p.deepApproach),a=controls.splinter.angle;
    tool.position.set(p.woodBase[0]+Math.sin(a)*along+Math.cos(a)*x,p.woodBase[1],p.woodBase[2]+Math.cos(a)*along-Math.sin(a)*x);
    deepForceps.setClosed(p.deepClose);
    heatUniform.value=p.heat;pocket.material.opacity=.29*p.infection;pocket.visible=p.infection>0;
  }
  camera.updateMatrixWorld();return p;
}
function caption(t){
  const c=timeline.captions.find(c=>t>=c.start&&t<c.end);if(!c)return;
  let size=57;ctx.font=`750 ${size}px Montserrat`;
  while(ctx.measureText(c.text).width>904){size--;ctx.font=`750 ${size}px Montserrat`;}
  const w=ctx.measureText(c.text).width,x=(1080-w)/2,y=1561;
  const inP=range(t,c.start,c.start+.09)*(1-range(t,c.end-.065,c.end));
  ctx.save();ctx.translate(0,(1-inP)*9);ctx.globalAlpha=inP;
  roundBox(x-33,y-size-24,w+66,size+58,17,'#051725dd','#b9e6ed25');
  ctx.shadowColor='#001017';ctx.shadowBlur=5;
  const i=c.text.indexOf(c.accent);const before=c.text.slice(0,i),after=c.text.slice(i+c.accent.length);
  text(before,x,y,size,white,750);const bw=ctx.measureText(before).width;
  text(c.accent,x+bw,y,size,t>=18.98?warm:accent,800);const aw=ctx.measureText(c.accent).width;
  text(after,x+bw+aw,y,size,white,750);ctx.restore();
}
function overlay(t){
  ctx.clearRect(0,0,W,H);ctx.save();ctx.scale(S,S);
  const shade=ctx.createLinearGradient(0,0,0,480);shade.addColorStop(0,'#051c30ff');shade.addColorStop(.66,'#051c30ee');shade.addColorStop(1,'#051c3000');ctx.fillStyle=shade;ctx.fillRect(0,0,1080,480);
  const bot=ctx.createLinearGradient(0,1350,0,1920);bot.addColorStop(0,'#061b2900');bot.addColorStop(.78,'#061b29cd');bot.addColorStop(1,'#061b29');ctx.fillStyle=bot;ctx.fillRect(0,1350,1080,570);
  // Small brand lockup, not a copied creator logo.
  line(68,95,88,73,accent,3);line(88,73,104,95,accent,3);line(104,95,122,73,accent,3);line(122,73,142,95,accent,3);
  text('MONARCH',162,98,26,white,700);text('MOTION EDITION / 03',1011,98,20,muted,500,'right');line(68,135,1012,135,'#c2e9ee3b',1);
  const shot=timeline.shots.find(s=>t>=s.start&&t<s.end)||timeline.shots.at(-1);
  const p=range(t,shot.start,shot.start+.21)*(1-range(t,shot.end-.10,shot.end));
  ctx.save();ctx.globalAlpha=p;ctx.translate(0,(1-p)*12);
  text(`${shot.id}  /  ${t<7?'FINGERTIP':t>=25.83?'SAFE RESPONSE':'UNDER THE SKIN'}`,70,197,23,accent,600);
  let hsize=t<3.68?76:t>=18.98&&t<22.08?88:55;
  ctx.font=`800 ${hsize}px Montserrat`;while(ctx.measureText(shot.label).width>944){hsize--;ctx.font=`800 ${hsize}px Montserrat`;}
  text(shot.label,68,284,hsize,t>=18.98&&t<25.83?warm:white,800);
  text(shot.sub,72,333,26,muted,500);
  ctx.restore();
  if(t>=7&&t<9.46){
    const op=range(t,7,7.30)*(1-range(t,9.18,9.46));ctx.font='600 23px Montserrat';leader('SKIN',[1.3,0,.06],765,700,op);leader('TISSUE',[1.5,-1.03,.1],755,1060,op);leader('FAT',[1.7,-2.42,.15],785,1240,op);
  }
  if(t>=8.9&&t<11.55){
    ctx.save();ctx.globalAlpha=range(t,8.9,9.13)*(1-range(t,11.3,11.55));
    roundBox(78,1275,345,70,12,'#06253bd9','#a2e3dd46');text('CELLS MOVE IN',102,1320,28,accent,700);ctx.restore();
  }
  if(t>=13.12&&t<15.56){
    ctx.save();ctx.globalAlpha=range(t,13.12,13.40)*(1-range(t,15.34,15.56));
    roundBox(74,1215,413,104,14,'#291e24e6','#e3b87455');text('AGAR INFECTION HO',99,1258,24,warm,750);text('Peep ban sakti hai',99,1294,26,white,550);ctx.restore();
  }
  if(t>=15.76&&t<18.88){
    ctx.save();ctx.globalAlpha=range(t,15.76,16.05)*(1-range(t,18.61,18.88));
    const p0=projected([.71,-.7,.38]),p1=projected([.93,.1,.4]);
    const flutter=Math.sin((t-15.56)*2.2)*3;const grow=range(t,15.76,16.31);const qx=lerp(p0[0],p1[0],grow)+44,qy=lerp(p0[1],p1[1]-flutter,grow);
    line(p0[0]+44,p0[1],qx,qy,accent,4);line(qx,qy,qx-12,qy+23,accent,4);line(qx,qy,qx+12,qy+23,accent,4);
    roundBox(69,1260,484,69,12,'#082e42e8','#96e1e34c');text('POSSIBLE — GUARANTEE NAHI',92,1305,25,accent,750);ctx.restore();
  }
  if(t>=18.98&&t<22.08){
    ctx.save();ctx.globalAlpha=range(t,18.98,19.22)*(1-range(t,21.86,22.08));
    roundBox(74,1220,930,126,18,'#122331eb','#edc08065');text('INFECTION KA WAIT NAHI.',110,1298,42,warm,800);ctx.restore();
  }
  if(t>=22.08&&t<25.83){
    const labels=['Gehra kaanta','Barhti laali','Dard / peep'];
    labels.forEach((s,i)=>{ctx.save();ctx.globalAlpha=range(t,22.08+i*.12,22.34+i*.12)*(1-range(t,25.64,25.83));const x=76+i*313;roundBox(x,1270,295,72,12,'#0a2536ee','#e3b77365');text(s,x+147.5,1316,25,warm,700,'center');ctx.restore()});
  }
  if(t>=25.83){
    ctx.save();ctx.globalAlpha=range(t,25.83,26.15);roundBox(74,1263,930,89,16,'#092e37ee','#99e4da66');text('SKIN KO MAT KHODO.',540,1322,40,accent,800,'center');ctx.restore();
  }
  caption(t);
  if(t>=29.4){text('Samjho. Khodo mat.',540,1548,50,white,750,'center');}
  text('Educational 3D · Scale aur waqt simplified',540,1680,23,muted,450,'center');
  if(t>=7)text('Medical advice ka replacement nahi.',540,1718,23,'#9cb6c1',450,'center');
  text('WF–02  /  MONARCH STUDIO',70,1805,21,'#99b9c6',550);
  text(`${String(Math.min(30,Math.floor(t))).padStart(2,'0')} / 30`,1010,1805,21,'#99b9c6',550,'right');
  roundBox(70,1834,940,4,2,'#6382914a');roundBox(70,1834,Math.max(1,940*t/timeline.duration),4,2,accent);
  ctx.restore();
}
window.renderAt=(t)=>{t=clamp(t,0,timeline.duration-.0001);background(t);const p=pose(t);renderer.info.reset();composer.render();overlay(t);return {time:t,shot:timeline.shots.find(s=>t>=s.start&&t<s.end)?.id,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,camera:p.camera,surfaceLift:p.surfaceLift,deepLift:p.deepLift}};
const deliveryCanvas=document.createElement('canvas');deliveryCanvas.width=W;deliveryCanvas.height=H;const deliveryCtx=deliveryCanvas.getContext('2d',{alpha:false,willReadFrequently:true});
window.exportFrame=(kind='png')=>{deliveryCtx.drawImage(bg,0,0);deliveryCtx.drawImage(renderer.domElement,0,0);deliveryCtx.drawImage(hud,0,0);return deliveryCanvas.toDataURL(kind==='png'?'image/png':'image/jpeg',.99).split(',')[1]};
window.motionState=t=>motion.sample(t);window.flush=()=>renderer.getContext().finish();
window.geometryInfo={gripHalfRaw:rawGripHalf,surfaceGap:surfaceForceps.closedGap,deepGap:deepForceps.closedGap};
window.filmInfo={version:3,width:W,height:H,fps:timeline.fps,triangles:0,native3d:true,duration:timeline.duration,interpolation:'C2 object/camera keyframes; no optical-flow generated frames'};
window.renderAt(0.8);
window.filmInfo.triangles=renderer.info.render.triangles;
window.ready=true;
if(params.get('play')==='1'){
  const button=document.querySelector('#controls');button.hidden=false;let playing=false,start=0,hold=0;
  button.onclick=()=>{playing=!playing;if(playing)start=performance.now()-hold*1000};
  const loop=now=>{if(playing){hold=((now-start)/1000)%timeline.duration;window.renderAt(hold)}requestAnimationFrame(loop)};requestAnimationFrame(loop);
}

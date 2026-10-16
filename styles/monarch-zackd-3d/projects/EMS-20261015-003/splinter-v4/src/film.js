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
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';

const params = new URLSearchParams(location.search);
const W = Number(params.get('w') || 1080), H = W * 16 / 9;
const stage = document.querySelector('#stage');
stage.style.width = W + 'px'; stage.style.height = H + 'px';
const timeline = await (await fetch('./data/timeline.json')).json();
const controls=await (await fetch('./data/motion.json')).json();
const motion=controller(controls);
const design=await (await fetch('./data/design.json')).json();
await document.fonts.load('600 46px Montserrat');
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
scene.environmentIntensity=.28;room.dispose();pmrem.dispose();
scene.add(new THREE.HemisphereLight('#c4d7de','#563f37',.58));
const key = new THREE.DirectionalLight('#fff0df',2.35);
key.position.set(-4.5,6,7); key.target.position.set(0,-1,0);
key.castShadow=true;key.shadow.mapSize.set(2048,2048);
Object.assign(key.shadow.camera,{left:-5,right:5,top:5,bottom:-5,near:.5,far:22});
key.shadow.bias=-.0003;key.shadow.normalBias=.022;key.shadow.radius=3;
scene.add(key,key.target);
const fill=new THREE.DirectionalLight('#bed3df',.72);fill.position.set(4,2,5);scene.add(fill);
const rim=new THREE.DirectionalLight('#cddfe4',1.75);rim.position.set(3,3,-5);scene.add(rim);
const soft=new THREE.PointLight('#e6c2ac',2.2,14,2);soft.position.set(-2,-1,3);scene.add(soft);

const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const ease=smoother;
const range=(t,a,b)=>ease((t-a)/(b-a));
const lerp=THREE.MathUtils.lerp;
const vec=(a)=>new THREE.Vector3(...a);
let seed=40217;
const rnd=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296};

// Independently authored procedural albedo and pore/ridge bump maps.
function tissueTexture(kind='skin') {
  const c=document.createElement('canvas');c.width=c.height=768;
  const x=c.getContext('2d'),im=x.createImageData(768,768);
  const bump=document.createElement('canvas');bump.width=bump.height=768;
  const bx=bump.getContext('2d'),bi=bx.createImageData(768,768);
  for(let j=0;j<768;j++)for(let i=0;i<768;i++){
    const u=i/768,v=j/768,n=rnd()-.5;
    const dist=kind==='finger'?Math.sqrt((u-.25)**2*1.7+(v-.16)**2*2.4):Math.sqrt((u-.49)**2*.83+(v-.53)**2*1.65);
    const ridge=Math.sin(dist*(kind==='finger'?500:255)+Math.sin(u*12)*.55+Math.sin(v*8)*.35);
    const crease=Math.pow(.5+.5*ridge,7),noisy=n*4.7+Math.sin(u*62+v*34)*.8;
    const rgb=kind==='dermis'?[175,87,82]:kind==='finger'?[198,151,128]:[201,151,132];
    const at=(j*768+i)*4;
    for(let k=0;k<3;k++){im.data[at+k]=rgb[k]+noisy-crease*(kind==='dermis'?0:3);bi.data[at+k]=128+ridge*(kind==='finger'?8+19*Math.exp(-((u-.25)**2/.019+(v-.16)**2/.058)):16)+n*17;}
    im.data[at+3]=bi.data[at+3]=255;
  }
  x.putImageData(im,0,0);bx.putImageData(bi,0,0);
  const map=new THREE.CanvasTexture(c),bmap=new THREE.CanvasTexture(bump);
  map.colorSpace=THREE.SRGBColorSpace;map.anisotropy=4;bmap.anisotropy=4;
  return {map,bumpMap:bmap};
}
const skinTex=tissueTexture('skin'),dermisTex=tissueTexture('dermis'),fingerTex=tissueTexture('finger');
const skinMat=new THREE.MeshPhysicalMaterial({...skinTex,roughness:.43,clearcoat:.065,clearcoatRoughness:.5,bumpScale:.010,envMapIntensity:.8});
const fingerMat=new THREE.MeshPhysicalMaterial({...fingerTex,roughness:.47,clearcoat:.07,clearcoatRoughness:.55,bumpScale:.008,envMapIntensity:.8});
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
    shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>\nfloat heat=exp(-dot(${q},${q})*2.35)*uHeat;diffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.38,0.022,0.026),heat*.87);`);
  };
  mat.customProgramCacheKey=()=>`heat-${kind}`;
}
addHeat(skinMat,'skin');
const dermMat=new THREE.MeshPhysicalMaterial({...dermisTex,roughness:.54,clearcoat:.045,bumpScale:.006,envMapIntensity:.7,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:2});addHeat(dermMat,'dermis');
const named={};
anatomy.traverse(o=>{
  if(!o.isMesh)return; named[o.name]=o;o.castShadow=true;o.receiveShadow=true;
  const n=o.name;
  if(n==='skin_top'||n==='skin_front')o.material=skinMat;
  else if(n==='dermis')o.material=dermMat;
  else if(n==='fat_layer')o.material=new THREE.MeshPhongMaterial({color:'#886a4d',shininess:12,specular:'#181714'});
  else if(n.startsWith('fat_'))o.material=new THREE.MeshStandardMaterial({color:n.charCodeAt(n.length-1)%2?'#bfa16d':'#ad8b57',roughness:.53,envMapIntensity:.7});
  else if(n==='basal')o.material=new THREE.MeshPhongMaterial({color:'#86554b',shininess:18,specular:'#241c1b'});
  else if(n.startsWith('basal_cell'))o.material=new THREE.MeshStandardMaterial({color:'#bd897c',roughness:.59,envMapIntensity:.6});
  else if(n==='collagen')o.material=new THREE.MeshPhongMaterial({color:'#b98578',shininess:12,specular:'#20191b'});
  else if(n==='artery')o.material=new THREE.MeshPhongMaterial({color:'#953c37',shininess:48,specular:'#713d37'});
  else if(n==='vein')o.material=new THREE.MeshPhongMaterial({color:'#475b6b',shininess:38,specular:'#54606b'});
  else if(n==='sweat_ducts')o.material=new THREE.MeshPhongMaterial({color:'#b78c78',shininess:20,specular:'#312421'});
  else if(n.startsWith('tweezer'))o.material=steel;
  else if(n.startsWith('immune'))o.material=new THREE.MeshPhysicalMaterial({color:n.charCodeAt(n.length-1)%2?'#e2dbce':'#d6d7cd',roughness:.48,clearcoat:.045,envMapIntensity:.7});
  else if(n.startsWith('debris'))o.material=new THREE.MeshPhongMaterial({color:'#c7b99b',shininess:24,specular:'#3b3327'});
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


// The cut face is an explanatory reveal, not an external wall: avoid floating
// black cell/vessel shadows and coplanar layer acne on that presentation plane.
for(const n of ['skin_front','dermis','basal','collagen','artery','vein','sweat_ducts']){named[n].castShadow=false;named[n].receiveShadow=false;}
named.sweat_ducts.visible=false;
named.collagen.material.transparent=true;named.collagen.material.opacity=.38;named.collagen.material.depthWrite=false;
for(const [n,o] of Object.entries(named))if(n.startsWith('basal_cell'))o.castShadow=false;
// Soft, gently irregular membrane geometry rather than cotton/popcorn shapes.
const membrane=new THREE.SphereGeometry(1,28,20);const mp=membrane.attributes.position;
for(let i=0;i<mp.count;i++){const x=mp.getX(i),y=mp.getY(i),z=mp.getZ(i),q=1+.070*Math.sin(x*4.2+y*2.1)*Math.sin(z*3.8-x);mp.setXYZ(i,x*q,y*q,z*q);}
membrane.computeVertexNormals();
const adipose=new THREE.SphereGeometry(1,28,20);const ap=adipose.attributes.position;
for(let i=0;i<ap.count;i++){const x=ap.getX(i),y=ap.getY(i),z=ap.getZ(i),r=1+.047*Math.sin(x*3.4+z)*Math.cos(y*4.2-x);ap.setXYZ(i,x*r,y*r,z*r);}
adipose.computeVertexNormals();for(const [name,obj] of Object.entries(named))if(/^fat_\d+$/.test(name))obj.geometry=adipose;

for(let i=0;i<32;i++){named['immune_'+i].geometry=membrane;if(i>=design.active_cells)named['immune_'+i].visible=false;}
// Hardware instancing preserves every animated cell transform while replacing
// >150 repetitive draw calls with four batches. Critical on a software GPU.
const instanceBatches=[];
function instanceGroup(names,dynamic=false){
  const objects=names.map(n=>named[n]);if(!objects.length)return;
  const mat=objects[0].material.clone();mat.color.set('#ffffff');
  const batch=new THREE.InstancedMesh(objects[0].geometry,mat,objects.length);
  batch.name='Batch_'+names[0];batch.castShadow=!/^(immune|debris|basal_cell)/.test(names[0]);batch.receiveShadow=!names[0].startsWith('immune_');batch.frustumCulled=false;
  objects[0].parent.add(batch);
  objects.forEach((o,i)=>{batch.setColorAt(i,o.material.color);o.visible=false});
  const update=()=>{objects.forEach((o,i)=>{o.updateMatrix();batch.setMatrixAt(i,o.matrix)});batch.instanceMatrix.needsUpdate=true};
  update();if(dynamic)instanceBatches.push({update});
}
const keys=Object.keys(named);
instanceGroup(keys.filter(n=>/^fat_\d+$/.test(n)));
instanceGroup(keys.filter(n=>n.startsWith('basal_cell')));
instanceGroup(keys.filter(n=>n.startsWith('immune_')).slice(0,design.active_cells),true);
instanceGroup(keys.filter(n=>n.startsWith('debris_')),true);

// Procedural fingertip; palmar skin has no hair follicles. No face/identity asset.
const hand=new THREE.Group();hand.scale.set(.88,1,.90);scene.add(hand);
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
const palm=ellipsoid([-.08,-4.5,-.38],[1.42,1.35,.71],fingerMat);
const curl=ellipsoid([-.87,-3.46,-.42],[.48,.9,.47],fingerMat);curl.rotation.z=-.15;
const thumb=ellipsoid([.83,-3.65,.16],[.55,.95,.46],fingerMat);thumb.rotation.z=-.83;
// This cut is a fingertip macro, not a full-hand shot: keep palm masses out.
palm.visible=curl.visible=thumb.visible=false;
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
const handAxis=new THREE.Group();handAxis.rotation.y=controls.splinter.surface_angle;handToolRoot.add(handAxis);
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

// Two deliberate typographic beats, made from actual extruded glyph meshes.
const typeface=new FontLoader().parse(await (await fetch('./assets/fonts/Montserrat-Cinema.typeface.json')).json());
const heroWords=design.typography.map(cue=>{
  const geom=new TextGeometry(cue.text,{font:typeface,size:cue.size,depth:cue.depth,curveSegments:10,bevelEnabled:true,bevelThickness:cue.bevel,bevelSize:cue.bevel,bevelSegments:3});
  geom.computeBoundingBox();geom.translate(-(geom.boundingBox.min.x+geom.boundingBox.max.x)/2,0,-cue.depth/2);
  const materials=[new THREE.MeshStandardMaterial({color:'#e8e3d7',metalness:.18,roughness:.32,envMapIntensity:.75,transparent:true,opacity:0}),new THREE.MeshStandardMaterial({color:'#697174',metalness:.25,roughness:.39,envMapIntensity:.8,transparent:true,opacity:0})];
  const mesh=new THREE.Mesh(geom,materials);scene.add(mesh);return {cue,mesh};
});
function typography(t){
  for(const {cue,mesh} of heroWords){
    const a=envelope(t,cue.start,cue.in_end),b=1-envelope(t,cue.out_start,cue.end),op=a*b;
    mesh.visible=op>.0001;for(const material of mesh.material){material.opacity=op;material.depthWrite=op>.999;}
    mesh.position.set(...cue.position);mesh.position.y+=(1-a)*-.07;
    mesh.rotation.set(0,cue.yaw+(1-a)*.09,0);mesh.scale.setScalar(.985+.015*a);
  }
}
function background(t){
  b.save();b.scale(S,S);
  const g=b.createRadialGradient(550,710,90,520,860,1330);g.addColorStop(0,design.palette.background_center);g.addColorStop(.63,'#294957');g.addColorStop(1,design.palette.background_edge);
  b.fillStyle=g;b.fillRect(0,0,1080,1920);b.restore();
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
    for(let i=0;i<design.active_cells;i++){const c=motion.cell(i,t),o=named['immune_'+i];o.position.set(...c.position);o.scale.set(...c.scale);o.rotation.set(...c.rotation);}
    for(let i=0;i<18;i++){const c=motion.debris(i,t),o=named['debris_'+i];o.position.set(...c.position);o.scale.set(...c.scale);o.rotation.set(...c.rotation);}
    for(const batch of instanceBatches)batch.update();
    const tool=deepForceps.group;
    tool.visible=t>=controls.cues.deep_approach_start;
    tool.rotation.set(0,controls.splinter.angle,0);
    const along=2.083+1.30*(1-p.deepApproach),x=rawGripCenter*.57+.15*(1-p.deepApproach),a=controls.splinter.angle;
    tool.position.set(p.woodBase[0]+Math.sin(a)*along+Math.cos(a)*x,p.woodBase[1],p.woodBase[2]+Math.cos(a)*along-Math.sin(a)*x);
    deepForceps.setClosed(p.deepClose);
    heatUniform.value=p.heat;
  }
  camera.updateMatrixWorld();return p;
}
// Plain editorial subtitles: no boxes, accent colours, badges or HUD layers.
function overlay(t){
  ctx.clearRect(0,0,W,H);ctx.save();ctx.scale(S,S);
  const c=timeline.captions.find(c=>t>=c.start&&t<c.end);
  if(c){
    let size=design.caption_font_px;ctx.font=`550 ${size}px Montserrat`;
    while(ctx.measureText(c.text).width>916){size--;ctx.font=`550 ${size}px Montserrat`;}
    ctx.globalAlpha=envelope(t,c.start,c.start+.10)*(1-envelope(t,c.end-.07,c.end));
    ctx.textAlign='center';ctx.textBaseline='alphabetic';
    ctx.lineJoin='round';ctx.lineWidth=3.4;ctx.strokeStyle='#0915199c';ctx.fillStyle='#f3f1e9';ctx.shadowColor='#061218a0';ctx.shadowBlur=8;
    const y=design.caption_y+4*(1-envelope(t,c.start,c.start+.13));
    ctx.strokeText(c.text,540,y);ctx.fillText(c.text,540,y);
  }
  ctx.restore();
}
window.renderAt=(t)=>{t=clamp(t,0,timeline.duration-.0001);background(t);const p=pose(t);typography(t);renderer.info.reset();composer.render();overlay(t);return {time:t,shot:timeline.shots.find(s=>t>=s.start&&t<s.end)?.id,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,camera:p.camera,surfaceLift:p.surfaceLift,deepLift:p.deepLift}};
const deliveryCanvas=document.createElement('canvas');deliveryCanvas.width=W;deliveryCanvas.height=H;const deliveryCtx=deliveryCanvas.getContext('2d',{alpha:false,willReadFrequently:true});
window.exportFrame=(kind='png')=>{deliveryCtx.drawImage(bg,0,0);deliveryCtx.drawImage(renderer.domElement,0,0);deliveryCtx.drawImage(hud,0,0);return deliveryCanvas.toDataURL(kind==='png'?'image/png':'image/jpeg',.99).split(',')[1]};
window.motionState=t=>motion.sample(t);window.flush=()=>renderer.getContext().finish();
window.geometryInfo={gripHalfRaw:rawGripHalf,surfaceGap:surfaceForceps.closedGap,deepGap:deepForceps.closedGap,heroTextMeshes:heroWords.map(x=>({text:x.cue.text,type:x.mesh.geometry.type,vertices:x.mesh.geometry.attributes.position.count,depth:x.cue.depth})),hudDecorations:0};
window.filmInfo={version:4,real3dType:2,activeCells:design.active_cells,width:W,height:H,fps:timeline.fps,triangles:0,native3d:true,duration:timeline.duration,interpolation:'C2 object/camera keyframes; no optical-flow generated frames'};
window.renderAt(0.8);
window.filmInfo.triangles=renderer.info.render.triangles;
window.ready=true;
if(params.get('play')==='1'){
  const button=document.querySelector('#controls');button.hidden=false;let playing=false,start=0,hold=0;
  button.onclick=()=>{playing=!playing;if(playing)start=performance.now()-hold*1000};
  const loop=now=>{if(playing){hold=((now-start)/1000)%timeline.duration;window.renderAt(hold)}requestAnimationFrame(loop)};requestAnimationFrame(loop);
}

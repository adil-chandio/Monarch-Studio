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
import {director} from './director.mjs';
import {SelectiveFocusPass} from './focus-pass.js';

const params = new URLSearchParams(location.search);
const W = Number(params.get('w') || 1080), H = W * 16 / 9;
const stage = document.querySelector('#stage');
stage.style.width = W + 'px'; stage.style.height = H + 'px';
const timeline = await (await fetch('./data/timeline.json')).json();
const controls=await (await fetch('./data/motion.json')).json();
const motion=controller(controls);
const design=await (await fetch('./data/design.json')).json();
const shotPlan=await (await fetch('./data/shot_plan.json')).json();
const cinematography=director(shotPlan,motion,controls);
await document.fonts.load('600 46px Montserrat');
await document.fonts.ready;
const renderer = new THREE.WebGLRenderer({antialias:false, alpha:true, preserveDrawingBuffer:true});
renderer.setSize(W,H); renderer.setPixelRatio(1); renderer.setClearColor(0,0);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.07;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.domElement.style.zIndex='1';
const bg = document.createElement('canvas'), hud=document.createElement('canvas'), sceneCanvas=document.createElement('canvas');
for(const c of [bg,hud,sceneCanvas]) {c.width=W;c.height=H;c.style.width=W+'px';c.style.height=H+'px';}
bg.style.zIndex='0';hud.style.zIndex='2';sceneCanvas.style.zIndex='1';
stage.append(bg,sceneCanvas,hud);
const sceneComposite=sceneCanvas.getContext('2d',{willReadFrequently:true});
const b=bg.getContext('2d',{willReadFrequently:true}),ctx=hud.getContext('2d',{willReadFrequently:true});
const S=W/1080;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(32,W/H,.06,80);
const composer = new EffectComposer(renderer);
composer.setSize(W,H);
composer.addPass(new RenderPass(scene,camera));
const focusPass=new SelectiveFocusPass(scene,camera);composer.addPass(focusPass);
composer.addPass(new OutputPass());
const fxaa=new ShaderPass(FXAAShader);fxaa.material.uniforms.resolution.value.set(1/W,1/H);composer.addPass(fxaa);
renderer.info.autoReset=false;
const pmrem = new THREE.PMREMGenerator(renderer);
const room = new RoomEnvironment();
scene.environment=pmrem.fromScene(room,.08).texture;
scene.environmentIntensity=.28;room.dispose();pmrem.dispose();
scene.add(new THREE.HemisphereLight('#c4d7de','#503a34',.53));
const key = new THREE.DirectionalLight('#fff2e6',2.48);
key.position.set(-4.5,6,7); key.target.position.set(0,-1,0);
key.castShadow=true;key.shadow.mapSize.set(2048,2048);
Object.assign(key.shadow.camera,{left:-5,right:5,top:5,bottom:-5,near:.5,far:22});
key.shadow.bias=-.0003;key.shadow.normalBias=.022;key.shadow.radius=3;
scene.add(key,key.target);
const fill=new THREE.DirectionalLight('#b9d4e7',.65);fill.position.set(4,2,5);scene.add(fill);
const rim=new THREE.DirectionalLight('#d6ebf5',2.05);rim.position.set(3,3,-5);scene.add(rim);
const soft=new THREE.PointLight('#e6c2ac',2.2,14,2);soft.position.set(-2,-1,3);scene.add(soft);

const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const ease=smoother;
const range=(t,a,b)=>ease((t-a)/(b-a));
const lerp=THREE.MathUtils.lerp;
const vec=(a)=>new THREE.Vector3(...a);
let seed=40217;
const rnd=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296};

// Independently authored procedural albedo and pore/ridge bump maps.
function tissueTexture(kind='skin',N=768) {
  const c=document.createElement('canvas'),bump=document.createElement('canvas'),rough=document.createElement('canvas');
  for(const canvas of [c,bump,rough])canvas.width=canvas.height=N;
  const x=c.getContext('2d'),bx=bump.getContext('2d'),rx=rough.getContext('2d');const im=x.createImageData(N,N),bi=bx.createImageData(N,N),ri=rx.createImageData(N,N);
  const hash=(i,j)=>{const n=Math.sin(i*127.1+j*311.7)*43758.5453;return n-Math.floor(n)};
  const centers=[];for(let y=-1;y<=19;y++){const row=[];for(let x=-1;x<=31;x++)row.push([x+.18+.64*hash(x,y),y+.18+.64*hash(y+71,x+23)]);centers.push(row)}
  for(let j=0;j<N;j++)for(let i=0;i<N;i++){
    const u=i/N,v=j/N,n=rnd()-.5;let detail=0,bumpValue=128,shade=0;
    if(kind==='finger'){
      const mask=Math.exp(-((u-.25)**2/.019+(v-.16)**2/.050));
      const dist=Math.sqrt((u-.25)**2*1.7+(v-.16)**2*2.4);
      const ridge=Math.sin(dist*500+Math.sin(u*12)*.55+Math.sin(v*8)*.35);
      shade=-Math.pow(.5+.5*ridge,7)*3.6*mask;
      bumpValue=128+ridge*(1.2+19*mask)+n*12;
      detail=n*3.3+.7*Math.sin(u*63+v*41);
    }else if(kind==='skin'||kind==='surface'){
      const px=u*30,py=v*18,gx=Math.floor(px),gy=Math.floor(py);let d1=100,d2=100;
      for(let yy=gy-1;yy<=gy+1;yy++)for(let xx=gx-1;xx<=gx+1;xx++){
        const pt=centers[yy+1][xx+1],d=(px-pt[0])**2+(py-pt[1])**2;
        if(d<d1){d2=d1;d1=d}else if(d<d2)d2=d;
      }
      const edge=Math.exp(-(Math.sqrt(d2)-Math.sqrt(d1))*14);
      shade=-(kind==='surface'?8.5:3.8)*edge;detail=n*3.2+1.2*Math.sin(u*22+v*9);bumpValue=132+(kind==='surface'?22:11)*(1-edge)+n*8;
    }else{
      const fiber=Math.sin(u*78+Math.sin(v*19)*1.6+.3*Math.sin(u*9));
      const marble=Math.sin(u*8+v*9)+.55*Math.sin(u*16-v*6);
      detail=marble*2.4+n*3.9;shade=fiber*.7;bumpValue=128+fiber*3.5+n*12;
    }
    const rgb=kind==='dermis'?[173,83,80]:kind==='finger'?[194,142,117]:kind==='surface'?[197,136,117]:[199,143,124],at=(j*N+i)*4;
    for(let k=0;k<3;k++){im.data[at+k]=rgb[k]+detail+shade;bi.data[at+k]=bumpValue;ri.data[at+k]=242+n*15;}
    im.data[at+3]=bi.data[at+3]=ri.data[at+3]=255;
  }
  x.putImageData(im,0,0);bx.putImageData(bi,0,0);rx.putImageData(ri,0,0);
  const map=new THREE.CanvasTexture(c),bumpMap=new THREE.CanvasTexture(bump),roughnessMap=new THREE.CanvasTexture(rough);map.colorSpace=THREE.SRGBColorSpace;
  for(const t of [map,bumpMap,roughnessMap])t.anisotropy=4;
  return {map,bumpMap,roughnessMap};
}
const skinTex=tissueTexture('skin'),dermisTex=tissueTexture('dermis'),fingerTex=tissueTexture('finger');
const skinMat=new THREE.MeshPhysicalMaterial({...skinTex,roughness:.43,clearcoat:.065,clearcoatRoughness:.5,bumpScale:.010,envMapIntensity:.8});
const fingerMat=new THREE.MeshPhysicalMaterial({...fingerTex,roughness:.44,clearcoat:.07,clearcoatRoughness:.55,bumpScale:.008,envMapIntensity:.8});
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
// Longitudinal wood fibres and restrained brushed-steel roughness, rather
// than a uniform brown rod or featureless metal. No photographic scene plate.
function woodSurface(){
  const c=document.createElement('canvas'),b=document.createElement('canvas');c.width=b.width=512;c.height=b.height=1024;
  const x=c.getContext('2d'),bx=b.getContext('2d'),im=x.createImageData(512,1024),bi=bx.createImageData(512,1024);
  for(let y=0;y<1024;y++)for(let i=0;i<512;i++){
    const u=i/512,v=y/1024,n=rnd()-.5,f=.6*Math.sin(u*170+Math.sin(v*11)*.45)+.4*Math.sin(u*417+v*3.2),grain=f*10+n*5;
    const k=(y*512+i)*4;im.data[k]=103+grain;im.data[k+1]=64+grain*.70;im.data[k+2]=36+grain*.43;im.data[k+3]=255;
    bi.data[k]=bi.data[k+1]=bi.data[k+2]=128+f*19+n*10;bi.data[k+3]=255;
  }
  x.putImageData(im,0,0);bx.putImageData(bi,0,0);const map=new THREE.CanvasTexture(c);map.colorSpace=THREE.SRGBColorSpace;map.anisotropy=4;
  return new THREE.MeshStandardMaterial({map,bumpMap:new THREE.CanvasTexture(b),bumpScale:.0045,roughness:.68,envMapIntensity:.45});
}
const grainGeometry=named.splinter.geometry.clone(),gp=grainGeometry.attributes.position,guv=new Float32Array(gp.count*2);
for(let i=0;i<gp.count;i++){guv[i*2]=Math.atan2(gp.getY(i),gp.getX(i))/(Math.PI*2)+.5;guv[i*2+1]=gp.getZ(i)/2.12;}
grainGeometry.setAttribute('uv',new THREE.BufferAttribute(guv,2));named.splinter.geometry=grainGeometry;named.splinter.material=woodSurface();
const brushCanvas=document.createElement('canvas');brushCanvas.width=brushCanvas.height=256;const br=brushCanvas.getContext('2d'),brim=br.createImageData(256,256);
for(let y=0;y<256;y++)for(let x=0;x<256;x++){const at=(y*256+x)*4,v=223+9*Math.sin(x*2.17)+3*(rnd()-.5);brim.data[at]=brim.data[at+1]=brim.data[at+2]=v;brim.data[at+3]=255;}
br.putImageData(brim,0,0);steel.roughnessMap=new THREE.CanvasTexture(brushCanvas);steel.roughness=.23;steel.envMapIntensity=2.3;steel.needsUpdate=true;
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
instanceGroup(keys.filter(n=>n.startsWith('immune_')).slice(0,design.active_cells).filter(n=>!design.hero_cells.includes(Number(n.split('_')[1]))),true);
instanceGroup(keys.filter(n=>n.startsWith('debris_')),true);

// New hero-cell geometry: a softly translucent membrane and understated
// segmented inner forms. Stylized immune-cell anatomy, not microscopy footage.
const heroCells=design.hero_cells.map(index=>{
  const original=named['immune_'+index];original.visible=false;
  const group=new THREE.Group();group.name='HeroCell_'+index;original.parent.add(group);
  const shellMaterial=new THREE.MeshPhysicalMaterial({color:'#e2dfd1',roughness:.48,clearcoat:.035,transparent:true,opacity:.60,depthWrite:false,envMapIntensity:.55});
  const shell=new THREE.Mesh(membrane,shellMaterial);shell.renderOrder=3;group.add(shell);
  const cytoplasm=new THREE.Mesh(new THREE.SphereGeometry(.76,28,20),new THREE.MeshStandardMaterial({color:'#d8d6c5',roughness:.76,envMapIntensity:.4}));group.add(cytoplasm);
  const nucleusMaterial=new THREE.MeshStandardMaterial({color:'#566184',roughness:.7,envMapIntensity:.4});
  for(const [position,scale] of [[[-.24,-.68,.10],[.29,.18,.32]],[[.15,-.65,-.18],[.30,.19,.31]],[[.22,-.66,.24],[.27,.18,.29]]]){
    const n=new THREE.Mesh(new THREE.SphereGeometry(1,24,16),nucleusMaterial);n.position.set(...position);n.scale.set(...scale);group.add(n);
  }
  return {index,group,shell};
});
// Independent intact-surface macro insert. The older cross-section GLB draws
// internal actors in front of its reveal plane; this insert avoids pretending
// those presentation offsets are physically beneath an intact surface.
const surfaceScene=new THREE.Group();surfaceScene.name='IntactSkinMacro';scene.add(surfaceScene);
const surfaceTexture=tissueTexture('surface',1536);
const surfaceMaterial=new THREE.MeshPhysicalMaterial({...surfaceTexture,roughness:.44,clearcoat:.065,clearcoatRoughness:.48,bumpScale:.028,envMapIntensity:.7});
const N=112,A=192,span=12,spos=[],suv=[],sidx=[];
const surfaceHeight=(x,z)=>.005*Math.sin(x*5.7+z*.8)*Math.cos(z*4.8)-.023*Math.exp(-((x/.09)**2+(z/.075)**2));
// Annular radial topology gives a real smooth narrow slit, not missing square
// grid cells. Dense samples at the opening and a broad offscreen outer patch.
for(let j=0;j<=N;j++)for(let i=0;i<=A;i++){
 const angle=i/A*Math.PI*2,q=(j/N)**1.7;
 const x=Math.cos(angle)*(.024+(6-.024)*q),z=Math.sin(angle)*(.065+(6-.065)*q);
 spos.push(x,surfaceHeight(x,z),z);suv.push(x/4.8+.5,z/4.8+.5);
 if(j<N&&i<A){const a=j*(A+1)+i;sidx.push(a,a+1,a+A+1,a+1,a+A+2,a+A+1);}
}
for(const texture of Object.values(surfaceTexture)){texture.wrapS=texture.wrapT=THREE.RepeatWrapping;texture.needsUpdate=true;}
const surfaceGeometry=new THREE.BufferGeometry();surfaceGeometry.setAttribute('position',new THREE.Float32BufferAttribute(spos,3));surfaceGeometry.setAttribute('uv',new THREE.Float32BufferAttribute(suv,2));surfaceGeometry.setIndex(sidx);surfaceGeometry.computeVertexNormals();
const surfaceMesh=new THREE.Mesh(surfaceGeometry,surfaceMaterial);surfaceMesh.receiveShadow=true;surfaceScene.add(surfaceMesh);
const tissueUnderlay=new THREE.Mesh(new THREE.BoxGeometry(12,.35,12),new THREE.MeshStandardMaterial({color:'#97594a',roughness:.85}));tissueUnderlay.position.y=-.225;surfaceScene.add(tissueUnderlay);
const cavity=new THREE.Mesh(new THREE.SphereGeometry(1,32,20),new THREE.MeshStandardMaterial({color:'#58372e',roughness:.86}));cavity.position.set(0,-.059,0);cavity.scale.set(.034,.022,.050);surfaceScene.add(cavity);
const rimPoints=[];for(let i=0;i<=64;i++){const a=i/64*Math.PI*2,x=.032*Math.cos(a),z=.047*Math.sin(a);rimPoints.push(new THREE.Vector3(x,surfaceHeight(x,z)+.001,z));}
const apertureRim=new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(rimPoints),64,.0035,8,true),new THREE.MeshStandardMaterial({color:'#ae7b69',roughness:.60}));surfaceScene.add(apertureRim);apertureRim.visible=false;
const buriedWood=new THREE.Mesh(named.splinter.geometry,named.splinter.material);buriedWood.rotation.x=-Math.PI/2;buriedWood.position.set(.001,-.277,.012);buriedWood.scale.set(.16,.14,.12);surfaceScene.add(buriedWood);
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
for(let i=0;i<fingerWeights.length;i++){const [x,y,z]=fingerRest.slice(i*3,i*3+3);fingerWeights[i]=Math.exp(-((x-.17)**2+(z-.11)**2)/.035)*envelope(y,-.12,.38);}
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
  const g=b.createRadialGradient(550,710,90,520,860,1330);g.addColorStop(0,design.palette.background_center);g.addColorStop(.63,design.palette.background_mid);g.addColorStop(1,design.palette.background_edge);
  b.fillStyle=g;b.fillRect(0,0,1080,1920);b.restore();
}
function pose(t){
  const p=motion.sample(t),view=cinematography.sample(t,p),v=view.camera;
  anatomy.visible=view.scene==='anatomy';hand.visible=view.scene==='finger';surfaceScene.visible=view.scene==='surface';
  camera.position.set(v[0],v[1],v[2]);camera.lookAt(v[3],v[4],v[5]);camera.fov=v[6];camera.updateProjectionMatrix();focusPass.setFocus(view);
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
    for(const h of heroCells){const c=motion.cell(h.index,t);h.group.position.set(...c.position);h.group.scale.set(...c.scale);h.group.rotation.set(...c.rotation);}
    const tool=deepForceps.group;
    tool.visible=t>=controls.cues.deep_approach_start;
    tool.rotation.set(0,controls.splinter.angle,0);
    const along=2.083+1.30*(1-p.deepApproach),x=rawGripCenter*.57+.15*(1-p.deepApproach),a=controls.splinter.angle;
    tool.position.set(p.woodBase[0]+Math.sin(a)*along+Math.cos(a)*x,p.woodBase[1],p.woodBase[2]+Math.cos(a)*along-Math.sin(a)*x);
    deepForceps.setClosed(p.deepClose);
    heatUniform.value=p.heat;
  }
  camera.updateMatrixWorld();return {...p,camera:v,director:view};
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
window.renderAt=(t)=>{
  t=clamp(t,0,timeline.duration-.0001);background(t);renderer.info.reset();
  const active=controls.shutter.windows.some(([a,b])=>t>=a&&t<=b)&&!cinematography.cuts.some(c=>Math.abs(t-c)<=controls.shutter.no_cross_scene_blend_seconds);
  const samples=active?[-controls.shutter.half_exposure_seconds,0,controls.shutter.half_exposure_seconds]:[0];
  sceneComposite.clearRect(0,0,W,H);sceneComposite.globalCompositeOperation='lighter';sceneComposite.globalAlpha=1;
  for(let j=0;j<samples.length;j++){const dt=samples[j];sceneComposite.globalAlpha=active?controls.shutter.weights[j]:1;const time=clamp(t+dt,0,timeline.duration-.0001);pose(time);typography(time);composer.render();sceneComposite.drawImage(renderer.domElement,0,0);}
  sceneComposite.globalCompositeOperation='source-over';sceneComposite.globalAlpha=1;overlay(t);
  const p=motion.sample(t),view=cinematography.sample(t,p);
  return {time:t,shot:view.shot,view:view.description,focusDistance:view.focusDistance,focusEnabled:view.focusStrength>0,sceneGroup:view.scene,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,camera:view.camera,surfaceLift:p.surfaceLift,deepLift:p.deepLift,shutterSamples:samples.length};
};
const deliveryCanvas=document.createElement('canvas');deliveryCanvas.width=W;deliveryCanvas.height=H;const deliveryCtx=deliveryCanvas.getContext('2d',{alpha:false,willReadFrequently:true});
window.exportFrame=(kind='png')=>{deliveryCtx.drawImage(bg,0,0);deliveryCtx.drawImage(sceneCanvas,0,0);deliveryCtx.drawImage(hud,0,0);return deliveryCanvas.toDataURL(kind==='png'?'image/png':'image/jpeg',.99).split(',')[1]};
window.motionState=t=>({actor:motion.sample(t),director:cinematography.sample(t)});window.flush=()=>renderer.getContext().finish();
window.geometryInfo={newSurfaceVertices:surfaceGeometry.attributes.position.count,newHeroCells:heroCells.length,heroNucleusLobesPerCell:3,depthFocusMethod:'geometry-depth-guided separable Gaussian',intentionalCuts:cinematography.cuts,gripHalfRaw:rawGripHalf,surfaceGap:surfaceForceps.closedGap,deepGap:deepForceps.closedGap,heroTextMeshes:heroWords.map(x=>({text:x.cue.text,type:x.mesh.geometry.type,vertices:x.mesh.geometry.attributes.position.count,depth:x.cue.depth})),hudDecorations:0};
window.filmInfo={version:6,directorShots:shotPlan.shots.length,newSurfaceInsert:true,heroCells:heroCells.length,geometryDepthFocus:true,sceneShutterSamples:controls.shutter.samples,shutterExposure:controls.shutter.half_exposure_seconds*2,real3dType:2,activeCells:design.active_cells,width:W,height:H,fps:timeline.fps,triangles:0,native3d:true,duration:timeline.duration,interpolation:'Faster C2 move/settle controls; real scene-only shutter samples during fast movement, no optical flow' };
window.renderAt(0.8);
window.filmInfo.triangles=renderer.info.render.triangles;
window.ready=true;
if(params.get('play')==='1'){
  const button=document.querySelector('#controls');button.hidden=false;let playing=false,start=0,hold=0;
  button.onclick=()=>{playing=!playing;if(playing)start=performance.now()-hold*1000};
  const loop=now=>{if(playing){hold=((now-start)/1000)%timeline.duration;window.renderAt(hold)}requestAnimationFrame(loop)};requestAnimationFrame(loop);
}

/* Geometry-depth guided selective focus. A separable Gaussian image is mixed
 * with the sharp linear scene using actual camera-space depth. This avoids
 * sparse-kernel double contours; captions are composited after the effect.
 * It is a restrained art-directed focus approximation, not a calibrated lens.
 */
import * as THREE from 'three';
import {Pass,FullScreenQuad} from 'three/addons/postprocessing/Pass.js';
const vertex='varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.0,1.0);}';
export class SelectiveFocusPass extends Pass{
 constructor(scene,camera){
  super();this.scene=scene;this.camera=camera;this.needsSwap=true;
  this.depthTarget=new THREE.WebGLRenderTarget(360,640,{minFilter:THREE.NearestFilter,magFilter:THREE.NearestFilter,depthBuffer:true,stencilBuffer:false});
  this.blurA=new THREE.WebGLRenderTarget(540,960,{type:THREE.HalfFloatType,depthBuffer:false,stencilBuffer:false});this.blurB=this.blurA.clone();
  this.depthMaterial=new THREE.MeshDepthMaterial({depthPacking:THREE.RGBADepthPacking,blending:THREE.NoBlending,side:THREE.DoubleSide});
  this.uniforms={tDiffuse:{value:null},tBlur:{value:this.blurB.texture},tDepth:{value:this.depthTarget.texture},nearClip:{value:.06},farClip:{value:80},focusDistance:{value:6},focusRange:{value:.18},strength:{value:0},maxBlur:{value:0}};
  this.blurUniforms={tDiffuse:{value:null},stepUV:{value:new THREE.Vector2()}};
  this.blurMaterial=new THREE.ShaderMaterial({uniforms:this.blurUniforms,depthWrite:false,depthTest:false,vertexShader:vertex,fragmentShader:`varying vec2 vUv;uniform sampler2D tDiffuse;uniform vec2 stepUV;void main(){vec4 c=texture2D(tDiffuse,vUv)*.2270270270;c+=(texture2D(tDiffuse,vUv+stepUV*1.3846153846)+texture2D(tDiffuse,vUv-stepUV*1.3846153846))*.3162162162;c+=(texture2D(tDiffuse,vUv+stepUV*3.2307692308)+texture2D(tDiffuse,vUv-stepUV*3.2307692308))*.0702702703;gl_FragColor=c;}`});
  this.material=new THREE.ShaderMaterial({uniforms:this.uniforms,depthWrite:false,depthTest:false,vertexShader:vertex,fragmentShader:`
   #include <packing>
   varying vec2 vUv;uniform sampler2D tDiffuse,tBlur,tDepth;uniform float nearClip,farClip,focusDistance,focusRange,strength,maxBlur;
   void main(){float depth=unpackRGBAToDepth(texture2D(tDepth,vUv));float distance=-perspectiveDepthToViewZ(depth,nearClip,farClip);float amount=clamp((abs(distance-focusDistance)-focusRange)*strength/max(maxBlur,.001),0.0,1.0);amount=amount*amount*(3.0-2.0*amount);gl_FragColor=mix(texture2D(tDiffuse,vUv),texture2D(tBlur,vUv),amount);}`});
  this.quad=new FullScreenQuad(this.material);this.blurQuad=new FullScreenQuad(this.blurMaterial);this.savedColor=new THREE.Color();this.width=1080;this.height=1920;
 }
 setSize(w,h){this.width=w;this.height=h;this.depthTarget.setSize(Math.max(1,Math.round(w/3)),Math.max(1,Math.round(h/3)));this.blurA.setSize(Math.max(1,Math.round(w/2)),Math.max(1,Math.round(h/2)));this.blurB.setSize(Math.max(1,Math.round(w/2)),Math.max(1,Math.round(h/2)))}
 setFocus(info){const scale=this.width/1080;this.uniforms.focusDistance.value=info.focusDistance;this.uniforms.focusRange.value=info.focusRange;this.uniforms.strength.value=info.focusStrength*scale;this.uniforms.maxBlur.value=info.maxBlur*scale;this.enabled=info.focusStrength>0.01&&info.maxBlur>0}
 render(renderer,writeBuffer,readBuffer){
  const mat=this.scene.overrideMaterial,bg=this.scene.background,alpha=renderer.getClearAlpha(),shadowUpdate=renderer.shadowMap.autoUpdate;renderer.getClearColor(this.savedColor);
  try{this.scene.overrideMaterial=this.depthMaterial;this.scene.background=null;renderer.shadowMap.autoUpdate=false;renderer.setClearColor(0xffffff,1);renderer.setRenderTarget(this.depthTarget);renderer.clear();renderer.render(this.scene,this.camera)}
  finally{this.scene.overrideMaterial=mat;this.scene.background=bg;renderer.shadowMap.autoUpdate=shadowUpdate;renderer.setClearColor(this.savedColor,alpha)}
  const radius=this.uniforms.maxBlur.value/3.2307692308;
  this.blurUniforms.tDiffuse.value=readBuffer.texture;this.blurUniforms.stepUV.value.set(radius/this.width,0);renderer.setRenderTarget(this.blurA);this.blurQuad.render(renderer);
  this.blurUniforms.tDiffuse.value=this.blurA.texture;this.blurUniforms.stepUV.value.set(0,radius/this.height);renderer.setRenderTarget(this.blurB);this.blurQuad.render(renderer);
  this.uniforms.tDiffuse.value=readBuffer.texture;this.uniforms.nearClip.value=this.camera.near;this.uniforms.farClip.value=this.camera.far;
  renderer.setRenderTarget(this.renderToScreen?null:writeBuffer);if(this.clear)renderer.clear();this.quad.render(renderer);
 }
 dispose(){for(const t of [this.depthTarget,this.blurA,this.blurB])t.dispose();for(const m of [this.depthMaterial,this.material,this.blurMaterial])m.dispose();this.quad.dispose();this.blurQuad.dispose()}
}

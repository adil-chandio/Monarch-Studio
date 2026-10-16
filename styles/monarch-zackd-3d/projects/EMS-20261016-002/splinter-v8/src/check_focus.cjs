#!/usr/bin/env node
// Isolated A/B proof: expose diagnostic handles in the in-memory served module,
// never alter the frozen production film.js. Focus must change the scene image
// while the actual caption canvas remains byte-identical.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium:pw}=require('playwright-core'),chromium=require('@sparticuz/chromium');
const root=path.resolve(__dirname,'..'),three=path.resolve(path.dirname(require.resolve('three')),'..'),out=path.resolve(process.argv[2]||path.join(root,'build'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const browser=await pw.launch({headless:true,executablePath:await chromium.executablePath(),args:chromium.args,env:{...process.env,LD_LIBRARY_PATH:path.join(out,'runtime-libs/lib')+':'+(process.env.LD_LIBRARY_PATH||'')}});
 try{
  const page=await browser.newPage({viewport:{width:540,height:960},deviceScaleFactor:1});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.route('**/*',async r=>{const u=new URL(r.request().url());if(u.hostname!=='monarch-render.invalid')throw Error('External URL rejected');const p=decodeURIComponent(u.pathname),vendor=p.startsWith('/vendor/three/'),base=vendor?three:root,file=path.resolve(base,vendor?p.slice(14):p.slice(1)||'index.html');if(!file.startsWith(base+path.sep))throw Error('Path rejected');let body=fs.readFileSync(file);if(file===path.join(root,'src/film.js'))body=Buffer.from(body.toString()+"\nwindow.__focusProof={pass:focusPass,hud};\n");const mime={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.glb':'model/gltf-binary','.ttf':'font/ttf'};await r.fulfill({body,contentType:mime[path.extname(file)]||'application/octet-stream'});});
  await page.goto('http://monarch-render.invalid/index.html?w=540');await page.waitForFunction(()=>window.ready,null,{timeout:120000});
  const proofs=[];
  for(const t of [7.8,9.3,27.4]){
   await page.evaluate(t=>window.renderAt(t),t);
   const on=await page.evaluate(()=>({image:window.exportFrame('png'),hud:window.__focusProof.hud.toDataURL('image/png').split(',')[1],distance:window.__focusProof.pass.uniforms.focusDistance.value,maxBlur:window.__focusProof.pass.uniforms.maxBlur.value}));
   await page.evaluate(()=>{const p=window.__focusProof.pass;p.savedSetFocus=p.setFocus;p.setFocus=function(){this.enabled=false}});
   await page.evaluate(t=>window.renderAt(t),t);
   const off=await page.evaluate(()=>({image:window.exportFrame('png'),hud:window.__focusProof.hud.toDataURL('image/png').split(',')[1]}));
   await page.evaluate(()=>{const p=window.__focusProof.pass;p.setFocus=p.savedSetFocus});
   const onImage=Buffer.from(on.image,'base64'),offImage=Buffer.from(off.image,'base64');fs.writeFileSync(path.join(out,`focus-on-${t}.png`),onImage);fs.writeFileSync(path.join(out,`focus-off-${t}.png`),offImage);
   proofs.push({time:t,scene_image_changes:hash(onImage)!==hash(offImage),caption_canvas_identical:on.hud===off.hud,focus_distance:on.distance,preview_blur_px:on.maxBlur,on_sha256:hash(onImage),off_sha256:hash(offImage)});
  }
  const result={passed:errors.length===0&&proofs.every(p=>p.scene_image_changes&&p.caption_canvas_identical),method:'Same actual3D timestamp, production focus pass on/off in an isolated browser; compare scene PNG and raw caption canvas separately',proofs,errors};fs.writeFileSync(path.join(out,'FOCUS_QA.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));if(!result.passed)process.exitCode=1;
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});

#!/usr/bin/env node
// Isolated diagnostic injection only. Frozen production scene is not modified.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium:pw}=require('playwright-core'),chromium=require('@sparticuz/chromium');
const root=path.resolve(__dirname,'..'),three=path.resolve(path.dirname(require.resolve('three')),'..');
const out=path.resolve(process.argv[2]||path.join(root,'build'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const browser=await pw.launch({headless:true,executablePath:await chromium.executablePath(),args:chromium.args,env:{...process.env,LD_LIBRARY_PATH:path.join(out,'runtime-libs/lib')+':'+(process.env.LD_LIBRARY_PATH||'')}});
 try{
  const page=await browser.newPage({viewport:{width:540,height:960},deviceScaleFactor:1});const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  await page.route('**/*',async r=>{
   const u=new URL(r.request().url());if(u.hostname!=='monarch-render.invalid')throw Error('External URL rejected');
   const p=decodeURIComponent(u.pathname),vendor=p.startsWith('/vendor/three/'),base=vendor?three:root;
   const file=path.resolve(base,vendor?p.slice(14):p.slice(1)||'index.html');if(!file.startsWith(base+path.sep))throw Error('Path rejected');
   let body=fs.readFileSync(file);
   if(file===path.join(root,'src/film.js')){
    let s=body.toString();if(!s.includes('const k=1+ripple+leading;'))throw Error('Production deformation anchor missing');
    s=s.replace('const k=1+ripple+leading;','const k=window.__disableOrganic?1:1+ripple+leading;');
    body=Buffer.from(s+'\nwindow.__organicProof={heroCells,hud};\n');
   }
   const mime={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.glb':'model/gltf-binary','.ttf':'font/ttf'};
   await r.fulfill({body,contentType:mime[path.extname(file)]||'application/octet-stream'});
  });
  await page.goto('http://monarch-render.invalid/index.html?w=540');await page.waitForFunction(()=>window.ready,null,{timeout:120000});
  const samples=[];
  for(const time of [9.3,10.7,13.7,9.3]){
   await page.evaluate(t=>window.renderAt(t),time);
   const state=await page.evaluate(()=>({
    cells:window.__organicProof.heroCells.map(h=>{
     const a=h.shell.geometry.attributes.position.array;let max=0,finite=true;
     for(let i=0;i<a.length;i++){finite=finite&&Number.isFinite(a[i]);max=Math.max(max,Math.abs(a[i]-h.rest[i]));}
     return {index:h.index,positions:Array.from(a),vertexCount:a.length/3,maxDisplacement:max,finite,opacity:h.shell.material.opacity};
    }),image:window.exportFrame('png'),caption:window.__organicProof.hud.toDataURL('image/png')
   }));
   const cells=state.cells.map(c=>({...c,positions:undefined,positionHash:hash(Buffer.from(JSON.stringify(c.positions)))}));
   if(samples.length<3)fs.writeFileSync(path.join(out,`organic-on-${time}.png`),Buffer.from(state.image,'base64'));
   await page.evaluate(t=>{window.__disableOrganic=true;window.renderAt(t)},time);
   const off=await page.evaluate(()=>({image:window.exportFrame('png'),caption:window.__organicProof.hud.toDataURL('image/png')}));
   await page.evaluate(()=>{window.__disableOrganic=false});
   samples.push({time,cells,imageChanges:hash(Buffer.from(state.image,'base64'))!==hash(Buffer.from(off.image,'base64')),captionUnchanged:state.caption===off.caption});
  }
  const repeat=samples[0].cells.every((c,i)=>c.positionHash===samples[3].cells[i].positionHash);
  const moves=samples[0].cells.every((c,i)=>c.positionHash!==samples[1].cells[i].positionHash);
  const bounded=samples.every(s=>s.cells.every(c=>c.vertexCount>=1500&&c.finite&&c.maxDisplacement>.001&&c.maxDisplacement<.05));
  const result={passed:errors.length===0&&repeat&&moves&&bounded&&samples.every(s=>s.imageChanges&&s.captionUnchanged),scope:'Three stylized hero membranes only; no biological mechanics claim. Same-time picture A/B, absolute-time return, geometry density and deformation bounds.',repeatIsExact:repeat,membranesMove:moves,bounded,samples,errors};
  fs.writeFileSync(path.join(out,'ORGANIC_QA.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));if(!result.passed)process.exitCode=1;
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});

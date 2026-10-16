#!/usr/bin/env node
// Small native-scene integration check. Revisit an anatomical timestamp after
// unrelated shots and verify its picture region is bit-identical; catches accumulated
// scale, stale visibility and incremental-animation bugs.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium:pw}=require('playwright-core'),chromium=require('@sparticuz/chromium');
const root=path.resolve(__dirname,'..'),three=path.resolve(path.dirname(require.resolve('three')),'..');
const out=path.resolve(process.argv[2]||path.join(root,'build'));
const lib=process.env.CHROMIUM_LIB_DIR||path.join(out,'runtime-libs/lib');
(async()=>{
  const browser=await pw.launch({headless:true,executablePath:await chromium.executablePath(),args:chromium.args,env:{...process.env,LD_LIBRARY_PATH:lib+':'+(process.env.LD_LIBRARY_PATH||'')}});
  const errors=[];
  try{
    const page=await browser.newPage({viewport:{width:270,height:480},deviceScaleFactor:1});
    page.on('pageerror',e=>errors.push(String(e)));
    await page.route('**/*',async route=>{
      const p=new URL(route.request().url()).pathname,external=p.startsWith('/vendor/three/');
      const base=external?three:root;const file=path.resolve(base,external?p.slice(14):p.slice(1)||'index.html');
      if(!file.startsWith(base+path.sep))throw Error('Invalid path');
      const mime={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.glb':'model/gltf-binary','.ttf':'font/ttf'};
      await route.fulfill({body:fs.readFileSync(file),contentType:mime[path.extname(file)]||'application/octet-stream'});
    });
    await page.goto('http://monarch-render.invalid/index.html?w=270');await page.waitForFunction(()=>window.ready,null,{timeout:120000});
    const samples=[];let i=0;
    for(const time of [.8,4.82,7.8,9.3,17.4,27.4,.8,4.82,7.8,9.3,17.4,27.4]){
      await page.evaluate(t=>window.renderAt(t),time);
      const pixels=Buffer.from(await page.evaluate(()=>window.exportFrame('png')),'base64');
      fs.writeFileSync(path.join(out,`determinism-${i++}.png`),pixels);
      samples.push({time,sha256:crypto.createHash('sha256').update(pixels).digest('hex')});
    }
    const groups=new Map();for(const s of samples){if(!groups.has(s.time))groups.set(s.time,new Set());groups.get(s.time).add(s.sha256)}
    const passed=errors.length===0&&[...groups.values()].every(set=>set.size===1);
    const geometry=await page.evaluate(()=>window.geometryInfo);
    const result={passed,geometry,viewport:[270,480],method:'Full-frame lossless composite PNG hashes at repeated absolute times; camera, cells, geometry, grip and captions must return to identical pixels.',samples,errors};
    fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'DETERMINISM_REPORT.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify(result,null,2));if(!passed)process.exitCode=1;
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});

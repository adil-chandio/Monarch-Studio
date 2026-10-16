#!/usr/bin/env node
/* Offline native-pixel Three.js capture. All browser URLs are fulfilled from
 * explicitly allowlisted local project/vendor paths: no network server or
 * remote requests. Each complete chunk is independently resumable. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const zlib=require('node:zlib');
const {spawn,spawnSync}=require('node:child_process');
const {once}=require('node:events');
const chromium=require('@sparticuz/chromium');
const {chromium:playwright}=require('playwright-core');
const root=path.resolve(__dirname,'..');
const args=process.argv.slice(2);
const opt=(name,fallback)=>{const i=args.indexOf(name);return i>=0?args[i+1]:fallback};
const out=path.resolve(opt('--out',path.join(root,'build')));
const width=Number(opt('--width',args.includes('--stills')?'540':'1080'));
const height=width*16/9;
const timeline=JSON.parse(fs.readFileSync(path.join(root,'data/timeline.json')));
const fps=timeline.fps,total=Math.round(timeline.duration*fps),chunkSize=90;
const ffmpeg=process.env.FFMPEG || 'ffmpeg';
const capture=opt('--capture','canvas-png');
const threeRoot=path.resolve(path.dirname(require.resolve('three')),'..');
const chrRoot=path.resolve(path.dirname(require.resolve('@sparticuz/chromium')),'..');
const mime={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.glb':'model/gltf-binary','.ttf':'font/ttf','.wav':'audio/wav','.png':'image/png'};
function hashSources(){const h=crypto.createHash('sha256');for(const name of ['index.html','src/film.js','src/director.mjs','src/focus-pass.js','src/motion.mjs','src/render.cjs','data/timeline.json','data/motion.json','data/design.json','data/shot_plan.json','assets/fonts/Montserrat-Cinema.typeface.json','assets/models/cutaway.glb'])h.update(fs.readFileSync(path.join(root,name)));h.update(String(width));h.update(capture);return h.digest('hex')}
function mkdir(p){fs.mkdirSync(p,{recursive:true})}
function libraries(){
  const libdir=path.join(out,'runtime-libs');
  if(!fs.existsSync(path.join(libdir,'lib/libnss3.so'))){
    mkdir(libdir);const tar=path.join(libdir,'al2023.tar');
    fs.writeFileSync(tar,zlib.brotliDecompressSync(fs.readFileSync(path.join(chrRoot,'bin/al2023.tar.br'))));
    const p=spawnSync('tar',['xf',tar,'-C',libdir]);if(p.status)throw Error(p.stderr.toString());fs.unlinkSync(tar);
  }
  return path.join(libdir,'lib');
}
async function main(){
  mkdir(out);const signature=hashSources();
  const browser=await playwright.launch({headless:true,executablePath:await chromium.executablePath(),args:chromium.args,env:{...process.env,LD_LIBRARY_PATH:libraries()+':'+(process.env.LD_LIBRARY_PATH||'')}});
  const errors=[];
  try{
    const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
    page.on('pageerror',e=>{errors.push(String(e));console.error('BROWSER ERROR',e)});
    page.on('console',m=>{if(m.type()==='error')console.error('BROWSER',m.text())});
    await page.route('**/*',async route=>{
      try{
        const url=new URL(route.request().url());
        if(url.hostname!=='monarch-render.invalid')throw Error('Unexpected external URL '+url);
        const p=decodeURIComponent(url.pathname);
        const vendor=p.startsWith('/vendor/three/');
        const base=vendor?threeRoot:root;
        const rel=vendor?p.slice('/vendor/three/'.length):p.slice(1);
        const file=path.resolve(base,rel||'index.html');
        if(!file.startsWith(base+path.sep))throw Error('Path outside render allowlist');
        await route.fulfill({status:200,contentType:mime[path.extname(file)]||'application/octet-stream',body:fs.readFileSync(file)});
      }catch(e){errors.push(String(e));await route.fulfill({status:404,body:String(e)})}
    });
    await page.goto(`http://monarch-render.invalid/index.html?w=${width}`,{timeout:120000});
    await page.waitForFunction(()=>window.ready,{},{timeout:120000});
    const info=await page.evaluate(()=>window.filmInfo);console.log(JSON.stringify({event:'ready',...info,signature}));
    if(errors.length)throw Error(errors.join('\n'));
    if(args.includes('--bench')){
      const profile=[];
      for(const t of [4.80,10.25,17.0]){
        let at=Date.now();await page.evaluate(t=>{window.renderAt(t);window.flush()},t);const renderMs=Date.now()-at;
        at=Date.now();const dom=await page.screenshot({type:'png'});const screenshotMs=Date.now()-at;
        at=Date.now();const b64=await page.evaluate(()=>window.exportFrame('png'));const canvasMs=Date.now()-at;
        fs.writeFileSync(path.join(out,`bench-dom-${t}.png`),dom);fs.writeFileSync(path.join(out,`bench-canvas-${t}.png`),Buffer.from(b64,'base64'));
        profile.push({time:t,renderMs,screenshotMs,canvasMs,domBytes:dom.length,canvasBytes:Buffer.byteLength(b64,'base64')});
        console.log(JSON.stringify(profile.at(-1)));
      }
      fs.writeFileSync(path.join(out,'CAPTURE_PROFILE.json'),JSON.stringify(profile,null,2));
      console.log('RIG',await page.evaluate(()=>window.geometryInfo));
    }
    if(args.includes('--stills')){
      const times=String(opt('--times','0.8,3.2,4.9,6.3,8.4,10.7,13.7,17.4,20.3,23.9,27.2,29.9')).split(',').map(Number);
      for(const t of times){const start=Date.now();await page.evaluate(t=>window.renderAt(t),t);fs.writeFileSync(path.join(out,`still-${t.toFixed(2)}.png`),Buffer.from(await page.evaluate(()=>window.exportFrame('png')),'base64')); console.log(JSON.stringify({event:'still',time:t,ms:Date.now()-start}));}
    }
    if(args.includes('--render')){
      const startFrame=Number(opt('--from','0')),endFrame=Math.min(total,Number(opt('--to',String(total))));
      const frameReport=[];
      for(let start=startFrame;start<endFrame;start+=chunkSize){
        const end=Math.min(start+chunkSize,endFrame),num=String(start).padStart(5,'0'),file=path.join(out,`chunk-${num}.mp4`),receipt=file+'.json';
        if(fs.existsSync(file)&&fs.existsSync(receipt)){
          const old=JSON.parse(fs.readFileSync(receipt));
          if(old.signature===signature&&old.start===start&&old.end===end&&old.bytes===fs.statSync(file).size){console.log(JSON.stringify({event:'resume-skip',start,end}));continue;}
        }
        const tmp=file.replace('.mp4','.partial.mp4');
        const enc=spawn(ffmpeg,['-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate',String(fps),'-vcodec','png','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','17','-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p','-pix_fmt','yuv420p','-color_range','tv','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',tmp],{stdio:['pipe','ignore','pipe']});
        let stderr='';enc.stderr.on('data',d=>stderr+=d);
        const encoderExit=once(enc,'close');
        const begin=Date.now();let sceneEvaluations=0,shutterFrames=0,focusFrames=0;const shotFrames={},sceneGroups={};
        try{
          for(let f=start;f<end;f++){
            const time=f/fps;const state=await page.evaluate(t=>window.renderAt(t),time);sceneEvaluations+=state.shutterSamples||1;if(state.shutterSamples>1)shutterFrames++;if(state.focusEnabled)focusFrames++;shotFrames[state.shot]=(shotFrames[state.shot]||0)+1;sceneGroups[state.sceneGroup]=(sceneGroups[state.sceneGroup]||0)+1;
            const image=capture==='canvas-png'?Buffer.from(await page.evaluate(()=>window.exportFrame('png')),'base64'):await page.screenshot({type:'png',timeout:120000});
            if(!enc.stdin.write(image))await once(enc.stdin,'drain');
            if(f%30===0){console.log(JSON.stringify({event:'frame',frame:f,total,time,shot:state.shot,elapsed:((Date.now()-begin)/1000).toFixed(2)}));frameReport.push({frame:f,...state});}
            if(errors.length)throw Error(errors.join('\n'));
          }
          enc.stdin.end();const [code]=await encoderExit;if(code)throw Error('Encoder failed '+stderr);
        }catch(e){enc.kill('SIGTERM');throw e;}
        fs.renameSync(tmp,file);
        const report={signature,capture,start,end,fps,width,height,sceneEvaluations,shutterFrames,focusFrames,shotFrames,sceneGroups,bytes:fs.statSync(file).size,seconds:(Date.now()-begin)/1000};
        fs.writeFileSync(receipt,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({event:'chunk-complete',...report}));
      }
      fs.writeFileSync(path.join(out,'frame-report.json'),JSON.stringify({signature,info,frames:frameReport},null,2)+'\n');
      if(startFrame===0&&endFrame===total){
        const files=[];for(let f=0;f<total;f+=chunkSize)files.push(`file 'chunk-${String(f).padStart(5,'0')}.mp4'`);
        const concat=path.join(out,'concat.txt');fs.writeFileSync(concat,files.join('\n')+'\n');
        const p=spawnSync(ffmpeg,['-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy','-movflags','+faststart',path.join(out,'picture.mp4')],{encoding:'utf8'});
        if(p.status)throw Error(p.stderr);console.log(JSON.stringify({event:'picture-complete',file:path.join(out,'picture.mp4'),frames:total,duration:timeline.duration}));
      }
    }
  }finally{await browser.close()}
}
main().catch(e=>{console.error(e);process.exitCode=1});

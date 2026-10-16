const {test}=require('node:test');const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const tl=JSON.parse(fs.readFileSync(path.join(root,'data/timeline.json')));

test('native portrait contract has an integral frame count',()=>{
  assert.equal(tl.width,1080);assert.equal(tl.height,1920);assert.equal(tl.fps,30);
  assert.equal(tl.duration*tl.fps,915);
});
test('nine shot intervals cover the entire film without gaps or overlap',()=>{
  assert.equal(tl.shots.length,9);assert.equal(tl.shots[0].start,0);
  tl.shots.forEach((s,i)=>{assert(s.end>s.start);if(i)assert.equal(s.start,tl.shots[i-1].end)});
  assert.equal(tl.shots.at(-1).end,tl.duration);
});
test('captions are in bounds, ordered and preserve the safety message',()=>{
  tl.captions.forEach((c,i)=>{assert(c.start>=0);assert(c.end>c.start);assert(c.end<=tl.duration);assert(c.text.includes(c.accent));if(i)assert(c.start>=tl.captions[i-1].end)});
  const all=tl.captions.map(c=>c.text).join(' ');
  for(const clause of ['har baar nahi','intezaar mat karo','doctor se madad lo','Skin ko mat khodo'])assert(all.includes(clause));
});
test('every Urdu WAV exists and its measured duration matches its placement',()=>{
  tl.narration.forEach((c,i)=>{
    const wav=fs.readFileSync(path.join(root,'assets/vo',c.file));
    assert.equal(wav.toString('ascii',0,4),'RIFF');assert.equal(wav.toString('ascii',8,12),'WAVE');
    let p=12,byteRate,dataSize;
    while(p+8<=wav.length){const id=wav.toString('ascii',p,p+4),n=wav.readUInt32LE(p+4);if(id==='fmt ')byteRate=wav.readUInt32LE(p+8+8);if(id==='data')dataSize=n;p+=8+n+(n%2)}
    assert(Math.abs(dataSize/byteRate-c.duration)<.001);
    assert(c.start+c.duration<=tl.duration);if(i)assert(c.start>=tl.narration[i-1].start+tl.narration[i-1].duration);
  });
});
test('recovered GLB is genuine animated geometry with embedded buffers',()=>{
  const glb=fs.readFileSync(path.join(root,'assets/models/cutaway.glb'));
  assert.equal(glb.toString('ascii',0,4),'glTF');assert.equal(glb.readUInt32LE(4),2);assert.equal(glb.readUInt32LE(8),glb.length);
  const g=JSON.parse(glb.toString('utf8',20,20+glb.readUInt32LE(12)));
  assert(g.meshes.length>10);assert(g.animations[0].channels.length>=150);assert(g.buffers.every(b=>!b.uri));
});
test('stateless transform regression and native render size are explicit',()=>{
  const js=fs.readFileSync(path.join(root,'src/film.js'),'utf8');
  assert(js.includes('named.splinter.scale.set(.57,.74,1)'));
  assert(!/named\.splinter\.scale\.[xyz]\s*\*=/.test(js));
  assert(js.includes('renderer.setSize(W,H)'));assert(js.includes('composer.setSize(W,H)'));
  assert(js.includes('morphAttributes.normal='));
});
test('reference media is provenance only, not a scene plate or audio asset',()=>{
  const provenance=JSON.parse(fs.readFileSync(path.join(root,'data/SOURCES.json')));
  assert.equal(provenance.reference.used_in_output,false);
  const walk=d=>fs.readdirSync(d,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(d,e.name)):[path.join(d,e.name)]);
  const files=walk(path.join(root,'assets'));
  assert(!files.some(f=>/\.(mp4|jpg|jpeg|png|webm)$/i.test(f)));
});

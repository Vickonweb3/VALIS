import {chromium} from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
const jobs=JSON.parse(fs.readFileSync(process.argv[2]));
const b=await chromium.launch({executablePath:'/usr/bin/google-chrome',args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--allow-file-access-from-files','--no-sandbox']});
const p=await b.newPage({viewport:{width:900,height:1100}});
p.on('console',m=>console.log('console:',m.text()));p.on('pageerror',e=>console.log('pageerror',e.message));
await p.goto('http://localhost:8765/viewer.html');
const info=await p.evaluate(()=>window.__init());console.log('clips',info.clips.length);
fs.mkdirSync('/tmp/work/png',{recursive:true});
for(const j of jobs){const d=await p.evaluate(j=>window.__render(j.clip,j.t,j.opt),j);fs.writeFileSync('/tmp/work/png/'+j.name+'.png',Buffer.from(d.split(',')[1],'base64'));console.log('ok',j.name)}
await b.close();

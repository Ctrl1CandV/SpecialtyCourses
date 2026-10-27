/** C3 teaching decks. Native editable content, institutional background.
 * Usage: node 课程/课件/C3/维护/render_c3.mjs C3-A-01 [--publish]
 * Dependencies: bundled @oai/artifact-tool; tools/node_modules/js-yaml.
 * All previews/candidates/validator receipts stay under _tmp/c3_revision.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');
const RUNTIME=process.env.RUNTIME_NODE_MODULES || path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
process.env.RUNTIME_NODE_MODULES=RUNTIME;
const req=createRequire(path.join(RUNTIME,'__runtime__.cjs'));
const {Presentation,PresentationFile}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href);
const yaml=createRequire(path.join(ROOT,'tools/package.json'))('js-yaml');
const SKILL=process.env.PRESENTATIONS_SKILL || path.join(process.env.USERPROFILE,'.codex/plugins/cache/openai-primary-runtime/presentations/26.1020.11618/skills/presentations');
const {finalizePresentation,makeNativeBulletParagraphs}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const PY=process.env.C3_PYTHON || path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe');
const W=1280,H=720,X=76,CW=1128,TOP=204,BOTTOM=625;
const FONT='Microsoft YaHei',MONO='Consolas';
const C={ink:'#1F2329',blue:'#1F4E9C',red:'#C0392B',gray:'#75808B',pale:'#EDF3F8',line:'#CCD6DF'};
const bg=await fs.readFile(path.join(ROOT,'课程/素材/底图.jpg'));
const clean=x=>String(x??'').replace(/`([^`]+)`/g,'$1').replace(/\*\*([^*]+)\*\*/g,'$1');
const weight=s=>[...clean(s)].reduce((n,c)=>n+(/[\u2E80-\uFFFF]/u.test(c)?1:/[il.,:;'| !]/.test(c)?.3:.57),0);
const lines=(s,width,size)=>Math.max(1,...clean(s).split('\n').map(t=>Math.ceil(weight(t)*size/width)));
function txt(slide,text,left,top,width,height,size=27,extra={}){
  const sh=slide.shapes.add({geometry:'textbox',name:extra.name||'Teaching text',position:{left,top,width,height},fill:'none',line:{fill:'none',width:0}});
  sh.text=clean(text);
  sh.text.style={typeface:FONT,fontSize:size,color:C.ink,insets:0,autoFit:'none',wrap:'square',lineSpacing:1.15,...extra};
  return sh;
}
function rect(slide,left,top,width,height,fill,line='none'){
 return slide.shapes.add({geometry:'rect',position:{left,top,width,height},fill,line:{fill:line,width:line==='none'?0:1}});
}
function bullet(slide,text,y,height,size){
 const sh=txt(slide,'',X,y,CW,height,size);
 sh.text=makeNativeBulletParagraphs([clean(text)],{marginLeftPoints:18,hangingPoints:9,spaceAfterPoints:0});
}
function diagram(slide,b,y,height){
 const padX=76,padY=28,areaW=CW-padX*2,areaH=height-padY-(b.caption?56:32);
 const getpos=n=>({x:X+padX+n.x/100*areaW,y:y+padY+n.y/100*areaH});
 const nodes=new Map();
 for(const n of b.nodes){
  const p=getpos(n),label=clean(n.text),ellipse=n.shape==='ellipse';
  const nw=ellipse?Math.max(52,weight(label)*24+26):Math.min(240,Math.max(94,weight(label)*22+26));
  const nh=ellipse?52:50;
  const sh=slide.shapes.add({geometry:ellipse?'ellipse':'rect',name:'Diagram node '+n.id,
   position:{left:p.x-nw/2,top:p.y-nh/2,width:nw,height:nh},
   fill:n.highlight?C.blue:'#FFFFFF',line:{fill:n.highlight?C.blue:C.ink,width:1.7}});
  sh.text=label;sh.text.style={typeface:FONT,fontSize:ellipse?20:22,bold:!!n.highlight,color:n.highlight?'#FFFFFF':C.ink,
   alignment:'center',verticalAlignment:'middle',insets:2,autoFit:'none',wrap:'none'};
  nodes.set(n.id,{sh,n,p,box:{x:p.x-nw/2,y:p.y-nh/2,w:nw,h:nh}});
 }
 for(const e of b.edges||[]){
  const a=nodes.get(e.from),z=nodes.get(e.to);if(!a||!z)throw Error('Unknown diagram edge endpoint');
  const link=slide.shapes.connect(a.sh,z.sh,{kind:e.kind||'straight',...(e.fromSide?{fromSide:e.fromSide}:{}),...(e.toSide?{toSide:e.toSide}:{}),
   line:{fill:e.highlight?C.red:C.gray,width:2},...(e.directed===false?{}:{tail:{type:'triangle',width:'med',length:'med'}})});
  link.bringToFront();
  if(e.label){
   const vertical=Math.abs(a.p.x-z.p.x)<Math.abs(a.p.y-z.p.y);
   const labelWidth=weight(e.label)*20+14;
   const label=txt(slide,e.label,(a.p.x+z.p.x)/2+(vertical?12:-labelWidth/2),(a.p.y+z.p.y)/2-(vertical?14:32),labelWidth,30,20,{alignment:vertical?'left':'center',color:C.blue});
   label.fill='#FFFFFF';
  }
 }
 const labelBoxes=[];
 for(const l of b.labels||[]){
  const p=getpos(l),w=Math.min(CW,Math.max(110,weight(l.text)*21+16));
  const box={x:Math.max(X,Math.min(X+CW-w,p.x-w/2)),y:p.y-14,w,h:29};
  const obstacles=[...[...nodes.values()].map(v=>v.box),...labelBoxes];
  const collide=(a,z)=>a.x<z.x+z.w+5&&a.x+a.w>z.x-5&&a.y<z.y+z.h+5&&a.y+a.h>z.y-5;
  for(let pass=0;pass<5;pass++){
   const z=obstacles.find(z=>collide(box,z));if(!z)break;
   box.y=box.y+box.h/2<z.y+z.h/2?z.y-box.h-7:z.y+z.h+7;
  }
  txt(slide,l.text,box.x,box.y,w,29,21,{color:C.blue,alignment:'center'});labelBoxes.push(box);
 }
 if(b.caption)txt(slide,b.caption,X,y+height-29,CW,29,21,{color:C.gray,alignment:'center'});
}
function table(slide,b,y,height){
 const values=[b.head,...b.rows].map(r=>r.map(clean)),nc=values[0].length;
 const weights=Array.from({length:nc},(_,j)=>Math.max(5,...values.map(r=>Math.min(28,weight(r[j])))));
 const widths=weights.map(w=>CW*w/weights.reduce((a,b)=>a+b,0));
 const rowUnits=values.map(row=>Math.max(...row.map((v,j)=>lines(v,widths[j]-24,24))));
 const desired=rowUnits.map(v=>v*29+22),sum=desired.reduce((a,b)=>a+b,0);
 const rows=desired.map(v=>v*Math.min(1,height/sum));
 const t=slide.tables.add({rows:values.length,columns:nc,left:X,top:y,width:CW,height:rows.reduce((a,b)=>a+b,0),columnWidths:widths,values});
 t.borders.assign({fill:C.line,width:1,style:'solid'});
 for(let r=0;r<values.length;r++){
  t.rows[r].height=rows[r];
  for(let c=0;c<nc;c++){
   const cell=t.getCell(r,c);cell.fill=r===0?C.pale:'#FFFFFF';
   cell.text.style={typeface:FONT,fontSize:24,bold:r===0,color:r===0?C.blue:C.ink,verticalAlignment:'middle',autoFit:'none',insets:10,lineSpacing:1.08};
  }
 }
}
function measure(b,size=27){
 if(b.type==='bullets')return b.items.reduce((sum,t)=>sum+lines(t,CW-22,size)*size*1.25+20,0);
 if(b.type==='code')return Math.max(180,clean(b.text).trimEnd().split('\n').length*37+34);
 if(b.type==='table')return 360;
 if(b.type==='diagram'||b.type==='image')return 350;
 return lines(b.text,CW,size)*size*1.25+20;
}
function addBlocks(slide,blocks,lessonDir,tableOwners,page){
 return (async()=>{
 const flexible=blocks.filter(b=>['diagram','image','table'].includes(b.type));
 const notes=blocks.filter(b=>b.type==='note');
 const budget=BOTTOM-TOP-14*Math.max(0,blocks.length-1);
 let size=blocks.some(b=>b.type==='diagram')?24:27;
 let nonflex=blocks.filter(b=>!flexible.includes(b)).reduce((s,b)=>s+measure(b,b.type==='note'?21:size),0);
 if(nonflex>budget&&flexible.length===0){size=25;nonflex=blocks.reduce((s,b)=>s+measure(b,b.type==='note'?21:size),0);}
 if(nonflex>budget+15&&flexible.length===0)throw Error(`Overfull content on page ${page}: ${nonflex}`);
 let y=TOP;
 for(const b of blocks){
  const flex=['diagram','image','table'].includes(b.type);
  const h=flex?(budget-nonflex)/flexible.length:measure(b,b.type==='note'?21:size);
  if(h<120&&flex)throw Error(`No room for diagram/table on page ${page}`);
  if(b.type==='bullets'){
   for(const item of b.items){const ih=lines(item,CW-22,size)*size*1.25+20;bullet(slide,item,y,ih,size);y+=ih;}
  }else if(b.type==='code'){
   const n=clean(b.text).split('\n').length;
   const maxw=Math.max(...clean(b.text).split('\n').map(weight));
   const font=Math.min(26,Math.floor((CW-52)/maxw));
   if(font<20)throw Error(`Code line too long on page ${page}: ${font}px`);
   rect(slide,X,y,CW,h,C.pale);rect(slide,X,y,4,h,C.blue);
   txt(slide,clean(b.text).trimEnd(),X+24,y+14,CW-48,h-22,font,{typeface:MONO,lineSpacing:1.15,wrap:'none'});y+=h;
  }else if(b.type==='table'){table(slide,b,y,h);tableOwners.push(page);y+=h;}
  else if(b.type==='diagram'){diagram(slide,b,y,h);y+=h;}
  else if(b.type==='image'){
   const f=path.resolve(ROOT,b.src),bytes=await fs.readFile(f);
   slide.images.add({blob:bytes,contentType:f.endsWith('.jpg')?'image/jpeg':'image/png',alt:b.alt||'Algorithm teaching diagram',fit:'contain',position:{left:X,top:y,width:CW,height:h}});y+=h;
  }else{txt(slide,b.text,X,y,CW,h,b.type==='note'?21:size,{color:b.type==='note'?C.gray:C.ink});y+=h;}
  y+=14;
 }
 })();
}
async function build(id){
 if(!/^C3-[AB]-\d{2}$/.test(id))throw Error('Use one C3 lesson id');
 const dir=path.join(ROOT,'课程/课件/C3',id),source=path.join(dir,'deck.yaml');
 const deck=yaml.load(await fs.readFile(source,'utf8'));
 const manuscript=await fs.readFile(path.join(dir,`${id}-讲稿.md`),'utf8');
 const matches=[...manuscript.matchAll(/^## P(\d+) .*\r?\n([\s\S]*?)(?=^## |$(?![\s\S]))/gm)];
 const notes=new Map(matches.map(m=>[Number(m[1]),m[2].trim()]));
 if(notes.size!==deck.slides.length)throw Error(`Lecture/slide mismatch ${notes.size}/${deck.slides.length}`);
 const run=path.join(ROOT,'_tmp/c3_revision',id,Date.now().toString());
 await fs.mkdir(path.join(run,'png'),{recursive:true});
 await fs.mkdir(path.join(run,'final'),{recursive:true});
 const p=Presentation.create({slideSize:{width:W,height:H}}),tableOwners=[];
 for(let i=0;i<deck.slides.length;i++){
  const data=deck.slides[i],s=p.slides.add();
  s.images.add({blob:bg,contentType:'image/jpeg',alt:'伴梦研途原课件底图',fit:'cover',position:{left:0,top:0,width:W,height:H}});
  if(data.type==='cover'){
   txt(s,data.kicker,X,165,CW,36,23,{color:C.blue});
   txt(s,data.title,X,230,CW,80,48,{bold:true});
   txt(s,data.subtitle,X,337,CW,75,36,{color:C.blue});
   txt(s,data.meta,X,490,CW,45,24,{color:C.gray});
  }else{
   txt(s,data.kicker||deck.meta.stage,X,103,CW,27,20,{color:C.blue});
   txt(s,data.title,X,142,CW,55,35,{bold:true,name:'Slide title'});
   await addBlocks(s,data.blocks||[],dir,tableOwners,i+1);
  }
  txt(s,String(i+1),W-95,646,45,25,17,{alignment:'right',color:C.gray});
  s.speakerNotes.text=notes.get(i+1)||'';
 }
 const candidate=path.join(run,`${id}.candidate.pptx`),final=path.join(run,'final',`${id}.pptx`);
 await (await PresentationFile.exportPptx(p)).save(candidate);
 for(let i=0;i<deck.slides.length;i++){
  const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1.25});
  await fs.writeFile(path.join(run,'png',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
 }
 const receipt=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:final,pythonExecutable:PY,
  integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],
  explicitTotalSlideCount:deck.slides.length,requiredNativeTableOwnerSlides:tableOwners,
  fontPolicy:{basis:'design',families:[FONT,MONO],scriptFonts:{ea:FONT}},verifyArtifactToolImport:true,
  receiptPath:path.join(run,'validation.json')});
 const manifest={id,pages:deck.slides.length,duration:deck.meta.duration,diagrams:deck.slides.filter(s=>s.blocks?.some(b=>b.type==='diagram')).length,
  tables:tableOwners,source:source,final,previews:path.join(run,'png'),validated:true};
 await fs.writeFile(path.join(ROOT,'_tmp/c3_revision',`${id}.latest.json`),JSON.stringify(manifest,null,2));
 if(process.argv.includes('--publish')){
  await fs.copyFile(final,path.join(dir,`${id}.pptx`));
  const indexFile=path.join(ROOT,'课程/课件/C3/维护/成品核对.json');
  const index=JSON.parse(await fs.readFile(indexFile,'utf8').catch(()=>'{"lessons":[]}'));
  const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
  const entry={id,pages:deck.slides.length,duration:deck.meta.duration,diagram_pages:manifest.diagrams,
   source_sha256:hash(await fs.readFile(source)),lecture_sha256:hash(await fs.readFile(path.join(dir,`${id}-讲稿.md`))),
   pptx_sha256:hash(await fs.readFile(final)),background_sha256:hash(bg),
   package_integrity:receipt.packageIntegrity.status,layout_findings:receipt.presentationLayout.finding_count,
   note:'本次生成已通过结构与版面自动校验；修改后须重新逐页视觉审查。'};
  index.lessons=[...index.lessons.filter(r=>r.id!==id),entry].sort((a,b)=>a.id.localeCompare(b.id));
  await fs.writeFile(indexFile,JSON.stringify(index,null,2)+'\n');
 }
 console.log(JSON.stringify(manifest));
}
try{for(const id of process.argv.slice(2).filter(a=>!a.startsWith('--')))await build(id);}
catch(error){console.error(error.message);if(error.details)console.error(JSON.stringify(error.details));process.exitCode=1;}

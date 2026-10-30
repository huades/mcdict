import assert from 'node:assert/strict';
import fs from 'node:fs';import vm from 'node:vm';
import {residualLabel,residualKey,themeIsDark} from '../web/ui-utils.js';

// Small synthetic fixture: UI checks run on a clean checkout without book data.
const forms=[...['一','丨','丿','丶','乛'].map((label,i)=>({id:'test:'+i,number:i+1,strokes:1,label,hint:label+'部',index_pdf:35})),{id:'r7:33:2:1399',number:30,strokes:3,label:'艹',hint:'草字头',index_pdf:43}];
const page=fs.readFileSync(new URL('../web/index.html',import.meta.url),'utf8');
assert.match(page,/<a[^>]+href="https:\/\/github.com\/huades\/mcdict"[^>]+rel="noopener noreferrer"[^>]+aria-label="GitHub repository"/);
assert.equal(residualLabel(null,null),'原表未单列部外笔画');
assert.equal(residualLabel(5,7),'5至7画');assert.equal(residualLabel(10,99),'10画以上');
assert.equal(residualKey(null,null),'none');
assert.equal(themeIsDark('auto',true,false),true);
assert.equal(themeIsDark('auto',false,true),false);
assert.equal(themeIsDark('light',true,true),false);
assert.equal(themeIsDark('dark',false,false),true);
assert.equal(themeIsDark('auto',null,true),true);

// Execute the production UI and its real event handlers against a small native
// bridge/DOM harness: catches missing systemtheme handlers and init/event races.
const source=fs.readFileSync(new URL('../web/app.js',import.meta.url),'utf8').replace(/^import .*;\r?\n/m,'');
async function runApp(initialDark,initialTheme='auto'){
 const elements=new Map(),events=new Map(),classes=new Set(),requests=[];
 const element=id=>{if(!elements.has(id))elements.set(id,{value:'',hidden:false,innerHTML:'',textContent:'',style:{setProperty(){}},classList:{toggle(){},remove(){},add(){}},setAttribute(){},addEventListener(){},scrollIntoView(){},insertAdjacentHTML(where,html){this.innerHTML+=html;}});return elements.get(id);};
 const media={matches:!initialDark,addEventListener(type,fn){this.listener=fn;}};
 const context={console,residualLabel,residualKey,themeIsDark,forms,setTimeout,clearTimeout,matchMedia:()=>media,
  document:{querySelector:element,querySelectorAll:()=>[],documentElement:{style:{setProperty(){}}},body:{classList:{toggle(name,on){on?classes.add(name):classes.delete(name);}}}},
  window:{addEventListener(name,fn){events.set(name,fn);},scrollTo(){}},innerWidth:390};
 context.window.DictionaryNative={request(id,action,payload){requests.push({action,payload:JSON.parse(payload)});const data=action==='init'?{user:{favorites:{},history:[],settings:{theme:initialTheme}},systemDark:initialDark}:action==='glyphs'?{items:[],groups:[{residual_min:null,residual_max:null,count:3},{residual_min:5,residual_max:7,count:2}],total:5,more:false}:{};queueMicrotask(()=>context.window.nativeReply(id,data,null));}};
 vm.runInNewContext(source,context);await new Promise(r=>setImmediate(r));
 const dark=()=>classes.has('dark');
 element('.repo-link').onclick({preventDefault(){}});assert.ok(requests.some(r=>r.action==='repository'));
 const nativeRequest=context.window.DictionaryNative.request;
 context.window.DictionaryNative.request=(id,action,payload)=>{
  if(action==='sameCharacter'){requests.push({action,payload:JSON.parse(payload)});queueMicrotask(()=>context.window.nativeReply(id,{items:[{id:'xdhy7:grass',head:'草',head_html:'草',pinyin:'cǎo'}]},null));}
  else if(action==='detail'){requests.push({action,payload:JSON.parse(payload)});queueMicrotask(()=>context.window.nativeReply(id,{id:'xdhy7:grass',head:'草',head_html:'草',pinyin:'cǎo',body_text:'高等植物',body_html:'高等植物',unknown_glyph:0},null));}
  else nativeRequest(id,action,payload);
 };
 assert.equal(element('#dictionary-edition').value,'7','Seventh edition is the default');
 vm.runInContext(`api('search',{query:'动车'});`,context);
 assert.ok(requests.some(r=>r.action==='search'&&r.payload.edition===7));
 vm.runInContext(`user.settings.dictionaryEdition=5;api('search',{query:'安静'});`,context);
 assert.ok(requests.some(r=>r.action==='search'&&r.payload.edition===5));
 const kept=vm.runInContext(`JSON.stringify(Object.keys(safeUser({favorites:{'xdhy5:old':{},'xdhy7:new':{},'other:bad':{}}}).favorites).sort())`,context);
 assert.equal(kept,'["xdhy5:old","xdhy7:new"]','Both editions keep their own favorite IDs');
 assert.equal(dark(),initialTheme==='dark'||initialTheme==='auto'&&initialDark,'Initial native setting overrides contradictory media query');
 const system=value=>events.get('systemtheme')({detail:{dark:value}});
 system(!initialDark);assert.equal(dark(),initialTheme==='dark'||initialTheme==='auto'&&!initialDark);
 element('#theme').value='light';element('#theme').onchange();system(true);assert.equal(dark(),false,'Manual light survives system change');
 element('#theme').value='dark';element('#theme').onchange();system(false);assert.equal(dark(),true,'Manual dark survives system change');
 element('#theme').value='auto';element('#theme').onchange();assert.equal(dark(),false);system(true);assert.equal(dark(),true,'Auto changes live');
 media.matches=false;media.listener();assert.equal(dark(),true,'WebView light preference cannot override native dark');
 assert.ok(requests.some(r=>r.action==='appearance'&&r.payload.theme==='auto'&&r.payload.dark));
 // Exercise the actual grouped picker and ensure changing groups clears stale selection.
 vm.runInContext(`radicals=forms;radicalGroup=3;setRadical('r7:33:2:1399')`,vm.createContext(context));
 assert.match(element('#radical-selection').textContent,/艹 · 草字头 · 部首3画/);
 assert.ok(!element('#radical-grid').innerHTML.includes('<img'),'Radical picker must use text, never source screenshot crops');
 assert.match(element('#radical-grid').innerHTML,/r7:33:2:1399/);
 await new Promise(r=>setImmediate(r));
 assert.match(element('#stroke-input').innerHTML,/原表未单列部外笔画/);
 assert.match(element('#stroke-input').innerHTML,/5至7画/);
 element('#stroke-input').value='6:6';await element('#glyph-search').onclick();
 assert.ok(requests.some(r=>r.action==='glyphs'&&r.payload.radical==='r7:33:2:1399'&&r.payload.group==='6:6'),'Grass uses the exact PDF form, never a Kangxi number');
 assert.ok(requests.some(r=>r.action==='glyphs'&&r.payload.mode==='text'),'Radical page queries the new linked text candidates by default');
 vm.runInContext(`glyphItems.set('grass',{id:'grass',character:'草',body_page:129,body_pdf:223});openRadicalGlyph('grass')`,context);
 await new Promise(r=>setImmediate(r));await new Promise(r=>setImmediate(r));
 assert.ok(requests.some(r=>r.action==='sameCharacter'&&r.payload.edition===7));
 assert.ok(requests.some(r=>r.action==='detail'&&r.payload.id==='xdhy7:grass'));
 assert.match(element('#detail').innerHTML,/第7版 · 社区校订/);
 assert.match(element('#detail').innerHTML,/返回部首查字/);
 vm.runInContext(`radicalGroup=1;setRadical('')`,context);
 assert.equal((element('#radical-grid').innerHTML.match(/data-radical=/g)||[]).length,5);
 assert.equal(element('#stroke-input').disabled,true);
 await new Promise(r=>setImmediate(r));
}
await runApp(true);await runApp(false);await runApp(false,'dark');await runApp(true,'light');
console.log('PASS: source-backed radical picker, range/unlisted groups, native initial/live/manual themes');

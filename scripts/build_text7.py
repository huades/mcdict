"""Community text7 is primary; fifth edition is never used to fill its definitions."""
from pathlib import Path
import ast,collections,hashlib,html,json,re,sqlite3,sys,unicodedata
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.deps'))
from bs4 import BeautifulSoup
# Reuse existing, tested pinyin segmentation without executing the fifth-edition builder.
tree=ast.parse((ROOT/'scripts/build_data.py').read_text(encoding='utf-8'))
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('pykey','tokens','norm','initials') or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='syllables' for t in n.targets)]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'dictionary-key-functions','exec'))
raw=(ROOT/'source-text7/dict.mdx.txt').read_bytes();source=json.loads((ROOT/'source-text7/source.json').read_text(encoding='utf-8'))
assert hashlib.sha256(raw).hexdigest()==source['sha256']
records=[x.strip('\r\n').split('\n',1) for x in raw.decode('utf-8',errors='strict').split('</>') if x.strip()]
OUT=ROOT/'generated';path=OUT/'dictionary7.db'
if path.exists():path.unlink()
db=sqlite3.connect(path);db.executescript('''
CREATE TABLE entries(id TEXT PRIMARY KEY,head TEXT,head_html TEXT,pinyin TEXT,pinyin_key TEXT,initials TEXT,body_html TEXT,body_text TEXT,ordinal INTEGER,unknown_glyph INTEGER);
CREATE INDEX head_idx ON entries(head);CREATE INDEX py_idx ON entries(pinyin_key);
CREATE VIRTUAL TABLE fulltext USING fts4(text,tokenize=simple);
CREATE TABLE aliases(alias TEXT,target TEXT);CREATE INDEX alias_idx ON aliases(alias);
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
''')
counts=collections.Counter();anomalies=[];aliases=[];seen=collections.Counter();samples={}
corrections=json.loads((ROOT/'source-text7/corrections.json').read_text(encoding='utf-8'))['entries'];applied=[]
def normalized(s):return unicodedata.normalize('NFC',s).replace('ɡ','g').replace('ɑ','a').replace('・','·').strip()
for ordinal,(key,fragment) in enumerate(records):
 key=key.strip();fragment=fragment.strip()
 if fragment.startswith('@@@LINK='):
  aliases.append((key,fragment[len('@@@LINK='):].strip()));continue
 soup=BeautifulSoup(fragment,'html.parser');main=soup.find('main')
 if main is None:counts['non_dictionary_records']+=1;continue
 title=main.select_one('.title');py=main.select_one('.py')
 if not title:counts['missing_title']+=1;anomalies.append({'key':key,'reason':'missing title'});continue
 title_html=''.join(str(c) for c in title.contents);head=key
 pronunciation=normalized(py.get_text(' ',strip=True)) if py else ''
 for change in corrections:
  if key==change['head'] and pronunciation==change['pinyin_before']:pronunciation=change['pinyin_after'];applied.append(change)
 if pronunciation.startswith('@@'):anomalies.append({'key':key,'reason':'invalid pinyin'})
 title.decompose()
 if py:py.decompose()
 for tag in list(main.find_all(['script','style','link','iframe','object','embed'])):tag.decompose();counts['unsafe_nodes_removed']+=1
 for tag in list(main.find_all(True)):
  if tag.name not in ('span','div','p','br','sup','sub','table','tbody','tr','td','th','b','i','strong','em'):
   tag.unwrap();continue
  classes=tag.get('class',[]);tag.attrs={'class':' '.join(c for c in classes if re.fullmatch('[a-zA-Z0-9_-]+',c))} if classes else {}
 body=''.join(str(c) for c in main.contents);text=main.get_text(' ',strip=True)
 if not text:counts['empty_definitions']+=1;anomalies.append({'key':key,'reason':'empty definition'})
 bad=re.findall('[\ue000-\uf8ff\ufffd]',head+pronunciation+text)
 if bad:anomalies.append({'key':key,'reason':'unresolved character','codepoints':sorted(set('U+%04X'%ord(c) for c in bad))})
 seen[key]+=1
 identifier='xdhy7:'+hashlib.sha256((key+'\0'+fragment).encode('utf-8')).hexdigest()[:20]+':'+str(seen[key])
 # Search normalization does not rewrite the source's Chinese definitions.
 db.execute('INSERT INTO entries VALUES(?,?,?,?,?,?,?,?,?,?)',(identifier,head,title_html,pronunciation,pykey(pronunciation),initials(pronunciation,head),body,text,ordinal,int(bool(bad))))
 rowid=db.execute('SELECT last_insert_rowid()').fetchone()[0];db.execute('INSERT INTO fulltext(rowid,text) VALUES(?,?)',(rowid,tokens(head+' '+text)))
 counts['entries']+=1
 if key in ('安静','行','得','草','绿','略','给力','动车','什么','矛盾','一站式','接地气'):samples.setdefault(key,[]).append({'id':identifier,'pinyin':pronunciation,'text':text})
 if counts['entries']%20000==0:print('Parsed',counts['entries'],flush=True)
heads={r[0] for r in db.execute('select distinct head from entries')};resolved=[];broken=[]
mapping=dict(aliases)
for alias,target in aliases:
 visited={alias}
 while target not in heads and target in mapping and target not in visited:visited.add(target);target=mapping[target]
 if target in heads:resolved.append((normalized(alias),target))
 else:broken.append({'alias':alias,'target':target})
db.executemany('INSERT INTO aliases VALUES(?,?)',resolved)
counts.update({'source_records':len(records),'aliases':len(resolved),'broken_aliases':len(broken),'anomaly_records':len(anomalies),'distinct_heads':len(heads)})
assert len(applied)==len(corrections)
manifest={'edition':'第7版社区校订文本','official':False,'source':source,'counts':dict(counts),'localCorrections':applied,'quality':'重点核对版，未完成逐条人工校勘；异常条目保留提示，不以第5版补写第7版释义。'}
for k,v in manifest.items():db.execute('INSERT INTO metadata VALUES(?,?)',(k,json.dumps(v,ensure_ascii=False)))
db.commit();db.execute('VACUUM');assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.close()
(OUT/'manifest7.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'reports/text7-audit.json').write_text(json.dumps({'summary':manifest,'anomalies':anomalies,'broken_aliases':broken,'samples':samples},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(counts),ensure_ascii=False));print('sample readings',{k:[r['pinyin'] for r in v] for k,v in samples.items()})

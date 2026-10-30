"""Build an immutable, source-backed seventh-edition index (never Unihan)."""
import collections,hashlib,json,pathlib,sqlite3
from PIL import Image
from pdf7_parse import ROOT,QA
from radical_text7 import annotate

SOURCE=ROOT/'source-index7'
data=json.loads((SOURCE/'transcription.json').read_text(encoding='utf-8'))
catalog=json.loads((SOURCE/'catalog.json').read_text(encoding='utf-8'))
assert not data['issues'],data['issues']
assert not catalog['issues'],catalog['issues']
assert all(e['page_check']!='pending' for e in data['entries'])
forms=catalog['forms'];sections=data['sections'];entries=data['entries']
annotate(forms)
(ROOT/'generated/radicals-text7.json').write_text(json.dumps(forms,ensure_ascii=False),encoding='utf-8')
assert len(forms)==len(sections)==279
assert {f['number'] for f in forms if not f['alias']}==set(range(1,202))
# Multiple aliases sharing a page were visually compared in qa/matches.png.
# Their relative order agrees in the directory and the table, within each key.
keys=lambda f:(f['number'],f['index_page'],f['alias'])
groups=collections.defaultdict(list);sgroups=collections.defaultdict(list)
for f in forms:groups[keys(f)].append(f)
for s in sections:sgroups[(s['radical'],s['index_paper'],s['alias'])].append(s)
assert {k:len(v) for k,v in groups.items()}=={k:len(v) for k,v in sgroups.items()}
for k,fs in groups.items():
 for f,s in zip(fs,sgroups[k]):f['section']=s['id']
out=ROOT/'generated';assets=out/'index7';assets.mkdir(parents=True,exist_ok=True)
images={}
def page(n):
 if n not in images:images[n]=Image.open(QA/f'page-{n:04d}.png').convert('RGB')
 return images[n]

# Keep original shapes including source parentheses and multiple printed forms.
# One image per directory item; glyph records use one compact sprite per page.
for i,f in enumerate(forms):
 width=f['right']-f['left'];crop=page(f['catalog_pdf']).crop((round(f['left']+width*.30),f['top'],round(f['left']+width*.79),f['bottom']))
 f['image']=f'index7/r-{i:03d}.png';crop.save(out/f['image'])
by_page=collections.defaultdict(list)
for e in entries:by_page[e['glyph']['source_page']].append(e)
for n,es in by_page.items():
 boxes=list(dict.fromkeys(tuple(e['glyph']['box']) for e in es));positions={b:i for i,b in enumerate(boxes)}
 sprite=Image.new('RGB',(120*12,52*((len(boxes)+11)//12)),'white')
 for box,i in positions.items():
  crop=page(n).crop(box);sprite.paste(crop,(i%12*120,i//12*52))
 sprite.save(assets/f'g-{n:02d}.png')
 for e in es:
  i=positions[tuple(e['glyph']['box'])];e['image']=f'index7/g-{n:02d}.png';e['sx']=i%12*120;e['sy']=i//12*52

dbpath=out/'index7.db'
if dbpath.exists():dbpath.unlink()
db=sqlite3.connect(dbpath)
db.executescript('''
CREATE TABLE forms(id TEXT PRIMARY KEY,number INTEGER,strokes INTEGER,alias INTEGER,section TEXT UNIQUE,image TEXT,catalog_pdf INTEGER,index_pdf INTEGER,ordinal INTEGER,label TEXT,hint TEXT);
CREATE TABLE glyphs(id TEXT PRIMARY KEY,section TEXT,radical INTEGER,residual_min INTEGER,residual_max INTEGER,body_page INTEGER,body_pdf INTEGER,index_pdf INTEGER,character TEXT,image TEXT,sx INTEGER,sy INTEGER,ordinal INTEGER,page_check TEXT,source_x INTEGER,source_y INTEGER);
CREATE INDEX glyph_section ON glyphs(section,ordinal);
CREATE INDEX glyph_character ON glyphs(character);
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
''')
for i,f in enumerate(forms):db.execute('INSERT INTO forms VALUES(?,?,?,?,?,?,?,?,?,?,?)',(f['id'],f['number'],f['strokes'],int(f['alias']),f['section'],f['image'],f['catalog_pdf'],f['index_page']+20,i,f['label'],f['hint']))
for i,e in enumerate(entries):
 assert e['body_pdf']==e['body_page']+94 and 95<=e['body_pdf']<=1860
 assert (e['residual_min'] is None)==(e['residual_max'] is None)
 db.execute('INSERT INTO glyphs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(e['id'],e['section'],e['radical'],e['residual_min'],e['residual_max'],e['body_page'],e['body_pdf'],e['index_pdf'],e['character'],e['image'],e['sx'],e['sy'],i,e['page_check'],e['left'],e['y']))
manifest={'edition':7,'pdf_sha256':'efd0d6b626a306fd633a1ce1c970a03f10435c28be668014f05671c114b80216','catalog_pdf':[33,34],'table_pdf':[35,89],'body_pdf_offset':94,'main_radicals':201,'forms':279,'references':len(entries),'page_checks':dict(collections.Counter(e['page_check'] for e in entries)),'unlisted_residual_references':sum(e['residual_min'] is None for e in entries),'character_policy':'OCR agreement is a search suggestion, not an edition mapping. Original glyph crop is authoritative; every item has a seventh-edition PDF link.','residual_policy':'Preserve printed exact/range headings; NULL means the table did not print a separate heading.','review':'Directory IDs, stroke boundaries, ambiguous aliases, and page disagreements checked visually. Every extracted page reference cross-checked by OCR agreement or recorded visual correction. No claim that every Unicode glyph or edition equivalence was manually verified.'}
for k,v in manifest.items():db.execute('INSERT INTO metadata VALUES(?,?)',(k,json.dumps(v,ensure_ascii=False)))
db.commit();assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.close()
manifest['database_sha256']=hashlib.sha256(dbpath.read_bytes()).hexdigest()
(out/'index7-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))

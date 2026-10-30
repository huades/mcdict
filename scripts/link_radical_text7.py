"""Link source-backed radical records to real seventh-edition text entries."""
from pathlib import Path
import hashlib,json,sqlite3
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'generated/index7.db';db=sqlite3.connect(path)
db.execute('DROP TABLE IF EXISTS entry_links');db.execute('CREATE TABLE entry_links(glyph_id TEXT,entry_id TEXT,head TEXT,pinyin TEXT,PRIMARY KEY(glyph_id,entry_id))')
with sqlite3.connect(ROOT/'generated/dictionary7.db') as words:
 mapping={}
 for identifier,head,py in words.execute('SELECT id,head,pinyin FROM entries WHERE length(head)=1'):mapping.setdefault(head,[]).append((identifier,head,py))
 for alias,target in words.execute('SELECT alias,target FROM aliases WHERE length(alias)=1'):
  if alias not in mapping and target in mapping:mapping[alias]=mapping[target]
for gid,ch in db.execute('SELECT id,character FROM glyphs WHERE character IS NOT NULL').fetchall():
 for row in mapping.get(ch,[]):db.execute('INSERT OR IGNORE INTO entry_links VALUES(?,?,?,?)',(gid,*row))
db.execute('CREATE INDEX link_entry ON entry_links(entry_id)');db.commit();db.execute('VACUUM')
counts={'linked_references':db.execute('SELECT count(distinct glyph_id) FROM entry_links').fetchone()[0],'linked_characters':db.execute('SELECT count(distinct character) FROM glyphs WHERE id IN(SELECT glyph_id FROM entry_links)').fetchone()[0],'entry_links':db.execute('SELECT count(*) FROM entry_links').fetchone()[0]};db.close()
m=json.loads((ROOT/'generated/index7-manifest.json').read_text(encoding='utf-8'));m.update(database_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),databaseBytes=path.stat().st_size,text7_links=counts)
(ROOT/'generated/index7-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'generated/manifest7.json';m=json.loads(p.read_text(encoding='utf-8'));data=(ROOT/'generated/dictionary7.db').read_bytes();m.update(databaseSha256=hashlib.sha256(data).hexdigest(),databaseBytes=len(data));p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(counts)

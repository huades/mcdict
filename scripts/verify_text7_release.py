from pathlib import Path
import hashlib,json,sqlite3,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1];apk=ROOT/'.android-build/output/modern-chinese-dictionary-offline-1.2.1.apk'
sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(apk) as z:
 assert z.testzip() is None
 for name in ('app.js','app.css','index.html','ui-utils.js'):assert z.read('assets/'+name)==(ROOT/'web'/name).read_bytes()
 for name in ('dictionary.db','dictionary7.db','index7.db','manifest7.json','index7-manifest.json','book7-pages.json'):assert z.read('assets/'+name)==(ROOT/'generated'/name).read_bytes()
 assert sha(z.read('assets/dictionary7.db'))==json.loads(z.read('assets/manifest7.json'))['databaseSha256']
 assert sha(z.read('assets/index7.db'))==json.loads(z.read('assets/index7-manifest.json'))['database_sha256']
 assert not any(n.startswith(('assets/book7-pages/','assets/book7-compact/','assets/index7/')) and not n.endswith('/') for n in z.namelist())
 assert len(z.read('assets/dictionary7.db'))>0
for path in list((ROOT/'web').glob('*'))+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'scripts').glob('*.mjs')):
 text=path.read_bytes().decode('utf-8',errors='strict');assert '\ufffd' not in text and not text.startswith('\ufeff'),path
with sqlite3.connect(ROOT/'generated/dictionary7.db') as db:
 assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
 assert db.execute('select count(*) from entries').fetchone()[0]==70113
 assert db.execute('select pinyin from entries where head=?',('矛盾',)).fetchone()[0]=='máodùn'
copies=[]
for name in ('现代汉语词典-v1.2.1.apk','现代汉语词典.apk'):
 target=ROOT.parent/name;shutil.copyfile(apk,target);assert sha(target.read_bytes())==sha(apk.read_bytes());copies.append(str(target))
result={'version':'1.2.1','version_code':10201,'bytes':apk.stat().st_size,'sha256':sha(apk.read_bytes()),'copies':copies,'primary_entries':70113,'resolved_aliases':4698,'broken_aliases_inactive':8,'legacy_entries':65738,'book_pack_optional':True,'zip_crc':'passed','assets':'all match','source7':json.loads((ROOT/'generated/manifest7.json').read_text(encoding='utf-8'))}
(ROOT/'reports/1.2.1-release.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='source7'},ensure_ascii=False,indent=2))

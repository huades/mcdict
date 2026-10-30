"""Verify packaged source assets, Unicode filenames and copy the reviewed APK."""
from pathlib import Path
import hashlib,json,shutil,sqlite3,zipfile
ROOT=Path(__file__).resolve().parents[1]
apk=ROOT/'.android-build/output/modern-chinese-dictionary-offline-1.1.2.apk'
sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(apk) as z:
 assert z.testzip() is None
 for name in ('app.js','app.css','index.html','ui-utils.js'):
  assert z.read('assets/'+name)==(ROOT/'web'/name).read_bytes(),name
 for name in ('index7.db','index7-manifest.json','dictionary.db'):
  assert z.read('assets/'+name)==(ROOT/'generated'/name).read_bytes(),name
 manifest=json.loads(z.read('assets/index7-manifest.json'))
 book=json.loads(z.read('assets/book7-pages.json'));assert book['count']==len(book['pages'])==1897
 page_assets={i for i in z.namelist() if i.startswith(('assets/book7-pages/','assets/book7-compact/')) and not i.endswith('/')}
 assert page_assets=={'assets/'+p['file'] for p in book['pages']},'Unexpected stale or missing book pages'
 assert book['source_pdf_sha256']==manifest['pdf_sha256']
 from PIL import Image
 import io
 for n,page in enumerate(book['pages'],1):
  raw=z.read('assets/'+page['file']);assert page['page']==n and sha(raw)==page['sha256']
  with Image.open(io.BytesIO(raw)) as image:
   image.load();assert image.size==(page['width'],page['height'])
   if page.get('pixel_sha256'):assert sha(image.convert('RGB').tobytes())==page['pixel_sha256']
 assert 'assets/book7.pdf' not in z.namelist()
 with sqlite3.connect(ROOT/'generated/index7.db') as db:
  names={r[0] for r in db.execute('select image from forms union select image from glyphs')}
 for name in names:assert 'assets/'+name not in z.namelist(),name
for path in list((ROOT/'web').glob('*'))+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'scripts').glob('*.mjs'))+list((ROOT/'source-index7').glob('*.json')):
 text=path.read_bytes().decode('utf-8',errors='strict')
 assert '\ufffd' not in text and not text.startswith('\ufeff'),path
 assert '\ufffd' not in path.name and '?' not in path.name,path
assert sha(next(ROOT.parent.glob('*.pdf')).read_bytes())==manifest['pdf_sha256']
copies=[]
for name in ('现代汉语词典-v1.1.2.apk','现代汉语词典.apk'):
 target=ROOT.parent/name;shutil.copyfile(apk,target)
 assert sha(target.read_bytes())==sha(apk.read_bytes());copies.append(str(target))
result={'version':'1.1.2','version_code':10102,'bytes':apk.stat().st_size,'sha256':sha(apk.read_bytes()),'copies':copies,'unused_index_images_removed':len(names),'book_pages_decoded_and_hashed':1897,'all_packaged_assets_match':True,'zip_crc':'passed','utf8':'strict, no BOM or replacement characters','index':manifest}
(ROOT/'reports/1.1.2-release.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='index'},ensure_ascii=False,indent=2))

from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];m=json.loads((ROOT/'generated/book7-pages.json').read_text(encoding='utf-8'))
target=ROOT.parent/'现代汉语词典-第7版原书离线包.zip'
if not target.exists():
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as z:
  for r in m['pages']:
   file=ROOT/'generated'/r['file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==r['sha256'];z.write(file,r['file'])
with zipfile.ZipFile(target) as z:
 assert len(z.namelist())==1897
 for r in m['pages']:assert hashlib.sha256(z.read(r['file'])).hexdigest()==r['sha256']
print('Offline pack verified',target.stat().st_size,'bytes')

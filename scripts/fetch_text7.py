from pathlib import Path
import urllib.request,hashlib,json
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'source-text7';out.mkdir(exist_ok=True)
for name,sha in [('dict.mdx.txt','90dc7fb83197166ebd94516290252b78b5df31a8')]:
 url='https://raw.githubusercontent.com/pampas9000/ModernChineseDict/main/mdx/'+name
 target=out/name
 if not target.exists():target.write_bytes(urllib.request.urlopen(url,timeout=90).read())
 raw=target.read_bytes();actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert actual==sha,(actual,sha)
 raw.decode('utf-8',errors='strict')
 (out/'source.json').write_text(json.dumps({'url':url,'git_blob':sha,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'label':'Community corrected seventh-edition text; not official publisher data'},ensure_ascii=False,indent=2),encoding='utf-8')
 print('Source verified',len(raw),'bytes');print(raw.decode('utf-8')[:1800])

"""Preserve already-JPEG original scans rather than expanding them into PNG."""
import json,pathlib,hashlib,io
from PIL import Image
from pypdf import PdfReader
ROOT=pathlib.Path(__file__).resolve().parents[1];path=ROOT/'generated/book7-pages.json'
m=json.loads(path.read_text(encoding='utf-8'));pdf=PdfReader(str(next(ROOT.parent.glob('*.pdf'))));count=0
for r,page in zip(m['pages'],pdf.pages):
 objects=list(page['/Resources'].get('/XObject',{}).values())
 if len(objects)!=1 or page.get('/Rotate',0)!=0:continue
 obj=objects[0].get_object();raw=obj._data
 if obj.get('/Filter')!='/DCTDecode' or not raw.startswith(b'\xff\xd8'):continue
 with Image.open(io.BytesIO(raw)) as image:
  if image.size!=(r['width'],r['height']):continue
 target=ROOT/'generated/book7-pages'/f'p{r["page"]:04d}.jpg';target.write_bytes(raw)
 r.update(file=f'book7-pages/{target.name}',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),method='original-JPEG-stream');count+=1
m['bytes']=sum(r['bytes'] for r in m['pages']);m['format']='Original JPEG streams or lossless decoded PNG scans';path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Preserved JPEG scans',count,'total MiB',round(m['bytes']/1024/1024,1))

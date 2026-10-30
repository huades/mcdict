"""Decode original scan pages once, avoiding device-specific PDF rendering.

Original page pixels are saved losslessly as PNG. Source PDF is read-only.
"""
import hashlib,json,pathlib,time
import pypdfium2 as pdfium
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
source=next(ROOT.parent.glob('*.pdf'))
digest=hashlib.sha256(source.read_bytes()).hexdigest()
assert digest=='efd0d6b626a306fd633a1ce1c970a03f10435c28be668014f05671c114b80216'
out=ROOT/'generated/book7-pages';out.mkdir(parents=True,exist_ok=True)
doc=pdfium.PdfDocument(str(source));assert len(doc)==1897
records=[];start=time.monotonic()
for i in range(len(doc)):
 target=out/f'p{i+1:04d}.png';page=doc[i]
 if target.exists():
  with Image.open(target) as existing:width,height=existing.size
  method='cached-lossless'
 else:
  pictures=list(page.get_objects(filter=[pdfium.raw.FPDF_PAGEOBJ_IMAGE]))
  simple=False
  if len(pictures)==1 and page.get_rotation()==0:
   m=pictures[0].get_matrix();simple=m.a>0 and m.d>0 and abs(m.b)<.01 and abs(m.c)<.01
  if simple:
   bitmap=pictures[0].get_bitmap();image=bitmap.to_pil().copy();method='original-scan-pixels'
  else:
   bitmap=page.render(scale=2,fill_color=(255,255,255,255));image=bitmap.to_pil().copy();bitmap.close();method='pdfium-page-composite'
  if image.mode=='L':
   colors=image.getcolors(3)
   if colors and {v for _,v in colors}<={0,255}:image=image.convert('1',dither=Image.Dither.NONE)
  # Converting an already black/white source to 1-bit is pixel-exact.
  image.save(target,optimize=True);width,height=image.size
  with Image.open(target) as saved:assert saved.convert('RGB').tobytes()==image.convert('RGB').tobytes()
 records.append({'page':i+1,'file':f'book7-pages/{target.name}','width':width,'height':height,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'method':method})
 page.close()
 if (i+1)%100==0:print(f'Prepared {i+1}/1897 pages, {time.monotonic()-start:.1f}s',flush=True)
manifest={'version':1,'count':1897,'source_pdf_sha256':digest,'body_pdf_offset':94,'format':'lossless PNG at original scan resolution','bytes':sum(r['bytes'] for r in records),'pages':records}
(ROOT/'generated/book7-pages.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Book ready: {len(records)} pages, {manifest["bytes"]/1024/1024:.1f} MiB, {time.monotonic()-start:.1f}s',flush=True)

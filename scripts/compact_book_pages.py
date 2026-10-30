"""Preserve page composition and scan resolution without artificial gray halos.

Render black/white scans without image interpolation; then select the smaller
lossless PNG/WebP encoding. Original color JPEG pages are retained unchanged.
"""
from pathlib import Path
import concurrent.futures,hashlib,io,json,time
from PIL import Image
import pypdfium2 as pdfium
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'generated/book7-pages.json'
backup=ROOT/'generated/book7-pages-1.1.1.json'
if not backup.exists():backup.write_bytes(path.read_bytes())
old=json.loads(backup.read_text(encoding='utf-8'));doc=pdfium.PdfDocument(str(next(ROOT.parent.glob('*.pdf'))))
assert hashlib.sha256(next(ROOT.parent.glob('*.pdf')).read_bytes()).hexdigest()==old['source_pdf_sha256']
out=ROOT/'generated/book7-compact';out.mkdir(exist_ok=True);start=time.monotonic()
def encode(image,number):
 rgb=image.convert('RGB');original=rgb.tobytes();png=io.BytesIO();webp=io.BytesIO()
 colors=image.getcolors(3)
 if image.mode=='L' and colors and {v for _,v in colors}<={0,255}:image=image.convert('1',dither=Image.Dither.NONE)
 image.save(png,format='PNG',optimize=True)
 rgb.save(webp,format='WEBP',lossless=True,method=3)
 data,ext=min(((png.getvalue(),'png'),(webp.getvalue(),'webp')),key=lambda x:len(x[0]))
 with Image.open(io.BytesIO(data)) as check:assert check.convert('RGB').tobytes()==original
 target=out/f'p{number:04d}.{ext}';target.write_bytes(data)
 return {'page':number,'file':f'book7-compact/{target.name}','width':rgb.width,'height':rgb.height,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'pixel_sha256':hashlib.sha256(original).hexdigest(),'method':'native-resolution-page-composite-no-image-interpolation-lossless'}
records=[];futures=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for i,r in enumerate(old['pages']):
  if r['file'].endswith('.jpg'):
   records.append(r);continue
  page=doc[i];pictures=list(page.get_objects(filter=[pdfium.raw.FPDF_PAGEOBJ_IMAGE]))
  # Use the full scan's native width, retain every overlay through PDF rendering.
  largest=max(pictures,key=lambda o:abs(o.get_matrix().a*o.get_matrix().d-o.get_matrix().b*o.get_matrix().c))
  source=largest.get_bitmap().to_pil();width=source.width
  gray=source.mode in ('1','L')
  bitmap=page.render(scale=width/page.get_width(),grayscale=gray,no_smoothimage=True,no_smoothpath=True,no_smoothtext=True)
  image=bitmap.to_pil().copy();bitmap.close();page.close()
  futures.append(pool.submit(encode,image,i+1))
  if len(futures)>=8:records.append(futures.pop(0).result())
  if (i+1)%100==0:print(f'Compressed {i+1}/1897, {time.monotonic()-start:.1f}s',flush=True)
 records.extend(f.result() for f in futures)
records.sort(key=lambda r:r['page']);assert [r['page'] for r in records]==list(range(1,1898))
m={**old,'format':'Native scan resolution, composed page, lossless PNG/WebP; original color JPEG','bytes':sum(r['bytes'] for r in records),'pages':records,'compression_policy':'No lossy recompression or page downscaling. Image interpolation disabled for original scan composition; output decode pixel hash checked.'}
path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Compact pages:',round(m['bytes']/1024/1024,1),'MiB',flush=True)

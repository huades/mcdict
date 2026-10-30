"""Render immutable source pages and retain their OCR character geometry."""
import pathlib,json,hashlib
import pypdfium2 as pdfium
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'source-index7'/'qa';OUT.mkdir(parents=True,exist_ok=True)
source=next(ROOT.parent.glob('*.pdf'))
assert hashlib.sha256(source.read_bytes()).hexdigest()=='efd0d6b626a306fd633a1ce1c970a03f10435c28be668014f05671c114b80216'
doc=pdfium.PdfDocument(str(source));scale=2.2
for number in range(33,92):
 page=doc[number-1];w,h=page.get_size();name=f'page-{number:04d}'
 if not (OUT/(name+'.png')).exists():page.render(scale=scale).to_pil().save(OUT/(name+'.png'))
 if not (OUT/(name+'-layer.json')).exists():
  text=page.get_textpage();chars=[]
  for i in range(text.count_chars()):
   c=text.get_text_range(i,1)
   if not c.strip():continue
   left,bottom,right,top=text.get_charbox(i)
   chars.append({'t':c,'x':left*scale,'y':(h-top)*scale,'w':(right-left)*scale,'h':(top-bottom)*scale})
  (OUT/(name+'-layer.json')).write_text(json.dumps({'page':number,'scale':scale,'width':w*scale,'height':h*scale,'chars':chars},ensure_ascii=False),encoding='utf-8')
 print('Prepared PDF',number,flush=True)

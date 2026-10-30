from pathlib import Path
from PIL import Image,ImageDraw
import pypdfium2 as pdfium
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'reports/text7-review';out.mkdir(exist_ok=True)
doc=pdfium.PdfDocument(str(next(ROOT.parent.glob('*.pdf'))))
for n in [7,129,270,273,516,517,535,1161,1465,881]:
 page=doc[n+93];text=page.get_textpage();s=text.get_text_range()
 for term in ('安静','草','矛盾','什么','得','行'):
  pos=s.find(term)
  if pos<0:continue
  x1,y1,x2,y2=text.get_charbox(pos);w,h=page.get_size();scale=1.6
  im=page.render(scale=scale).to_pil();left=0 if x1<w/2 else round(w/2*scale)
  top=max(0,round((h-y2)*scale)-55);crop=im.crop((left,top,min(im.width,left+round(w/2*scale)),min(im.height,top+700)))
  crop.save(out/f'{n}-{term}.png')
print('Review crops prepared')

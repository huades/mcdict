"""Source crops for reviewing ambiguous directory-to-section matches."""
import json,collections
from PIL import Image,ImageDraw
from pdf7_parse import ROOT,QA
forms=json.loads((ROOT/'source-index7/catalog.json').read_text(encoding='utf-8'))['forms']
sections=json.loads((ROOT/'source-index7/transcription.json').read_text(encoding='utf-8'))['sections']
groups=collections.defaultdict(list)
for f in forms:groups[(f['number'],f['index_page'],f['alias'])].append(f)
groups={k:v for k,v in groups.items() if len(v)>1}
canvas=Image.new('RGB',(1400,len(groups)*210),'#eeeeee');draw=ImageDraw.Draw(canvas)
for i,(k,fs) in enumerate(groups.items()):
 draw.text((10,i*210+5),str(k),fill='black')
 for j,f in enumerate(fs):
  crop=Image.open(QA/f'page-{f["catalog_pdf"]:04d}.png').crop((f['left']+4,f['top'],f['right']-4,f['bottom']))
  canvas.paste(crop,(15+j*430,i*210+30));draw.text((15+j*430,i*210+85),f['id'],fill='black')
 ss=[s for s in sections if (s['radical'],s['index_paper'],s['alias'])==k]
 for j,s in enumerate(ss):
  crop=Image.open(QA/f'page-{s["index_pdf"]:04d}.png').crop((s['left']+4,s['y']-30,s['right']-4,s['y']+30))
  canvas.paste(crop,(15+j*430,i*210+110));draw.text((15+j*430,i*210+175),s['id'],fill='black')
canvas.save(QA/'matches.png')

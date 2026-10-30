"""Spatial transcription of the source tables; OCR suggestions retain provenance."""
import pathlib,json,re,statistics,itertools
from PIL import Image
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1];QA=ROOT/'source-index7'/'qa'

def load(n,engine):
 p=QA/f'page-{n:04d}-{engine}.json'
 if not p.exists():return []
 data=json.loads(p.read_text(encoding='utf-8-sig'))
 if engine=='windows':return [w for line in data['lines'] for w in line['words']]
 if engine=='layer':return data['chars']
 return data['items']

def rules(n):
 image=Image.open(QA/f'page-{n:04d}.png').convert('L');a=np.array(image)
 y1=1250 if n==33 else 160 if n!=35 else 435
 y2=1970 if n==34 else 2400
 black=a[y1:y2]<145
 # Dilate only horizontally so slightly sloped rules remain measurable.
 horizontal=np.zeros_like(black)
 for shift in range(-4,5):horizontal|=np.roll(black,shift,axis=1)
 scores=horizontal.sum(axis=0);threshold=(y2-y1)*.60
 clusters=[]
 for x,value in enumerate(scores):
  if value<threshold or x<60 or x>image.width-30:continue
  if clusters and x==clusters[-1][-1]+1:clusters[-1].append(x)
  else:clusters.append([x])
 candidates=[int(round(sum(c)/len(c))) for c in clusters if len(c)<40]
 expected=6 if n in (33,34) else 8
 if expected<len(candidates)<expected+5:
  subsets=list(itertools.combinations(candidates,expected))
  candidates=list(min(subsets,key=lambda c:statistics.pstdev(b-a for a,b in zip(c,c[1:]))))
 # Pages occasionally have a slanted outer rule; only the outer edge can be
 # reconstructed from the regular grid, with its actual ink position checked.
 if len(candidates)==expected-1:
  step=statistics.median(b-a for a,b in zip(candidates,candidates[1:]))
  if candidates[0]>image.width*.14:candidates.insert(0,round(candidates[0]-step))
  else:candidates.append(round(candidates[-1]+step))
 if len(candidates)!=expected:raise ValueError(f'PDF{n}: expected {expected} rules, got {candidates}')
 return candidates,y1,y2

def rows(n):
 boundaries,y1,y2=rules(n);words=[dict(w,engine=e) for e in ('windows','rapid') for w in load(n,e)];result=[]
 for column,(left,right) in enumerate(zip(boundaries,boundaries[1:])):
  items=[w for w in words if left<w['x']+w['w']/2<right and y1<w['y']+w['h']/2<y2]
  lines=[]
  for word in sorted(items,key=lambda w:w['y']+w['h']/2):
   cy=word['y']+word['h']/2
   if lines and cy-lines[-1]['cy']<17:
    lines[-1]['words'].append(word);lines[-1]['cy']=statistics.mean(x['y']+x['h']/2 for x in lines[-1]['words'])
   else:lines.append({'cy':cy,'words':[word]})
  for row in lines:
   row['words'].sort(key=lambda w:w['x']);row.update({'page':n,'column':column,'left':left,'right':right,'text':''.join(w['t'] for w in row['words'] if w['engine']=='rapid'),'windows':''.join(w['t'] for w in row['words'] if w['engine']=='windows')})
  result.extend(lines)
 return result

if __name__=='__main__':
 import sys
 pages=[int(x) for x in sys.argv[1:]] or list(range(33,90))
 allrows=[]
 for n in pages:
  try:r=rows(n);allrows.extend(r);print(n,len(r),rules(n)[0])
  except Exception as e:print(e)
 (QA/'spatial-rows.json').write_text(json.dumps(allrows,ensure_ascii=False),encoding='utf-8')
 (QA/'spatial-rows.tsv').write_text('\n'.join(f'{r["page"]}\t{r["column"]}\t{r["cy"]:.1f}\t{r["text"]}' for r in allrows),encoding='utf-8')

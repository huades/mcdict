from pdf7_parse import *
CN={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'零':0,'〇':0}
def number(t):
 if t.isdigit():return int(t)
 if '十' in t:
  a,b=t.split('十');return (CN.get(a,1) if a else 1)*10+CN.get(b,0)
 return CN.get(t)
def stroke_heading(t):
 t=t.replace(' ','').replace('畫','画')
 m=re.fullmatch(r'([一二三四五六七八九十零〇]+)(?:至([一二三四五六七八九十]+))?画(以上)?',t)
 if not m:return None
 low=number(m[1]);return low,99 if m[3] else number(m[2]) if m[2] else low
def page_value(row,engine):
 items=[w for w in row['words'] if w['engine']==engine and w['x']+w['w']/2>row['left']+(row['right']-row['left'])*.60]
 t=''.join(w['t'] for w in sorted(items,key=lambda w:w['x']))
 match=re.search(r'(\d{1,4})\D*$',t)
 return int(match[1]) if match else None
def character(row,engine):
 items=[w for w in row['words'] if w['engine']==engine and w['x']+w['w']/2<row['left']+(row['right']-row['left'])*.55]
 t=''.join(w['t'] for w in sorted(items,key=lambda w:w['x']))
 chars=re.findall(r'[\u3400-\u9fff\U00020000-\U000323af]',t)
 return chars[0] if len(chars)==1 else None

def main():
 corrections_path=ROOT/'source-index7'/'corrections.json'
 corrections=json.loads(corrections_path.read_text(encoding='utf-8')) if corrections_path.exists() else {}
 sections=[];entries=[];issues=[];active=None;group=(None,None);previous=None;last_glyph=None
 for n in range(35,90):
  page_rows=rows(n);image=Image.open(QA/f'page-{n:04d}.png').convert('L');a=np.array(image);layer=load(n,'layer')
  for index,row in enumerate(page_rows):
   txt=row['text'];win=row['windows'];left,right=row['left'],row['right'];width=right-left
   if ('部' in txt or '部' in win) and page_value(row,'rapid') is None and page_value(row,'windows') is None:
    candidates=[r for r in page_rows[max(0,index-3):index][::-1] if r['column']==row['column']]+[row]
    found=None
    for test in candidates:
     s=test['text'] or test['windows'];m=re.search(r'(\d{1,3})',s)
     if m and 1<=int(m[1])<=201:
      central=[w for w in test['words'] if re.search(r'\d',w['t']) and w['x']+w['w']/2<left+width*.75]
      if central:found=(int(m[1]),s,test);break
    if not found:issues.append({'kind':'header-number','page':n,'column':row['column'],'y':row['cy'],'t':txt,'w':win});previous=row;continue
    rid,mark,numberrow=found
    active={'id':f'p{n}c{row["column"]}y{round(row["cy"])}','radical':rid,'label_ocr':txt,'windows':win,'alias':any(c in mark for c in '[]［］'),'index_pdf':n,'index_paper':n-20,'column':row['column'],'y':row['cy'],'left':left,'right':right,'number_y':numberrow['cy']}
    sections.append(active);group=(None,None);last_glyph=None;previous=row;continue
   heading=stroke_heading(txt) or stroke_heading(win)
   if heading is None and previous and previous['column']==row['column']:
    heading=stroke_heading(previous['text']+txt) or stroke_heading(previous['windows']+win)
   for correction in corrections.get('headings',[]):
    if correction['page']==n and correction['column']==row['column'] and abs(correction['y']-row['cy'])<4:heading=tuple(correction['range'])
   if heading:
    group=heading;previous=row;continue
   rapid=page_value(row,'rapid');windows=page_value(row,'windows')
   if rapid is None and windows is None:
    if txt and not re.fullmatch(r'[\[\]（）()\d.。°]+',txt) and any(w['x']>left+width*.20 for w in row['words']):
     if any('画' in t or '畫' in t for t in (txt,win)):issues.append({'kind':'unparsed-heading','page':n,'column':row['column'],'y':row['cy'],'t':txt,'w':win})
    previous=row;continue
   value=rapid if rapid is not None else windows
   if not active:issues.append({'kind':'no-section','page':n,'y':row['cy']});previous=row;continue
   if value<1 or value>1766:
    issues.append({'kind':'page-range','page':n,'column':row['column'],'y':row['cy'],'r':rapid,'w':windows,'t':txt});previous=row;continue
   # Header numbers are central and do not occupy the right-hand page-number field.
   chars=(character(row,'rapid'),character(row,'windows'))
   y=round(row['cy']);glyph_box=(left+7,max(0,y-26),round(left+width*.54),min(image.height,y+26))
   ink=int((a[glyph_box[1]:glyph_box[3],glyph_box[0]:glyph_box[2]]<130).sum())
   continuation=ink<35 and last_glyph is not None
   glyph=last_glyph if continuation else {'box':glyph_box,'source_page':n,'r':chars[0],'w':chars[1]}
   last_glyph=glyph
   trusted=chars[0] is not None and chars[0]==chars[1]
   if continuation:trusted=glyph['r'] is not None and glyph['r']==glyph['w']
   identifier=f'i7:{n}:{row["column"]}:{y}'
   review=corrections.get('pages',{}).get(identifier)
   if review:value=review['value']
   layer_items=[c for c in layer if c['t'].isdigit() and left+width*.60<c['x']+c['w']/2<right and abs(c['y']+c['h']/2-row['cy'])<22]
   layer_text=''.join(c['t'] for c in sorted(layer_items,key=lambda c:c['x']))
   layer_number=int(layer_text) if layer_text and len(layer_text)<=4 else None
   agreement=sum(p==value for p in (rapid,windows,layer_number))
   entry={'id':identifier,'section':active['id'],'radical':active['radical'],'residual_min':group[0],'residual_max':group[1],'body_page':value,'body_pdf':value+94,'index_pdf':n,'index_paper':n-20,'column':row['column'],'y':y,'left':left,'right':right,'rapid_page':rapid,'windows_page':windows,'layer_page':layer_number,'page_agree':rapid==windows and rapid is not None,'page_check':'visual' if review else 'cross_ocr' if agreement>=2 else 'pending','glyph':glyph,'character':glyph['r'] if trusted else None,'ocr_rapid':chars[0],'ocr_windows':chars[1],'continuation':continuation,'ink':ink}
   entries.append(entry)
   if not review and rapid is not None and windows is not None and rapid!=windows:issues.append({'kind':'page-disagree','id':entry['id'],'r':rapid,'w':windows})
   if not review and agreement<2:issues.append({'kind':'page-single','id':entry['id'],'r':rapid,'w':windows,'layer':layer_number})
   previous=row
 data={'sections':sections,'entries':entries,'issues':issues}
 (ROOT/'source-index7'/'transcription.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
 (QA/'sections.tsv').write_text('\n'.join('%s\t%s\t%s\t%s\t%s\t%s\t%s'%(s['index_pdf'],s['column'],round(s['y']),s['radical'],s['alias'],s['label_ocr'],s['windows']) for s in sections),encoding='utf-8')
 print('Sections',len(sections),'canonical IDs',len({s['radical'] for s in sections}),'rows',len(entries),'page agreement',sum(e['page_agree'] for e in entries),'characters agreed',sum(e['character'] is not None for e in entries),'issues',len(issues))
 print('Missing radical IDs',sorted(set(range(1,202))-{s['radical'] for s in sections}))
 print('Issues',json.dumps(issues[:25],ensure_ascii=False))
if __name__=='__main__':main()

from pdf7_parse import *
from pdf7_transcribe import stroke_heading

def id_value(row,engine):
 items=[w for w in row['words'] if w['engine']==engine and w['x']<row['left']+(row['right']-row['left'])*.30]
 text=''.join(w['t'] for w in sorted(items,key=lambda w:w['x']))
 m=re.search(r'\d{1,3}',text)
 value=int(m[0]) if m else None
 return (value if value and value<=201 else None),bool(re.search(r'[\[\]［］]',text))
def index_value(row,engine):
 items=[w for w in row['words'] if w['engine']==engine and w['x']>row['left']+(row['right']-row['left'])*.70]
 text=''.join(w['t'] for w in sorted(items,key=lambda w:w['x']))
 m=re.search(r'\d{2}',text);value=int(m[0]) if m else None
 return value if value and 15<=value<=69 else None

if __name__=='__main__':
 forms=[];group=1;issues=[];last=None
 for n in (33,34):
  for row in rows(n):
   heading=stroke_heading(row['text']) or stroke_heading(row['windows'])
   # Original PDF 34, last column: the printed heading is 十一画.
   if n==34 and row['column']==4 and abs(row['cy']-681)<8:heading=(11,11)
   if heading:group=heading[0];continue
   rapid,ra=id_value(row,'rapid');windows,wa=id_value(row,'windows');rid=rapid or windows
   rp=index_value(row,'rapid');wp=index_value(row,'windows');target=rp or wp
   if rid is None:
    if last and last['index_page'] is None and target is not None:
     last['index_page']=target;last['bottom']=round(row['cy']+25);last['wrap']=True
    continue
   form={'id':f'r7:{n}:{row["column"]}:{round(row["cy"])}','number':rid,'strokes':group,'alias':ra or wa,'catalog_pdf':n,'column':row['column'],'y':round(row['cy']),'left':row['left'],'right':row['right'],'top':round(row['cy']-26),'bottom':round(row['cy']+26),'index_page':target,'rapid_id':rapid,'windows_id':windows,'rapid_index':rp,'windows_index':wp,'rapid_text':row['text'],'windows_text':row['windows']}
   forms.append(form);last=form
   if (rapid and windows and rapid!=windows) or (rp and wp and rp!=wp):issues.append(form)
 # Main radical stroke boundaries were read from the original directory headings.
 # They also catch OCR's occasional missed heading, without inferring stroke counts.
 starts=[(1,1),(6,2),(27,3),(61,4),(100,5),(122,6),(149,7),(168,8),(179,9),(188,10),(192,11),(195,12),(198,13),(200,14),(201,17)]
 for form in forms:
  if not form['alias']:
   expected=max((s for first,s in starts if first<=form['number']),default=1)
   if form['strokes']!=expected:issues.append(dict(form,problem='stroke-heading',expected=expected))
 # OCR disagreements visually checked against PDF 33-34; values are literal
 # directory readings, not Unicode or fifth-edition substitutions.
 verified={'r7:33:2:2278':(185,3,68),'r7:34:0:1727':(101,5,49),'r7:34:0:1864':(67,5,37),'r7:34:1:245':(105,5,50),'r7:34:2:1124':(148,6,59),'r7:34:2:1371':(151,7,60),'r7:34:4:341':(57,9,33),'r7:34:4:439':(188,10,69),'r7:34:4:778':(149,11,60)}
 reviewed=[f for f in issues if verified.get(f['id'])==(f['number'],f['strokes'],f['index_page'])]
 issues=[f for f in issues if f not in reviewed]
 data={'forms':forms,'issues':issues,'visually_reviewed':reviewed}
 (ROOT/'source-index7'/'catalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Catalog forms',len(forms),'main IDs',len({f['number'] for f in forms if not f['alias']}),'missing main',sorted(set(range(1,202))-{f['number'] for f in forms if not f['alias']}),'issues',len(issues))
 for form in issues:print(form)

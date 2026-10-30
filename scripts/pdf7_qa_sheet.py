from pdf7_parse import *
from PIL import ImageDraw,ImageFont
data=json.loads((ROOT/'source-index7'/'transcription.json').read_text(encoding='utf-8'))
font=ImageFont.load_default(size=14)
issues=data['issues'];sheet=Image.new('RGB',(1050,((len(issues)+2)//3)*110),'#e8efe8');draw=ImageDraw.Draw(sheet)
for index,issue in enumerate(issues):
 if 'id' in issue:
  _,n,c,y=issue['id'].split(':');n=int(n);c=int(c);y=int(y)
 else:n=issue['page'];c=issue['column'];y=round(issue['y'])
 boundaries,*_=rules(n);left,right=boundaries[c:c+2]
 image=Image.open(QA/f'page-{n:04d}.png');crop=image.crop((left+3,max(0,y-40),right-3,y+40)).convert('RGB')
 x=(index%3)*350;yout=(index//3)*110
 label=f'{index}: PDF{n} c{c} y{y} {issue["kind"]} '+str(issue.get('r',issue.get('t','')))+'/'+str(issue.get('w',''))
 draw.text((x+4,yout+2),label,font=font,fill='black');sheet.paste(crop,(x+5,yout+25))
sheet.save(QA/'issues-contact.png')
print(len(issues))

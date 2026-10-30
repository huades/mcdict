"""Reproducible local MOBI -> SQLite dictionary. Source books are never edited."""
from extract_source import extract,ROOT
import pathlib,re,html,sqlite3,json,hashlib,unicodedata,urllib.request,zipfile,io,bisect
from bs4 import BeautifulSoup

OUT=ROOT/'generated'; OUT.mkdir(exist_ok=True)
IMAGES=OUT/'images'; IMAGES.mkdir(exist_ok=True)
def fetch(url,name):
    target=OUT/name
    if not target.exists():
        with urllib.request.urlopen(url,timeout=90) as response: target.write_bytes(response.read())
    return target.read_bytes()
def norm(s): return unicodedata.normalize('NFC',s).casefold().strip()
def pykey(s):
    s=s.lower().replace('u:','ü').replace('v','ü'); out=''
    for c in s:
        if c in 'üǖǘǚǜ': out+='v'
        elif c.isascii() and c.isalpha(): out+=c
        else: out+=''.join(x for x in unicodedata.normalize('NFD',c) if x.isascii() and x.isalpha())
    return out
def tokens(s):
    return ' '.join(re.findall(r'[a-z0-9]+|[^\x00-\x7f\s]',norm(s)))

raw,records,firstimg=extract()
assert len(raw)==9453696
matches=list(re.finditer(rb'<b>(.*?)</b>',raw,re.S))
assert len(matches)==65738
starts=[raw.rfind(b'<p',0,m.start()) for m in matches]
dbfile=OUT/'dictionary.db'
if dbfile.exists(): dbfile.unlink()
db=sqlite3.connect(dbfile)
db.executescript('''PRAGMA journal_mode=OFF;PRAGMA synchronous=OFF;
CREATE TABLE entries(id TEXT PRIMARY KEY, head TEXT,head_html TEXT,pinyin TEXT,pinyin_key TEXT,initials TEXT,body_html TEXT,body_text TEXT,ordinal INTEGER,unknown_glyph INTEGER);
CREATE INDEX head_idx ON entries(head);CREATE INDEX py_idx ON entries(pinyin_key);CREATE INDEX init_idx ON entries(initials);
CREATE VIRTUAL TABLE fulltext USING fts4(text,tokenize=simple);
CREATE TABLE glyphs(codepoint TEXT,radical INTEGER,residual INTEGER,total INTEGER,PRIMARY KEY(codepoint,radical,residual));
CREATE TABLE radicals(number INTEGER,label TEXT,PRIMARY KEY(number));
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);''')
images={}; pending=[]; bad_links=0; unknown_count=0
def image_tag(tag):
    index=int(tag.get('recindex','0')); resource=firstimg+index-1
    alt=tag.get('alt',''); character=None
    if re.fullmatch(r'[0-9a-fA-F]{4,6}',alt):
        point=int(alt,16)
        if not (0xE000<=point<=0xF8FF or 0xF0000<=point<=0x10FFFD): character=chr(point)
    if resource not in images:
        binary=records[resource]
        ext='png' if binary.startswith(b'\x89PNG') else 'jpg' if binary.startswith(b'\xff\xd8') else 'gif'
        name=f'{index}.{ext}'; (IMAGES/name).write_bytes(binary);images[resource]=name
    return f'<img class="glyph" src="images/{images[resource]}" alt="{html.escape(character or "原书字形")}">',character
def sanitize(fragment):
    soup=BeautifulSoup(fragment,'html.parser')
    for tag in list(soup.find_all(True)):
        if tag.name=='img':
            markup,_=image_tag(tag);tag.replace_with(BeautifulSoup(markup,'html.parser'));continue
        if tag.name=='a':
            pos=tag.get('filepos',''); tag.attrs={'data-pos':pos};continue
        if tag.name in ('br','p','b','i','small','sup','sub','strong','em'):
            tag.attrs={}
        else: tag.unwrap()
    return str(soup)
for ordinal,m in enumerate(matches):
    start=starts[ordinal];end=raw.find(b'<hr',m.end())
    if end<0:end=len(raw)
    fragment=raw[start:end].decode('utf-8')
    head_soup=BeautifulSoup(m.group(1).decode('utf-8'),'html.parser');unknown=False
    for tag in list(head_soup.find_all('img')):
        _,ch=image_tag(tag);unknown|=ch is None;tag.replace_with(ch or '□')
    head=norm(head_soup.get_text()).replace(' ','')
    firstpara=fragment[:fragment.find('</p>')+4]
    tail=firstpara[firstpara.find('</b>')+4:]
    py=BeautifulSoup(tail,'html.parser').get_text(' ',strip=True)
    py=re.sub(r'^[（(][^）)]*[）)]','',py).strip()
    key=pykey(py)
    # Tone-bearing vowels and explicit separators locate syllable starts. Ambiguous
    # neutral syllables are handled by the legal-syllable dynamic program below.
    parts=re.split(r'[\s·∥’\x27\-—]+',py)
    head_html=sanitize(m.group(1).decode('utf-8'))
    body=sanitize(fragment[fragment.find('</b>')+4:])
    text=BeautifulSoup(body,'html.parser').get_text(' ',strip=True)
    identifier=f'xdhy5:{start}'
    pending.append((identifier,head,head_html,py,key,body,text,ordinal,int(unknown)))
    if unknown:unknown_count+=1
    if ordinal%10000==0:print('Parsed',ordinal,flush=True)

# Every split must be made of a standard syllable; source tone marks / apostrophes
# provide boundaries. Generate alternative initials for genuinely ambiguous splits.
syllables=set('a ai an ang ao ba bai ban bang bao bei ben beng bi bian biao bie bin bing bo bu ca cai can cang cao ce cen ceng cha chai chan chang chao che chen cheng chi chong chou chu chua chuai chuan chuang chui chun chuo ci cong cou cu cuan cui cun cuo da dai dan dang dao de dei den deng di dia dian diao die ding diu dong dou du duan dui dun duo e ei en eng er fa fan fang fei fen feng fo fou fu ga gai gan gang gao ge gei gen geng gong gou gu gua guai guan guang gui gun guo ha hai han hang hao he hei hen heng hng hm hong hou hu hua huai huan huang hui hun huo ji jia jian jiang jiao jie jin jing jiong jiu ju juan jue jun ka kai kan kang kao ke kei ken keng kong kou ku kua kuai kuan kuang kui kun kuo la lai lan lang lao le lei leng li lia lian liang liao lie lin ling liu lo long lou lu luan lun luo lv lve ma mai man mang mao me mei men meng mi mian miao mie min ming miu mo mou mu na nai nan nang nao ne nei nen neng ng ni nian niang niao nie nin ning niu nong nou nu nuan nuo nv nve o ou pa pai pan pang pao pei pen peng pi pian piao pie pin ping po pou pu qi qia qian qiang qiao qie qin qing qiong qiu qu quan que qun ran rang rao re ren reng ri rong rou ru ruan rui run ruo sa sai san sang sao se sen seng sha shai shan shang shao she shei shen sheng shi shou shu shua shuai shuan shuang shui shun shuo si song sou su suan sui sun suo ta tai tan tang tao te teng ti tian tiao tie ting tong tou tu tuan tui tun tuo wa wai wan wang wei wen weng wo wu xi xia xian xiang xiao xie xin xing xiong xiu xu xuan xue xun ya yan yang yao ye yi yin ying yo yong you yu yuan yue yun za zai zan zang zao ze zei zen zeng zha zhai zhan zhang zhao zhe zhei zhen zheng zhi zhong zhou zhu zhua zhuai zhuan zhuang zhui zhun zhuo zi zong zou zu zuan zui zun zuo'.split())
def initials(py,head):
    pieces=re.split(r'[\s·∥’\x27\-—]+',py.lower()); choices=['']
    for piece in pieces:
        if not piece:continue
        # A tone mark ends the vowel nucleus, so the next consonant can start a syllable.
        key=pykey(piece); memo={len(key):['']}
        def split(i):
            if i in memo:return memo[i]
            result=[]
            for size in range(1,7):
                s=key[i:i+size]
                if i+size<=len(key) and (s in syllables or (s.endswith('r') and s[:-1] in syllables)):
                    for rest in split(i+size):result.append(s[0]+rest)
            memo[i]=sorted(set(result),key=lambda x:(len(x),x))[:8];return memo[i]
        variants=split(0) or [key[:1]]
        choices=sorted(set(a+b for a in choices for b in variants),key=lambda x:(len(x),x))[:16]
    expected=len(head)
    if expected>1 and head.endswith('儿') and py.endswith('r') and not re.search(r'[eéěèē]r$',py): expected-=1
    exact=[x for x in choices if len(x)==expected]
    return '|'.join(exact or choices[:1])
for identifier,head,head_html,py,key,body,text,ordinal,unknown in pending:
    def link(match):
        global bad_links
        pos=match.group(1)
        if not pos.isdigit():bad_links+=1;return '<span class="broken-ref"'
        i=bisect.bisect_right(starts,int(pos))-1
        if i<0:bad_links+=1;return '<span class="broken-ref"'
        return f'<a data-entry="xdhy5:{starts[i]}"'
    body=re.sub(r'<a data-pos="([^"]*)"',link,body)
    # Invalid source anchors remain readable but have no active navigation.
    body=re.sub(r'(<span class="broken-ref"[^>]*>)(.*?)</a>',r'\1\2</span>',body,flags=re.S)
    db.execute('INSERT INTO entries VALUES(?,?,?,?,?,?,?,?,?,?)',(identifier,head,head_html,py,key,initials(py,head),body,text,ordinal,unknown))
    db.execute('INSERT INTO fulltext(rowid,text) VALUES(?,?)',(ordinal+1,tokens(head+' '+text)))
print('Building auxiliary radical index',flush=True)
unihan=fetch('https://www.unicode.org/Public/18.0.0/ucd/Unihan.zip','Unihan-18.0.0.zip')
fields={}
with zipfile.ZipFile(io.BytesIO(unihan)) as z:
    for name in z.namelist():
        for line in z.read(name).decode('utf-8').splitlines():
            if line.startswith('#') or not line:continue
            cp,field,value=line.split('\t',2)
            if field in ('kRSUnicode','kTotalStrokes'):fields.setdefault(cp,{})[field]=value
heads={h for _,h,*_ in pending if len(h)==1 and h!='□'}
for cp,f in fields.items():
    ch=chr(int(cp[2:],16))
    if ch not in heads:continue
    total=int(f.get('kTotalStrokes','0').split()[0])
    for rs in f.get('kRSUnicode','').split():
        r,s=rs.split('.');db.execute('INSERT OR IGNORE INTO glyphs VALUES(?,?,?,?,?)'.replace('?,?,?,?,?','?,?,?,?'),(ch,int(r.replace("'",'')),int(s),total))
radicals=fetch('https://www.unicode.org/Public/18.0.0/ucd/CJKRadicals.txt','CJKRadicals.txt').decode('utf-8')
for line in radicals.splitlines():
    if not line or line.startswith('#'):continue
    n,rad,ch=[p.strip() for p in line.split('#')[0].split(';')]
    if "'" not in n:db.execute('INSERT INTO radicals VALUES(?,?)',(int(n),chr(int(ch,16))))
license_data=fetch('https://www.unicode.org/license.txt','unicode-license.txt')
meta={'edition':'第5版（2005）','entryCount':len(pending),'unknownGlyphEntries':unknown_count,'sourceBrokenLinks':bad_links,'unihanVersion':'18.0.0','mobiSha256':hashlib.sha256(next(ROOT.parent.glob('*.mobi')).read_bytes()).hexdigest(),'pdfSha256':hashlib.sha256(next(ROOT.parent.glob('*.pdf')).read_bytes()).hexdigest(),'unihanSha256':hashlib.sha256(unihan).hexdigest()}
for k,v in meta.items():db.execute('INSERT INTO metadata VALUES(?,?)',(k,str(v)))
db.commit();db.execute('VACUUM');db.close()
(OUT/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(meta,ensure_ascii=False),flush=True)

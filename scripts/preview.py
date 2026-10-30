"""Local developer preview, bound only to loopback. Android uses the Java API."""
import http.server,json,pathlib,sqlite3,re,unicodedata,urllib.parse,sys,mimetypes,contextlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
state={}
def key(q):
    q=q.lower().replace('u:','ü').replace('v','ü');out=''
    for c in q:
        if c in 'üǖǘǚǜ':out+='v'
        else:out+=''.join(x for x in unicodedata.normalize('NFD',c) if x.isascii() and x.isalpha())
    return out
def query(p):
    action=p['action']
    if action=='init':return {'user':state,'manifest':json.loads((ROOT/'generated/manifest7.json').read_text(encoding='utf-8'))}
    if action=='saveUser':state.clear();state.update(p['user']);return {}
    if action in ('speak','pdf','export','import'):return {'error':'此功能请在安卓安装版中验证'}
    db=sqlite3.connect(ROOT/('generated/dictionary.db' if p.get('edition',7)==5 or p.get('id','').startswith('xdhy5:') else 'generated/dictionary7.db'));db.row_factory=sqlite3.Row
    def rows(sql,args=()):return [dict(r) for r in db.execute(sql,args)]
    try:
        if action=='detail':return rows('SELECT * FROM entries WHERE id=?',(p['id'],))[0]
        if action in ('radicals','glyphs','sameCharacter'):
            with contextlib.closing(sqlite3.connect(ROOT/'generated/index7.db')) as index:
                index.row_factory=sqlite3.Row
                def ir(sql,args=()):return [dict(r) for r in index.execute(sql,args)]
                if action=='radicals':return {'items':ir('SELECT * FROM forms ORDER BY ordinal')}
                if action=='sameCharacter':
                    a=ir('SELECT character FROM glyphs WHERE id=? AND character IS NOT NULL',(p['id'],))
                    if p.get('edition',7)!=5:
                        ids=[x['entry_id'] for x in ir('SELECT DISTINCT entry_id FROM entry_links WHERE glyph_id=?',(p['id'],))]
                        return {'items':rows('SELECT id,head,head_html,pinyin FROM entries WHERE id IN('+','.join('?' for _ in ids)+') ORDER BY ordinal',ids) if ids else []}
                    return {'items':rows('SELECT id,head,head_html,pinyin FROM entries WHERE head=? ORDER BY ordinal',(a[0]['character'],)) if a else []}
                form=ir('SELECT section FROM forms WHERE id=?',(p.get('radical',''),))
                if not form:raise ValueError('请先选择第7版部首')
                section=form[0]['section'];text_mode=p.get('mode')=='text';base=' WHERE section=?'+(' AND id IN(SELECT glyph_id FROM entry_links)' if text_mode else '');w=base;args=[section];group=p.get('group','all')
                groups=ir('SELECT residual_min,residual_max,'+('count(distinct character)' if text_mode else 'count(*)')+' AS count FROM glyphs'+base+' GROUP BY residual_min,residual_max ORDER BY residual_min',(section,))
                if group=='none':w+=' AND residual_min IS NULL'
                elif group!='all':
                    lo,hi=map(int,group.split(':'));w+=' AND residual_min=? AND residual_max=?';args.extend((lo,hi))
                total=ir('SELECT '+('count(distinct character)' if text_mode else 'count(*)')+' AS count FROM glyphs'+w,args)[0]['count']
                columns='SELECT *,min(ordinal) AS first_ordinal,group_concat(distinct body_page) AS body_pages,(SELECT group_concat(distinct pinyin) FROM entry_links WHERE glyph_id=glyphs.id) AS readings FROM glyphs' if text_mode else 'SELECT * FROM glyphs'
                a=ir(columns+w+(' GROUP BY character' if text_mode else '')+' ORDER BY ordinal LIMIT 61 OFFSET ?',args+[max(0,p.get('offset',0))])
                return {'items':a[:60],'more':len(a)>60,'groups':groups,'total':total}
        q=p.get('query','').lower().strip();off=p.get('offset',0);cols='SELECT id,head,head_html,pinyin,substr(body_text,1,65) summary,unknown_glyph FROM entries '
        if p.get('edition',7)!=5:
            alias=rows('SELECT target FROM aliases WHERE alias=? COLLATE NOCASE LIMIT 1',(q,))
            if alias:q=alias[0]['target']
        if not q:return {'items':[],'more':False}
        if p.get('mode')=='full':
            tokens=re.findall(r'[a-z0-9]+|[^\x00-\x7f\s]',q);t=' '.join('"'+s.replace('"','""')+'"' for s in tokens)
            a=rows(cols+'WHERE rowid IN(SELECT rowid FROM fulltext WHERE fulltext MATCH ?) AND instr(lower(body_text),?)>0 ORDER BY ordinal LIMIT 51 OFFSET ?',(t,q,off)) if t else []
        elif re.fullmatch(r'[a-züǖǘǚǜāáǎàēéěèīíǐìōóǒòūúǔùńňǹḿ \'’·∥:0-9-]+',q):
            k=key(q);a=rows(cols+"WHERE head=? COLLATE NOCASE OR pinyin_key LIKE ? OR ('|'||initials||'|') LIKE ? ORDER BY CASE WHEN head=? COLLATE NOCASE THEN -1 WHEN pinyin_key=? THEN 0 WHEN pinyin_key LIKE ? THEN 1 ELSE 2 END,ordinal LIMIT 51 OFFSET ?",(q,k+'%','%|'+k+'|%',q,k,k+'%',off))
        else:a=rows(cols+'WHERE head LIKE ? ORDER BY CASE WHEN head=? THEN 0 WHEN head LIKE ? THEN 1 ELSE 2 END,ordinal LIMIT 51 OFFSET ?',('%'+q+'%',q,q+'%',off))
        return {'items':a[:50],'more':len(a)>50}
    finally:db.close()
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        name=urllib.parse.unquote(urllib.parse.urlparse(self.path).path).lstrip('/') or 'index.html'
        if '..' in name:return self.send_error(403)
        file=ROOT/('web' if name in ('index.html','app.js','app.css','ui-utils.js') else 'generated')/name
        if not file.is_file():return self.send_error(404)
        data=file.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_POST(self):
        try:
            if self.path!='/api':return self.send_error(404)
            data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));answer=query(data)
        except Exception as e:answer={'error':str(e)}
        raw=json.dumps(answer,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
if __name__=='__main__':
    print('Preview: http://127.0.0.1:4186',flush=True);http.server.ThreadingHTTPServer(('127.0.0.1',4186),Handler).serve_forever()

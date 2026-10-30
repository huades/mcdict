import unittest,sqlite3,pathlib,re,json,time,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import preview
def query5(p):return preview.query(dict(p,edition=5))
class DataTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.db=sqlite3.connect(ROOT/'generated/dictionary.db')
 def test_integrity(self):
  self.assertEqual(self.db.execute('pragma integrity_check').fetchone()[0],'ok');self.assertEqual(self.db.execute('select count(*) from entries').fetchone()[0],65738)
  self.assertEqual(self.db.execute("select count(*) from entries where head='' or id='' ").fetchone()[0],0)
 def test_polyphonic(self):
  self.assertEqual(self.db.execute('select count(*) from entries where head=?',('行',)).fetchone()[0],4)
  self.assertEqual(self.db.execute('select count(*) from entries where head=?',('得',)).fetchone()[0],4)
  self.assertGreaterEqual(self.db.execute('select count(*) from entries where head=?',('略',)).fetchone()[0],3)
 def test_umlaut(self):
  for q in ('lü','lv','lu:'):
   result=query5({'action':'search','query':q});self.assertIn('吕',[e['head'] for e in result['items']])
  self.assertNotEqual(preview.key('lu'),preview.key('lü'))
 def test_initials(self):
  self.assertIn('安静',[x['head'] for x in query5({'action':'search','query':'aj'})['items']])
  self.assertEqual(self.db.execute('select initials from entries where head=?',('安静',)).fetchone()[0],'aj')
 def test_fulltext(self):
  self.assertIn('安静',[x['head'] for x in query5({'action':'search','query':'没有声音','mode':'full'})['items']])
 def test_glyphs(self):
  self.assertEqual(self.db.execute('select count(*) from entries where unknown_glyph=1').fetchone()[0],418)
  self.assertTrue(self.db.execute('select head_html from entries where head=?',('𩽾',)).fetchone())
  for body,head in self.db.execute('select body_html,head_html from entries'):
   self.assertNotRegex(body+head,r'<(?:script|iframe|object)\b|onerror=|javascript:')
   for name in re.findall(r'src="images/([^"]+)"',body+head):self.assertTrue((ROOT/'generated/images'/name).is_file())
 def test_links(self):
  ids={r[0] for r in self.db.execute('select id from entries')}
  for body, in self.db.execute('select body_html from entries'):
   for target in re.findall('data-entry="([^"]+)"',body):self.assertIn(target,ids)
 def test_radicals(self):
  forms=query5({'action':'radicals'})['items']
  self.assertEqual(len(forms),279)
  self.assertEqual({f['number'] for f in forms if not f['alias']},set(range(1,202)))
  for f in forms:self.assertTrue((ROOT/'generated'/f['image']).is_file())
 def test_grass_component(self):
  form=next(f for f in query5({'action':'radicals'})['items'] if f['number']==30 and not f['alias'])
  self.assertEqual(form['strokes'],3)
  result=query5({'action':'glyphs','radical':form['id'],'group':'6:6'})
  grass=next(r for r in result['items'] if r['character']=='草')
  self.assertEqual(grass['body_pdf'],grass['body_page']+94)
  same=query5({'action':'sameCharacter','id':grass['id']})['items']
  self.assertTrue(same);self.assertEqual({e['head'] for e in same},{'草'})
 def test_index_source_integrity(self):
  with sqlite3.connect(ROOT/'generated/index7.db') as db:
   self.assertEqual(db.execute('pragma integrity_check').fetchone()[0],'ok')
   self.assertEqual(db.execute('select count(*) from glyphs').fetchone()[0],16751)
   self.assertEqual(db.execute('select count(*) from glyphs where body_pdf!=body_page+94 or body_page<1 or body_page>1766 or page_check not in (\'visual\',\'cross_ocr\')').fetchone()[0],0)
   self.assertEqual(db.execute('select count(*) from glyphs g left join forms f on g.section=f.section where f.id is null').fetchone()[0],0)
   self.assertEqual(db.execute('select count(*) from glyphs where residual_min is null').fetchone()[0],2510)
   # Traverse all pages through the actual API: no 250-item truncation or lost duplicate references.
   for form,section in db.execute('select id,section from forms'):
    result=query5({'action':'glyphs','radical':form});seen=[]
    while True:
     seen.extend(e['id'] for e in result['items'])
     if not result['more']:break
     result=query5({'action':'glyphs','radical':form,'offset':len(seen)})
    self.assertEqual(len(set(seen)),db.execute('select count(*) from glyphs where section=?',(section,)).fetchone()[0])
 def test_editions(self):
  m=json.loads((ROOT/'generated/manifest.json').read_text(encoding='utf-8'));self.assertEqual(m['edition'],'第5版（2005）');self.assertEqual(m['unihanVersion'],'18.0.0')
  self.assertFalse(self.db.execute("select 1 from entries where head='动车'").fetchone())
 def test_search_performance(self):
  measurements=[]
  for q in ['安静','行','aj','lv','xue','没有声音']:
   start=time.perf_counter();r=query5({'action':'search','query':q,'mode':'full' if q=='没有声音' else 'auto'});measurements.append(round((time.perf_counter()-start)*1000,1));self.assertLessEqual(len(r['items']),50)
  print('Desktop query times (ms):',measurements)
if __name__=='__main__':unittest.main(verbosity=2)

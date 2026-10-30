import unittest,sqlite3,pathlib,sys,json,re
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import preview
class Text7Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.db=sqlite3.connect(ROOT/'generated/dictionary7.db')
 def test_complete_and_separate(self):
  self.assertEqual(self.db.execute('pragma integrity_check').fetchone()[0],'ok')
  self.assertEqual(self.db.execute('select count(*) from entries').fetchone()[0],70113)
  self.assertEqual(self.db.execute("select count(*) from entries where id not like 'xdhy7:%' or body_text='' or head=''").fetchone()[0],0)
  self.assertFalse(json.loads((ROOT/'generated/manifest7.json').read_text(encoding='utf-8'))['official'])
 def test_readings(self):
  for head,expected in [('行',{'háng','hàng','héng','xíng'}),('得',{'dé','·de','děi'}),('绿',{'lù','lǜ'})]:self.assertEqual({r[0] for r in self.db.execute('select pinyin from entries where head=?',(head,))},expected)
  self.assertEqual(self.db.execute('select count(*) from entries where head=?',('略',)).fetchone()[0],3)
 def test_confirmed_correction(self):self.assertEqual(self.db.execute('select pinyin from entries where head=?',('矛盾',)).fetchone()[0],'máodùn')
 def test_default7_backup5(self):
  seven=preview.query({'action':'search','query':'动车'})['items'];self.assertTrue(seven);self.assertTrue(all(e['id'].startswith('xdhy7:') for e in seven))
  self.assertFalse(preview.query({'action':'search','query':'动车','edition':5})['items'])
  old=preview.query({'action':'search','query':'安静','edition':5})['items'][0]
  self.assertEqual(preview.query({'action':'detail','id':old['id']})['id'],old['id'])
 def test_search(self):
  for q,head in [('aj','安静'),('lv','吕'),('lu:','吕'),('anjing','安静'),('maodun','矛盾'),('AI','AI')]:self.assertIn(head,[e['head'] for e in preview.query({'action':'search','query':q})['items']],q)
  self.assertIn('安静',[e['head'] for e in preview.query({'action':'search','query':'没有声音','mode':'full'})['items']])
 def test_aliases(self):
  self.assertEqual(self.db.execute('select count(*) from aliases').fetchone()[0],4698)
  self.assertEqual(self.db.execute('select count(*) from aliases where target not in(select head from entries)').fetchone()[0],0)
  for alias,target in self.db.execute('select alias,target from aliases limit 20'):self.assertIn(target,[e['head'] for e in preview.query({'action':'search','query':alias})['items']])
 def test_all_html(self):
  for head,body in self.db.execute('select head_html,body_html from entries'):
   self.assertNotRegex(head+body,r'<(?:script|iframe|object|embed)\b|onerror=|javascript:|<link\b')
   self.assertNotIn('\ufffd',head+body)
 def test_radical_text_candidates(self):
  form=next(f for f in preview.query({'action':'radicals'})['items'] if f['number']==30 and not f['alias'])
  result=preview.query({'action':'glyphs','radical':form['id'],'mode':'text','group':'6:6'})
  grass=next(g for g in result['items'] if g['character']=='草');self.assertIn('cǎo',grass['readings'])
  self.assertEqual(len({g['character'] for g in result['items']}),len(result['items']))
  entries=preview.query({'action':'sameCharacter','id':grass['id'],'edition':7})['items'];self.assertTrue(entries);self.assertTrue(all(e['id'].startswith('xdhy7:') for e in entries))
  for g in result['items']:self.assertTrue(g['character']);self.assertTrue(preview.query({'action':'sameCharacter','id':g['id'],'edition':7})['items'])
  with sqlite3.connect(ROOT/'generated/index7.db') as index:
   index.execute('ATTACH DATABASE ? AS text7',(str(ROOT/'generated/dictionary7.db'),))
   self.assertEqual(index.execute('SELECT count(*) FROM entry_links l LEFT JOIN text7.entries e ON e.id=l.entry_id WHERE e.id IS NULL').fetchone()[0],0)
if __name__=='__main__':unittest.main(verbosity=2)

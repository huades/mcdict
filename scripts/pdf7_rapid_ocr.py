import pathlib,sys,json,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.ocrdeps'))
from rapidocr import RapidOCR
QA=ROOT/'source-index7'/'qa'
engine=RapidOCR(params={'Global.max_side_len':4000,'Det.limit_side_len':2200,'Det.limit_type':'max','Global.use_cls':False,'EngineConfig.onnxruntime.intra_op_num_threads':4,'EngineConfig.onnxruntime.inter_op_num_threads':1,'Global.log_level':'warning'})
first=int(sys.argv[1]) if len(sys.argv)>1 else 33
last=int(sys.argv[2]) if len(sys.argv)>2 else 91
for n in range(first,last+1):
 output=QA/f'page-{n:04d}-rapid.json'
 if output.exists():continue
 start=time.monotonic();r=engine(str(QA/f'page-{n:04d}.png'))
 items=[]
 if r.txts is not None:
  for box,txt,score in zip(r.boxes,r.txts,r.scores):
   items.append({'t':txt,'score':float(score),'x':float(box[:,0].min()),'y':float(box[:,1].min()),'w':float(box[:,0].max()-box[:,0].min()),'h':float(box[:,1].max()-box[:,1].min())})
 output.write_text(json.dumps({'page':n,'engine':'RapidOCR 3.10 / PP-OCRv6','items':items},ensure_ascii=False),encoding='utf-8')
 print(f'Cross-OCR PDF {n}: {len(items)} boxes, {time.monotonic()-start:.1f}s',flush=True)

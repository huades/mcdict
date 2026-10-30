package io.github.huades.hanyudictionary.offline;
import android.content.Context;import android.graphics.*;import android.view.*;

/** A measured viewport, independent of nested ScrollView/ImageView measurement. */
public final class BookPageView extends View {
 private Bitmap bitmap;private float zoom=1,x=0,y=0,lastX,lastY;private boolean dragging;
 private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
 private final ScaleGestureDetector pinch;private final GestureDetector taps;
 private Runnable zoomListener;private String message="正在读取原书…";
 public BookPageView(Context context){super(context);setLayerType(View.LAYER_TYPE_SOFTWARE,null);
  pinch=new ScaleGestureDetector(context,new ScaleGestureDetector.SimpleOnScaleGestureListener(){
   public boolean onScale(ScaleGestureDetector d){scale(zoom*d.getScaleFactor(),d.getFocusX(),d.getFocusY());return true;}
  });
  taps=new GestureDetector(context,new GestureDetector.SimpleOnGestureListener(){
   public boolean onDown(android.view.MotionEvent e){return true;}
   public boolean onDoubleTap(android.view.MotionEvent e){scale(zoom>1?1:2,e.getX(),e.getY());return true;}
  });setContentDescription("第7版原书页面，可双指缩放、拖动或双击放大");
 }
 public void setZoomListener(Runnable listener){zoomListener=listener;}
 public float getZoom(){return zoom;}
 public void setZoom(float value){scale(value,getWidth()/2f,getHeight()/2f);}
 public void showMessage(String text){message=text;invalidate();}
 public void setPage(Bitmap value){Bitmap old=bitmap;bitmap=value;zoom=1;x=0;y=0;clamp();invalidate();if(old!=null&&old!=value)old.recycle();}
 public void release(){if(bitmap!=null){bitmap.recycle();bitmap=null;}}
 private float base(){return bitmap==null||getWidth()==0?1:getWidth()/(float)bitmap.getWidth();}
 private void scale(float value,float fx,float fy){float next=Math.max(1,Math.min(4,value)),ratio=next/zoom;x=fx-(fx-x)*ratio;y=fy-(fy-y)*ratio;zoom=next;clamp();invalidate();if(zoomListener!=null)zoomListener.run();}
 private void clamp(){if(bitmap==null)return;float w=bitmap.getWidth()*base()*zoom,h=bitmap.getHeight()*base()*zoom;x=w<=getWidth()?(getWidth()-w)/2:Math.max(getWidth()-w,Math.min(0,x));y=h<=getHeight()?(getHeight()-h)/2:Math.max(getHeight()-h,Math.min(0,y));}
 @Override protected void onSizeChanged(int w,int h,int ow,int oh){clamp();invalidate();}
 @Override protected void onDraw(Canvas canvas){super.onDraw(canvas);canvas.drawColor(0xffdfe4dd);
  if(bitmap==null){paint.setColor(0xff42564b);paint.setTextSize(16*getResources().getDisplayMetrics().scaledDensity);paint.setTextAlign(Paint.Align.CENTER);canvas.drawText(message,getWidth()/2f,getHeight()/2f,paint);return;}
  float s=base()*zoom;canvas.drawBitmap(bitmap,null,new RectF(x,y,x+bitmap.getWidth()*s,y+bitmap.getHeight()*s),paint);
 }
 @Override public boolean onTouchEvent(android.view.MotionEvent event){pinch.onTouchEvent(event);taps.onTouchEvent(event);
  if(event.getActionMasked()==MotionEvent.ACTION_DOWN){lastX=event.getX();lastY=event.getY();dragging=true;}
  else if(event.getActionMasked()==MotionEvent.ACTION_MOVE){if(dragging&&!pinch.isInProgress()&&event.getPointerCount()==1){x+=event.getX()-lastX;y+=event.getY()-lastY;clamp();invalidate();}lastX=event.getX();lastY=event.getY();}
  else if(event.getActionMasked()==MotionEvent.ACTION_POINTER_UP)dragging=false;
  else if(event.getActionMasked()==MotionEvent.ACTION_UP||event.getActionMasked()==MotionEvent.ACTION_CANCEL){dragging=false;performClick();}
  return true;
 }
 @Override public boolean performClick(){super.performClick();return true;}
}

package io.github.huades.hanyudictionary.offline;

import android.app.*;import android.os.*;import android.content.*;import android.graphics.*;
import android.graphics.drawable.*;
import android.view.*;import android.view.inputmethod.*;import android.widget.*;
import org.json.*;import java.io.*;import java.util.concurrent.*;

/** Independent seventh-edition reader with PDF numbering and large touch targets. */
public class PdfActivity extends Activity {
 private static final int GREEN=0xff146958;
 private int INK=0xff203a32,SOFT=0xffe5eee6;private boolean dark;
 private final ExecutorService worker=Executors.newSingleThreadExecutor();
 private boolean ready=true;private BookPageView pageView;private TextView status;
 private Button previous,next,pageButton,minus,plus;private LinearLayout root;
 private FrameLayout stage;
 private int page=0,pageCount=1897;private float zoom=1;
 private volatile int request=0;private volatile boolean closed=false;private JSONObject saved=new JSONObject();
 private JSONArray pageFiles;

 @Override public void onCreate(Bundle bundle){
  dark=Appearance.dark(this);if(dark)setTheme(android.R.style.Theme_Material_NoActionBar);super.onCreate(bundle);
  if(dark){INK=0xffe1ece5;SOFT=0xff294338;}
  try{saved=new JSONObject(getSharedPreferences("pdf",0).getString("state","{}"));
   page=ReaderPosition.openPage(saved.optInt("page",0),saved.optInt("startRevision",0),pageCount);
  }catch(Exception ignored){page=0;}
  int target=getIntent().getIntExtra("pdfPage",0);if(target>=1&&target<=pageCount)page=ReaderPosition.jump(target,false,pageCount);
  root=new LinearLayout(this);root.setOrientation(1);setContentView(root);SafeInsets.attach(this,root,true);Appearance.apply(this,root,dark);

  LinearLayout top=row();top.setPadding(dp(8),dp(4),dp(8),dp(4));
  top.addView(button("‹","返回词典",false,()->finish()),new LinearLayout.LayoutParams(dp(52),dp(52)));
  TextView title=new TextView(this);title.setText("原书 · 第7版");title.setTextColor(INK);title.setTextSize(18);title.setSingleLine(true);title.setGravity(Gravity.CENTER);
  top.addView(title,new LinearLayout.LayoutParams(0,dp(52),1));
  top.addView(button("首页","回到原书第一页",false,()->go(0)),new LinearLayout.LayoutParams(dp(64),dp(52)));
  top.addView(button("⋮","原书菜单，目录与书签",false,this::menu),new LinearLayout.LayoutParams(dp(52),dp(52)));
  root.addView(top);
  status=new TextView(this);status.setTextColor(dark?0xffa0b4a7:0xff64776a);status.setTextSize(13);status.setGravity(Gravity.CENTER);
  status.setPadding(dp(12),dp(4),dp(12),dp(8));status.setText("正在读取第7版原书…");root.addView(status);

  stage=new FrameLayout(this);stage.setBackgroundColor(dark?0xff0f1d18:0xffe7ebe5);
  pageView=new BookPageView(this);stage.addView(pageView,new FrameLayout.LayoutParams(-1,-1));
  pageView.setZoomListener(()->{zoom=pageView.getZoom();updateControls();status.setText(description());});
  LinearLayout zoomBar=row();zoomBar.setPadding(dp(4),dp(4),dp(4),dp(4));zoomBar.setBackground(background(dark?0xff1d3229:Color.WHITE,dark?0xff365043:0xffd7e1d5));
  minus=button("−","缩小原书页面",false,()->setZoom(zoom-.5f));plus=button("＋","放大原书页面",false,()->setZoom(zoom+.5f));
  zoomBar.addView(minus,new LinearLayout.LayoutParams(dp(52),dp(52)));zoomBar.addView(plus,new LinearLayout.LayoutParams(dp(52),dp(52)));
  android.widget.FrameLayout.LayoutParams zoomLayout=new android.widget.FrameLayout.LayoutParams(-2,-2,Gravity.BOTTOM|Gravity.END);
  zoomLayout.setMargins(dp(12),dp(12),dp(12),dp(12));stage.addView(zoomBar,zoomLayout);
  root.addView(stage,new LinearLayout.LayoutParams(-1,0,1));

  LinearLayout nav=row();nav.setPadding(dp(12),dp(10),dp(12),dp(10));
  previous=button("上一页","原书上一页",true,()->go(page-1));
  pageButton=button("1 / 1897\n点击跳页","输入原书页码",false,this::jumpDialog);pageButton.setTextSize(14);
  next=button("下一页","原书下一页",true,()->go(page+1));
  nav.addView(previous,new LinearLayout.LayoutParams(0,dp(56),1));
  LinearLayout.LayoutParams center=new LinearLayout.LayoutParams(0,dp(56),1.15f);center.setMargins(dp(8),0,dp(8),0);
  nav.addView(pageButton,center);nav.addView(next,new LinearLayout.LayoutParams(0,dp(56),1));root.addView(nav);updateControls();

  stage.post(()->render(true));
 }

 private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
 private LinearLayout row(){LinearLayout r=new LinearLayout(this);r.setGravity(Gravity.CENTER_VERTICAL);return r;}
 private GradientDrawable background(int fill,int stroke){GradientDrawable d=new GradientDrawable();d.setColor(fill);d.setCornerRadius(dp(12));d.setStroke(dp(1),stroke);return d;}
 private Button button(String label,String description,boolean primary,Runnable action){
  Button b=new Button(this);b.setText(label);b.setContentDescription(description);
  b.setTextSize(label.equals("‹")||label.equals("⋮")?28:label.equals("＋")||label.equals("−")?26:16);b.setAllCaps(false);
  b.setGravity(Gravity.CENTER);b.setIncludeFontPadding(false);b.setPadding(dp(6),dp(2),dp(6),dp(2));
  b.setMinWidth(dp(48));b.setMinimumWidth(dp(48));b.setMinHeight(dp(48));b.setMinimumHeight(dp(48));
  b.setTextColor(new android.content.res.ColorStateList(new int[][]{new int[]{-android.R.attr.state_enabled},new int[]{}},new int[]{0xff89978d,primary?Color.WHITE:dark?0xff85cdb4:GREEN}));
  StateListDrawable states=new StateListDrawable();
  states.addState(new int[]{-android.R.attr.state_enabled},background(dark?0xff24392e:0xffedf0eb,dark?0xff365043:0xffe3e8e0));
  states.addState(new int[]{android.R.attr.state_pressed},background(primary?0xff0b4f42:0xffccdfd2,0xffb8cdbb));
  states.addState(new int[]{},background(primary?GREEN:SOFT,primary?GREEN:0xffd7e1d5));
  b.setBackground(states);b.setOnClickListener(v->action.run());return b;
 }
 private void message(String s){Toast.makeText(this,s,Toast.LENGTH_SHORT).show();}
 private void go(int n){if(!ready||closed||n<0||n>=pageCount)return;page=n;zoom=1;render(true);}
 private void setZoom(float z){pageView.setZoom(z);}
 private void updateControls(){
  boolean available=ready;previous.setEnabled(available&&page>0);next.setEnabled(available&&page<pageCount-1);
  pageButton.setEnabled(available);minus.setEnabled(available&&zoom>1);plus.setEnabled(available&&zoom<4);
  pageButton.setText((page+1)+" / "+pageCount+"\n点击跳页");
  pageButton.setContentDescription("PDF第"+(page+1)+"页，共"+pageCount+"页，点击输入页码");
 }
 private String description(){int body=ReaderPosition.bodyNumber(page);return "原书第 "+(page+1)+" / "+pageCount+" 页"+(body>0?" · 正文第 "+body+" 页":"")+" · "+Math.round(zoom*100)+"%";}
 private void render(boolean resetScroll){
  if(closed)return;updateControls();final int token=++request,selected=page;
  status.setText(description()+" · 读取中");pageView.showMessage("正在读取原书第"+(page+1)+"页…");
  worker.execute(()->{try{
   if(pageFiles==null){try(InputStream input=getAssets().open("book7-pages.json")){pageFiles=new JSONObject(MainActivity.read(input,3000000)).getJSONArray("pages");}if(pageFiles.length()!=pageCount)throw new IOException("原书页面不完整");}
   String asset=pageFiles.getJSONObject(selected).getString("file");
   BitmapFactory.Options options=new BitmapFactory.Options();options.inPreferredConfig=Bitmap.Config.RGB_565;options.inJustDecodeBounds=true;
   try(InputStream input=BookImport.open(this,asset)){BitmapFactory.decodeStream(input,null,options);}
   options.inSampleSize=1;while(options.outWidth/options.inSampleSize>2400||(long)(options.outWidth/options.inSampleSize)*(options.outHeight/options.inSampleSize)>8000000)options.inSampleSize*=2;
   options.inJustDecodeBounds=false;
   Bitmap bitmap;try(InputStream input=BookImport.open(this,asset)){bitmap=BitmapFactory.decodeStream(input,null,options);}
   if(bitmap==null)throw new IOException("页面解码失败");
   runOnUiThread(()->{if(closed||token!=request){bitmap.recycle();return;}pageView.setPage(bitmap);zoom=1;status.setText(description());updateControls();
    try{saved.put("page",page);saved.put("startRevision",ReaderPosition.START_REVISION);getSharedPreferences("pdf",0).edit().putString("state",saved.toString()).apply();}catch(Exception ignored){}
   });
  }catch(Exception|OutOfMemoryError error){runOnUiThread(()->{if(!closed&&token==request){status.setText("页面读取失败，请在菜单中重试："+error.getMessage());pageView.showMessage("页面读取失败，请重试");}});}});
 }

 private void menu(){
  String[] labels={"回到第一页","目录","我的书签","添加当前页书签","输入页码","适合屏幕宽度","重新读取当前页"};
  new AlertDialog.Builder(this).setTitle("原书阅读").setItems(labels,(d,i)->{
   switch(i){case 0:go(0);break;case 1:contents();break;case 2:bookmarks();break;case 3:addBookmark();break;case 4:jumpDialog();break;case 5:setZoom(1);break;case 6:render(true);break;}
  }).show();
 }
 private void jumpDialog(){
  if(!ready)return;
  LinearLayout form=new LinearLayout(this);form.setOrientation(1);form.setPadding(dp(24),dp(8),dp(24),dp(4));
  RadioGroup modes=new RadioGroup(this);
  RadioButton fileMode=new RadioButton(this);fileMode.setId(View.generateViewId());fileMode.setText("PDF页码（1—"+pageCount+"）");fileMode.setTextSize(16);fileMode.setMinHeight(dp(48));
  RadioButton bodyMode=new RadioButton(this);bodyMode.setId(View.generateViewId());bodyMode.setText("正文页码（1—1766）");bodyMode.setTextSize(16);bodyMode.setMinHeight(dp(48));
  modes.addView(fileMode);modes.addView(bodyMode);modes.check(fileMode.getId());form.addView(modes);
  EditText input=new EditText(this);input.setSingleLine();input.setInputType(2);input.setTextSize(22);input.setGravity(Gravity.CENTER);input.setMinHeight(dp(56));input.setSelectAllOnFocus(true);
  input.setImeOptions(EditorInfo.IME_ACTION_GO);input.setText(String.valueOf(page+1));input.setContentDescription("跳转页码");form.addView(input);
  modes.setOnCheckedChangeListener((g,id)->{input.setError(null);input.setText(String.valueOf(id==bodyMode.getId()?Math.max(1,ReaderPosition.bodyNumber(page)):page+1));input.selectAll();});
  AlertDialog dialog=new AlertDialog.Builder(this).setTitle("跳转到指定页").setView(form).setNegativeButton("取消",null).setPositiveButton("跳转",null).create();
  dialog.setOnShowListener(ignored->{
   Runnable jump=()->{try{go(ReaderPosition.jump(Integer.parseInt(input.getText().toString().trim()),bodyMode.isChecked(),pageCount));
     ((InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(input.getWindowToken(),0);dialog.dismiss();
    }catch(Exception e){input.setError(bodyMode.isChecked()?"请输入1—1766之间的正文页码":"请输入1—"+pageCount+"之间的PDF页码");}};
   dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->jump.run());
   dialog.getButton(AlertDialog.BUTTON_POSITIVE).setMinHeight(dp(48));dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setMinHeight(dp(48));
   input.setOnEditorActionListener((v,action,event)->{if(action==EditorInfo.IME_ACTION_GO){jump.run();return true;}return false;});input.requestFocus();input.selectAll();
  });
  dialog.show();dialog.getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);
 }
 private void contents(){
  String[] labels={"原书第一页（PDF第1页）","正文 · A（纸书第1页）","西文字母词语（纸书第1761页）","附录（PDF第1861页）","版权页（PDF第1895页）"};
  int[] pages={0,94,1854,1860,1894};new AlertDialog.Builder(this).setTitle("第7版目录").setItems(labels,(d,i)->go(pages[i])).show();
 }
 private JSONObject marks(){JSONObject m=saved.optJSONObject("bookmarks");if(m==null){m=new JSONObject();try{saved.put("bookmarks",m);}catch(Exception ignored){}}return m;}
 private void addBookmark(){
  if(!ready)return;EditText text=new EditText(this);text.setText("PDF第"+(page+1)+"页");text.setTextSize(18);text.setPadding(dp(20),dp(16),dp(20),dp(16));
  new AlertDialog.Builder(this).setTitle("添加原书书签").setView(text).setNegativeButton("取消",null).setPositiveButton("保存",(d,w)->{
   try{marks().put(String.valueOf(page),text.getText().toString());getSharedPreferences("pdf",0).edit().putString("state",saved.toString()).apply();message("书签已保存");}catch(Exception ignored){}
  }).show();
 }
 private void bookmarks(){
  JSONObject m=marks();JSONArray keys=m.names();if(keys==null){message("还没有书签");return;}
  String[] labels=new String[keys.length()];for(int i=0;i<labels.length;i++)labels[i]=m.optString(keys.optString(i));
  new AlertDialog.Builder(this).setTitle("原书书签").setItems(labels,(d,i)->{try{go(Integer.parseInt(keys.optString(i)));}catch(Exception e){message("这个书签的页码无效");}}).show();
 }
 @Override protected void onDestroy(){closed=true;++request;pageView.release();worker.shutdownNow();super.onDestroy();}
}

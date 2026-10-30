package io.github.huades.hanyudictionary.offline;

import android.app.*;import android.os.*;import android.content.*;import android.database.*;import android.database.sqlite.*;import android.webkit.*;import android.speech.tts.*;import android.view.*;import android.widget.*;import android.net.Uri;
import org.json.*;import java.io.*;import java.util.*;import java.util.concurrent.*;import java.text.Normalizer;import java.security.MessageDigest;

public class MainActivity extends Activity {
 static final String ORIGIN="https://appassets.androidplatform.net/";
 int requestedBookPage=0;
 WebView web; FrameLayout content; SQLiteDatabase dict,dict7,index7,user; TextToSpeech tts; volatile boolean voiceReady=false; ExecutorService worker=Executors.newSingleThreadExecutor(); boolean closed=false,jsReady=false;
 public void onCreate(Bundle state){super.onCreate(state);
  content=new FrameLayout(this);web=new WebView(this);content.addView(web,new FrameLayout.LayoutParams(-1,-1));setContentView(content);
  SafeInsets.attach(this,content,true);applyAppearance(Appearance.dark(this));
  WebSettings s=web.getSettings();s.setJavaScriptEnabled(true);s.setDomStorageEnabled(true);s.setCacheMode(WebSettings.LOAD_NO_CACHE);s.setAllowFileAccess(false);s.setAllowContentAccess(false);s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
  web.setWebViewClient(new WebViewClient(){
   public void onPageFinished(WebView view,String url){if(url.equals(ORIGIN)||url.equals(ORIGIN+"index.html")){jsReady=true;notifySystemTheme();}}
   public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return navigate(r.getUrl().toString());}
   public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){try{
    Uri uri=r.getUrl();if(!"appassets.androidplatform.net".equals(uri.getHost())||!"https".equals(uri.getScheme()))return empty();
    String p=uri.getPath().substring(1);if(p.isEmpty())p="index.html";if(p.contains("..")||p.contains("\\"))return empty();
    String mime=p.endsWith(".js")?"text/javascript":p.endsWith(".css")?"text/css":p.endsWith(".png")?"image/png":p.endsWith(".gif")?"image/gif":p.endsWith(".jpg")?"image/jpeg":p.endsWith(".json")?"application/json":p.endsWith(".txt")?"text/plain":"text/html";
    if(p.endsWith(".db")||p.endsWith(".pdf"))return empty();
    WebResourceResponse res=new WebResourceResponse(mime,"UTF-8",getAssets().open(p));Map<String,String> headers=new HashMap<>();headers.put("Cache-Control","no-store");headers.put("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-src 'none'; base-uri 'none'");res.setResponseHeaders(headers);return res;
   }catch(Exception e){return empty();}}
  });
  web.addJavascriptInterface(new Bridge(),"DictionaryNative");web.loadUrl(ORIGIN);
  tts=new TextToSpeech(this,status->{if(status==TextToSpeech.SUCCESS){try{for(Voice v:tts.getVoices())if(v.getLocale().getLanguage().equals("zh")&&!v.isNetworkConnectionRequired()){tts.setVoice(v);voiceReady=true;break;}}catch(Exception ignored){}}});
 }
 boolean navigate(String url){
  if(url.startsWith(ORIGIN))return false;
  if(url.equals("https://github.com/huades/mcdict")){try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(url)));}catch(ActivityNotFoundException e){toast("未找到可打开链接的浏览器");}}return true;
 }
 void applyAppearance(boolean dark){Appearance.apply(this,content,dark);web.setBackgroundColor(dark?0xff14251f:0xfff7f8f4);}
 void notifySystemTheme(){if(closed||web==null)return;applyAppearance(Appearance.dark(this));if(jsReady)web.evaluateJavascript("window.dispatchEvent(new CustomEvent('systemtheme',{detail:{dark:"+Appearance.systemDark(this)+"}}))",null);}
 @Override public void onConfigurationChanged(android.content.res.Configuration configuration){super.onConfigurationChanged(configuration);notifySystemTheme();}
 @Override protected void onResume(){super.onResume();notifySystemTheme();}
 WebResourceResponse empty(){return new WebResourceResponse("text/plain","UTF-8",new ByteArrayInputStream(new byte[0]));}
 static void copyAsset(Context context,String name,File target)throws Exception{
  File temp=new File(target.getPath()+".tmp");try(InputStream in=context.getAssets().open(name);OutputStream out=new FileOutputStream(temp)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}
  if(!temp.renameTo(target)){temp.delete();throw new IOException("文件准备失败，请重试");}
 }
 void init()throws Exception{
  if(dict==null){File f=new File(getFilesDir(),"dictionary-v1.db");if(!f.exists())copyAsset(this,"dictionary.db",f);dict=SQLiteDatabase.openDatabase(f.getPath(),null,SQLiteDatabase.OPEN_READONLY);}
  if(dict7==null){JSONObject manifest=new JSONObject(readAsset("manifest7.json"));File f=VerifiedDatabase.install(getFilesDir(),manifest.getString("databaseSha256"),manifest.getLong("databaseBytes"),()->getAssets().open("dictionary7.db"));dict7=SQLiteDatabase.openDatabase(f.getPath(),null,SQLiteDatabase.OPEN_READONLY);try(Cursor c=dict7.rawQuery("SELECT count(*) FROM entries",null)){if(!c.moveToFirst()||c.getInt(0)!=70113)throw new IOException("第7版词库记录数异常");}}
  if(index7==null){JSONObject manifest=new JSONObject(readAsset("index7-manifest.json"));File f=VerifiedDatabase.install(new File(getFilesDir(),"index7-verified"),manifest.getString("database_sha256"),manifest.getLong("databaseBytes"),()->getAssets().open("index7.db"));index7=SQLiteDatabase.openDatabase(f.getPath(),null,SQLiteDatabase.OPEN_READONLY);}
  if(user==null){user=SQLiteDatabase.openOrCreateDatabase(new File(getFilesDir(),"user.db"),null);user.execSQL("CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value TEXT)");}
 }
 String state(){try(Cursor c=user.rawQuery("SELECT value FROM state WHERE key='user'",null)){return c.moveToFirst()?c.getString(0):"{}";}}
 void saveState(String json)throws Exception{JSONObject value=new JSONObject(json);if(json.length()>10000000)throw new Exception("备份数据过大");user.execSQL("INSERT OR REPLACE INTO state VALUES('user',?)",new Object[]{value.toString()});}
 JSONObject row(Cursor c,boolean detail)throws Exception{JSONObject o=new JSONObject();String[] names=c.getColumnNames();for(int i=0;i<names.length;i++){if(c.isNull(i))o.put(names[i],JSONObject.NULL);else if(c.getType(i)==Cursor.FIELD_TYPE_INTEGER)o.put(names[i],c.getLong(i));else o.put(names[i],c.getString(i));}return o;}
 JSONArray query(String sql,String[] args)throws Exception{return query(dict7,sql,args);}
 JSONArray query(SQLiteDatabase database,String sql,String[] args)throws Exception{JSONArray a=new JSONArray();try(Cursor c=database.rawQuery(sql,args)){while(c.moveToNext())a.put(row(c,false));}return a;}
 JSONArray indexQuery(String sql,String[] args)throws Exception{JSONArray a=new JSONArray();try(Cursor c=index7.rawQuery(sql,args)){while(c.moveToNext())a.put(row(c,false));}return a;}
 static String key(String s){s=s.toLowerCase(Locale.ROOT).replace("u:","ü").replace('v','ü');StringBuilder b=new StringBuilder();for(int i=0;i<s.length();i++){char c=s.charAt(i);if("üǖǘǚǜ".indexOf(c)>=0)b.append('v');else{String n=Normalizer.normalize(String.valueOf(c),Normalizer.Form.NFD);for(char x:n.toCharArray())if(x>='a'&&x<='z')b.append(x);}}return b.toString();}
 static String like(String s){return s.replace("\\","\\\\").replace("%","\\%").replace("_","\\_");}
 static String fts(String s){StringBuilder b=new StringBuilder();String latin="";for(int cp:s.toLowerCase(Locale.ROOT).codePoints().toArray()){if(cp<128&&Character.isLetterOrDigit(cp))latin+=(char)cp;else{if(!latin.isEmpty()){b.append('"').append(latin).append("\" ");latin="";}if(cp>127&&!Character.isWhitespace(cp))b.append('"').appendCodePoint(cp).append("\" ");}}if(!latin.isEmpty())b.append('"').append(latin).append('"');return b.toString().trim();}
 JSONObject dispatch(String action,JSONObject p)throws Exception{
  if(action.equals("repository")){runOnUiThread(()->navigate("https://github.com/huades/mcdict"));return new JSONObject();}
  if(action.equals("appearance")){String theme=p.optString("theme","auto");if(!theme.equals("dark")&&!theme.equals("light"))theme="auto";getSharedPreferences("appearance",0).edit().putString("theme",theme).apply();boolean dark=Appearance.dark(this);runOnUiThread(()->{if(!closed)applyAppearance(dark);});return new JSONObject();}
  init();JSONObject out=new JSONObject();
  if(action.equals("init")){out.put("user",new JSONObject(state()));out.put("systemDark",Appearance.systemDark(this));out.put("manifest",new JSONObject(readAsset("manifest7.json")));return out;}
  if(action.equals("saveUser")){saveState(p.getJSONObject("user").toString());return out;}
  if(action.equals("detail")){JSONArray a=query(p.getString("id").startsWith("xdhy5:")?dict:dict7,"SELECT * FROM entries WHERE id=?",new String[]{p.getString("id")});if(a.length()==0)throw new Exception("未找到词条");return a.getJSONObject(0);}
  if(action.equals("search")){
   String q=Normalizer.normalize(p.optString("query").trim(),Normalizer.Form.NFC).toLowerCase(Locale.ROOT);if(q.length()>120)throw new Exception("请输入120字以内的内容");
   SQLiteDatabase active=p.optInt("edition",7)==5?dict:dict7;
   if(active==dict7){try(Cursor alias=active.rawQuery("SELECT target FROM aliases WHERE alias=? COLLATE NOCASE LIMIT 1",new String[]{q})){if(alias.moveToFirst())q=alias.getString(0);}}
   int offset=Math.max(0,p.optInt("offset"));String mode=p.optString("mode","auto"), cols="SELECT id,head,head_html,pinyin,substr(body_text,1,65) AS summary,unknown_glyph FROM entries ";JSONArray a;
   if(q.isEmpty())a=new JSONArray();
   else if(mode.equals("full")){String t=fts(q);a=t.isEmpty()?new JSONArray():query(active,cols+"WHERE rowid IN(SELECT rowid FROM fulltext WHERE fulltext MATCH ?) AND instr(lower(body_text),?)>0 ORDER BY ordinal LIMIT 51 OFFSET ?",new String[]{t,q,String.valueOf(offset)});}
   else if(q.matches("[a-zA-Züǖǘǚǜāáǎàēéěèīíǐìōóǒòūúǔùńňǹḿ '’·∥:0-9-]+")){
    String k=key(q);a=query(active,cols+"WHERE head=? COLLATE NOCASE OR pinyin_key LIKE ? ESCAPE '\\' OR ('|'||initials||'|') LIKE ? ESCAPE '\\' ORDER BY CASE WHEN head=? COLLATE NOCASE THEN -1 WHEN pinyin_key=? THEN 0 WHEN pinyin_key LIKE ? ESCAPE '\\' THEN 1 ELSE 2 END,ordinal LIMIT 51 OFFSET ?",new String[]{q,like(k)+"%","%|"+like(k)+"|%",q,k,like(k)+"%",String.valueOf(offset)});
   }else a=query(active,cols+"WHERE head LIKE ? ESCAPE '\\' ORDER BY CASE WHEN head=? THEN 0 WHEN head LIKE ? ESCAPE '\\' THEN 1 ELSE 2 END,ordinal LIMIT 51 OFFSET ?",new String[]{"%"+like(q)+"%",q,like(q)+"%",String.valueOf(offset)});
   boolean more=a.length()>50;if(more)a.remove(50);out.put("items",a);out.put("more",more);return out;
  }
  if(action.equals("radicals")){out.put("items",indexQuery("SELECT * FROM forms ORDER BY ordinal",null));return out;}
  if(action.equals("glyphs")){
   String r=p.getString("radical"),group=p.optString("group","all");JSONArray forms=indexQuery("SELECT section FROM forms WHERE id=?",new String[]{r});if(forms.length()==0)throw new Exception("请先选择第7版部首");String section=forms.getJSONObject(0).getString("section");
   boolean textMode=p.optString("mode","book").equals("text");String base=" WHERE section=?"+(textMode?" AND id IN(SELECT glyph_id FROM entry_links)":"");String where=base;List<String> args=new ArrayList<>();args.add(section);
   out.put("groups",indexQuery("SELECT residual_min,residual_max,"+(textMode?"count(distinct character)":"count(*)")+" AS count FROM glyphs"+base+" GROUP BY residual_min,residual_max ORDER BY residual_min",new String[]{section}));
   if(group.equals("none"))where+=" AND residual_min IS NULL";else if(!group.equals("all")){String[] range=group.split(":");if(range.length!=2)throw new Exception("笔画分组无效");where+=" AND residual_min=? AND residual_max=?";args.add(String.valueOf(Integer.parseInt(range[0])));args.add(String.valueOf(Integer.parseInt(range[1])));}
   out.put("total",indexQuery("SELECT "+(textMode?"count(distinct character)":"count(*)")+" AS count FROM glyphs"+where,args.toArray(new String[0])).getJSONObject(0).getInt("count"));
   args.add(String.valueOf(Math.max(0,p.optInt("offset"))));String columns=textMode?"SELECT *,min(ordinal) AS first_ordinal,group_concat(distinct body_page) AS body_pages,(SELECT group_concat(distinct pinyin) FROM entry_links WHERE glyph_id=glyphs.id) AS readings FROM glyphs":"SELECT * FROM glyphs";JSONArray a=indexQuery(columns+where+(textMode?" GROUP BY character":"")+" ORDER BY ordinal LIMIT 61 OFFSET ?",args.toArray(new String[0]));boolean more=a.length()>60;if(more)a.remove(60);out.put("items",a);out.put("more",more);return out;
  }
  if(action.equals("sameCharacter")){
   if(p.optInt("edition",7)!=5){JSONArray refs=indexQuery("SELECT DISTINCT entry_id FROM entry_links WHERE glyph_id=?",new String[]{p.getString("id")});List<String> ids=new ArrayList<>();for(int i=0;i<refs.length();i++)ids.add(refs.getJSONObject(i).getString("entry_id"));String marks=String.join(",",Collections.nCopies(ids.size(),"?"));out.put("items",ids.isEmpty()?new JSONArray():query("SELECT id,head,head_html,pinyin FROM entries WHERE id IN("+marks+") ORDER BY ordinal",ids.toArray(new String[0])));}
   else{JSONArray refs=indexQuery("SELECT character FROM glyphs WHERE id=? AND character IS NOT NULL",new String[]{p.getString("id")});out.put("items",refs.length()==0?new JSONArray():query(dict,"SELECT id,head,head_html,pinyin FROM entries WHERE head=? ORDER BY ordinal",new String[]{refs.getJSONObject(0).getString("character")}));}return out;
  }
  if(action.equals("speak")){if(!voiceReady)throw new Exception("设备尚无可用的中文离线语音。请在系统的文字转语音设置中安装中文声音。");String text=p.optString("text");runOnUiThread(()->tts.speak(text,TextToSpeech.QUEUE_FLUSH,null,"dictionary"));return out;}
  if(action.equals("pdf")){int target=p.optInt("page",0);if(target<0||target>1897)throw new Exception("原书页码无效");requestedBookPage=target;runOnUiThread(()->{if(BookImport.ready(this))openBook();else new AlertDialog.Builder(this).setTitle("导入第7版原书").setMessage("查词无需导入。若需阅读扫描原书，请选择配套的「第7版原书离线包.zip」，导入后可完全离线阅读。").setNegativeButton("稍后",null).setPositiveButton("选择离线包",(d,w)->{Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);intent.setType("*/*");intent.addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(intent,43);}).show();});return out;}
  if(action.equals("export")){runOnUiThread(()->{Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.setType("application/json");i.addCategory(Intent.CATEGORY_OPENABLE);i.putExtra(Intent.EXTRA_TITLE,"现代汉语词典-备份.json");startActivityForResult(i,41);});return out;}
  if(action.equals("import")){runOnUiThread(()->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.setType("*/*");i.addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(i,42);});return out;}
  throw new Exception("不支持的操作");
 }
 String readAsset(String p)throws Exception{try(InputStream in=getAssets().open(p)){return read(in,20000000);}}
 void openBook(){Intent intent=new Intent(this,PdfActivity.class);if(requestedBookPage>0)intent.putExtra("pdfPage",requestedBookPage);startActivity(intent);}
 static String read(InputStream in,int limit)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1){if(out.size()+n>limit)throw new IOException("文件过大");out.write(b,0,n);}return out.toString("UTF-8");}
 class Bridge {@JavascriptInterface public void request(String id,String action,String payload){worker.execute(()->{try{reply(id,dispatch(action,new JSONObject(payload)),null);}catch(Exception e){reply(id,null,e.getMessage());}});}}
 void reply(String id,JSONObject result,String error){if(closed)return;runOnUiThread(()->{if(!closed)web.evaluateJavascript("window.nativeReply("+JSONObject.quote(id)+","+(result==null?"null":result.toString())+","+(error==null?"null":JSONObject.quote(error))+")",null);});}
 void toast(String s){runOnUiThread(()->Toast.makeText(this,s,Toast.LENGTH_LONG).show());}
 protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(result!=RESULT_OK||data==null)return;if(request==43){BookImport.importPackage(this,data.getData(),worker,this::openBook);return;}worker.execute(()->{try{
  if(request==41){JSONObject backup=new JSONObject();backup.put("format","xdhy-user");backup.put("version",1);backup.put("user",new JSONObject(state()));backup.put("pdf",getSharedPreferences("pdf",0).getString("state","{}"));try(OutputStream out=getContentResolver().openOutputStream(data.getData(),"wt")){out.write(backup.toString(2).getBytes("UTF-8"));}toast("备份已保存");}
  if(request==42){String text;try(InputStream in=getContentResolver().openInputStream(data.getData())){text=read(in,10000000);}JSONObject backup=new JSONObject(text);if(!backup.optString("format").equals("xdhy-user")||backup.optInt("version")!=1)throw new Exception("不支持的备份格式");JSONObject imported=backup.getJSONObject("user");validateUser(imported);String pdf=backup.optString("pdf","{}");new JSONObject(pdf);
   runOnUiThread(()->new AlertDialog.Builder(this).setTitle("恢复个人记录？").setMessage("将用备份替换本机收藏、历史、设置和复习记录。词典内容不受影响。").setNegativeButton("取消",null).setPositiveButton("恢复",(d,w)->worker.execute(()->{try{saveState(imported.toString());getSharedPreferences("pdf",0).edit().putString("state",pdf).apply();runOnUiThread(()->web.reload());toast("恢复完成");}catch(Exception e){toast("恢复失败："+e.getMessage());}})).show());}
 }catch(Exception e){toast("操作失败："+e.getMessage());}});}
 static void validateUser(JSONObject u)throws Exception{if(u.has("favorites")&&!(u.get("favorites") instanceof JSONObject))throw new Exception("收藏结构不正确");if(u.has("history")&&!(u.get("history") instanceof JSONArray))throw new Exception("历史结构不正确");if(u.has("settings")&&!(u.get("settings") instanceof JSONObject))throw new Exception("设置结构不正确");if(u.has("favorites")){JSONObject f=u.getJSONObject("favorites");Iterator<String> keys=f.keys();while(keys.hasNext()){String k=keys.next();if((!k.startsWith("xdhy5:")&&!k.startsWith("xdhy7:"))||!(f.get(k) instanceof JSONObject))throw new Exception("收藏词条无效");}}}
 public void onBackPressed(){web.evaluateJavascript("window.appBack?window.appBack():false",value->{if("false".equals(value))finish();});}
 protected void onDestroy(){closed=true;if(tts!=null){tts.stop();tts.shutdown();}worker.execute(()->{if(dict!=null)dict.close();if(index7!=null)index7.close();if(dict7!=null)dict7.close();if(user!=null)user.close();});worker.shutdown();web.destroy();super.onDestroy();}
}

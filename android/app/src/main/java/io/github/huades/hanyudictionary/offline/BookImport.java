package io.github.huades.hanyudictionary.offline;
import android.app.*;import android.content.*;import android.net.Uri;import org.json.*;
import java.io.*;import java.security.MessageDigest;import java.util.*;import java.util.concurrent.Executor;import java.util.zip.*;

/** Import only exact page names and hashes from the manifest shipped in this APK. */
final class BookImport {
 static File root(Context c){return new File(c.getFilesDir(),"book7-offline");}
 static boolean ready(Context c){return new File(root(c),".ready").isFile();}
 static InputStream open(Context c,String asset)throws IOException{
  File base=root(c),file=new File(base,asset);if(!file.getCanonicalPath().startsWith(base.getCanonicalPath()+File.separator))throw new IOException("页面路径无效");
  return file.isFile()?new FileInputStream(file):c.getAssets().open(asset);
 }
 static void importPackage(Activity activity,Uri uri,Executor worker,Runnable done){
  ProgressDialog dialog=new ProgressDialog(activity);dialog.setTitle("导入原书离线包");dialog.setMessage("正在核验页面…");dialog.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL);dialog.setMax(1897);dialog.setCancelable(false);dialog.show();
  worker.execute(()->{try{
   JSONObject manifest;try(InputStream in=activity.getAssets().open("book7-pages.json")){manifest=new JSONObject(MainActivity.read(in,3000000));}
   JSONArray pages=manifest.getJSONArray("pages");Map<String,JSONObject> expected=new HashMap<>();for(int i=0;i<pages.length();i++){JSONObject p=pages.getJSONObject(i);expected.put(p.getString("file"),p);}Set<String> seen=new HashSet<>();
   File base=root(activity);if(!base.isDirectory()&&!base.mkdirs())throw new IOException("无法创建原书目录");
   try(InputStream stream=activity.getContentResolver().openInputStream(uri);ZipInputStream zip=new ZipInputStream(stream)){
    ZipEntry entry;byte[] buffer=new byte[65536];while((entry=zip.getNextEntry())!=null){String name=entry.getName();JSONObject spec=expected.get(name);if(entry.isDirectory()||spec==null||!seen.add(name))throw new IOException("离线包包含未知或重复文件");
     File file=new File(base,name);if(!file.getCanonicalPath().startsWith(base.getCanonicalPath()+File.separator))throw new IOException("页面路径无效");File parent=file.getParentFile();if(!parent.isDirectory()&&!parent.mkdirs())throw new IOException("无法创建页面目录");File temp=new File(file.getPath()+".tmp");MessageDigest digest=MessageDigest.getInstance("SHA-256");long size=0,limit=spec.getLong("bytes");
     try(OutputStream out=new FileOutputStream(temp)){int n;while((n=zip.read(buffer))!=-1){size+=n;if(size>limit)throw new IOException("页面大小异常");digest.update(buffer,0,n);out.write(buffer,0,n);}}
     StringBuilder hex=new StringBuilder();for(byte b:digest.digest())hex.append(String.format(Locale.ROOT,"%02x",b&255));if(size!=limit||!hex.toString().equals(spec.getString("sha256"))){temp.delete();throw new IOException("页面校验失败，请选择配套离线包");}
     if(!temp.renameTo(file))throw new IOException("无法保存原书页面");final int progress=seen.size();activity.runOnUiThread(()->{if(!activity.isFinishing())dialog.setProgress(progress);});zip.closeEntry();
    }
   }
   if(seen.size()!=1897)throw new IOException("原书页数不足，需要1897页");try(OutputStream marker=new FileOutputStream(new File(base,".ready"))){marker.write(manifest.getString("source_pdf_sha256").getBytes("UTF-8"));}
   activity.runOnUiThread(()->{if(!activity.isFinishing()){dialog.dismiss();done.run();}});
  }catch(Exception e){activity.runOnUiThread(()->{if(!activity.isFinishing()){dialog.dismiss();new AlertDialog.Builder(activity).setTitle("原书导入失败").setMessage(e.getMessage()).setPositiveButton("知道了",null).show();}});}});
 }
}

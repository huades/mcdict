package io.github.huades.hanyudictionary.offline;
import java.io.*;import java.nio.file.*;import java.security.MessageDigest;import java.util.Locale;

/** A changed asset always gets a new private filename; user.db is never touched. */
public final class VerifiedDatabase {
 public interface Source {InputStream open()throws IOException;}
 private VerifiedDatabase(){}
 public static String sha256(File file)throws Exception{MessageDigest d=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(file)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)d.update(b,0,n);}return hex(d.digest());}
 private static String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte x:b)s.append(String.format(Locale.ROOT,"%02x",x&255));return s.toString();}
 public static File install(File directory,String expected,long bytes,Source source)throws Exception{
  if(!expected.matches("[0-9a-f]{64}")||bytes<1)throw new IOException("词库清单无效");
  if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("无法准备词库目录");
  File target=new File(directory,"dictionary7-"+expected+".db");
  if(target.isFile()&&target.length()==bytes&&sha256(target).equals(expected))return target;
  File temp=new File(directory,target.getName()+".tmp");MessageDigest digest=MessageDigest.getInstance("SHA-256");long size=0;
  try{
   try(InputStream in=source.open();OutputStream out=new FileOutputStream(temp)){byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))!=-1){size+=n;if(size>bytes)throw new IOException("词库文件大小异常");digest.update(buffer,0,n);out.write(buffer,0,n);}}
   if(size!=bytes||!hex(digest.digest()).equals(expected))throw new IOException("词库校验失败，请重新安装完整APK");
   try{Files.move(temp.toPath(),target.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}catch(AtomicMoveNotSupportedException e){Files.move(temp.toPath(),target.toPath(),StandardCopyOption.REPLACE_EXISTING);}
   return target;
  }finally{if(temp.exists())temp.delete();}
 }
}

import io.github.huades.hanyudictionary.offline.VerifiedDatabase;
import java.io.*;import java.nio.file.*;import java.security.*;import java.util.*;
public class VerifiedDatabaseTest {
 static String hash(byte[] b)throws Exception{StringBuilder s=new StringBuilder();for(byte v:MessageDigest.getInstance("SHA-256").digest(b))s.append(String.format(Locale.ROOT,"%02x",v&255));return s.toString();}
 static void check(boolean v,String label){if(!v)throw new AssertionError(label);}
 public static void main(String[] args)throws Exception{
  Path root=Files.createTempDirectory(Paths.get(args[0]),"verified-db-");byte[] old="old-db".getBytes("UTF-8"),fresh="new-db".getBytes("UTF-8");
  Path user=root.resolve("user.db");Files.write(user,"favorites".getBytes("UTF-8"));
  File first=VerifiedDatabase.install(root.toFile(),hash(old),old.length,()->new ByteArrayInputStream(old));
  File second=VerifiedDatabase.install(root.toFile(),hash(fresh),fresh.length,()->new ByteArrayInputStream(fresh));
  check(!first.equals(second),"Changed packaged DB cannot reuse old private filename");check(Arrays.equals(Files.readAllBytes(second.toPath()),fresh),"New asset is installed");
  check(VerifiedDatabase.install(root.toFile(),hash(fresh),fresh.length,()->{throw new IOException("must reuse valid cache");}).equals(second),"Valid fingerprint cache reused");
  Files.write(second.toPath(),old);VerifiedDatabase.install(root.toFile(),hash(fresh),fresh.length,()->new ByteArrayInputStream(fresh));check(Arrays.equals(Files.readAllBytes(second.toPath()),fresh),"Corrupt cache repaired");
  try{VerifiedDatabase.install(root.toFile(),hash("different".getBytes("UTF-8")),fresh.length,()->new ByteArrayInputStream(old));throw new AssertionError("Invalid asset accepted");}catch(IOException expected){}
  check(first.isFile()&&second.isFile(),"Failed upgrade preserves valid files");check(new String(Files.readAllBytes(user),"UTF-8").equals("favorites"),"Favorites untouched");
  System.out.println("PASS: database upgrade, cache validation, repair, failure rollback and user-data preservation");
 }
}

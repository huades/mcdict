import io.github.huades.hanyudictionary.offline.ReaderPosition;

/** Runs against the production page arithmetic without Android/emulator stubs. */
public class ReaderPositionTest {
 private static int checks;
 private static void eq(int expected,int actual,String scenario){checks++;if(expected!=actual)throw new AssertionError(scenario+": expected "+expected+", got "+actual);}
 private static void invalid(int number,boolean body){checks++;try{ReaderPosition.jump(number,body,1897);throw new AssertionError("Out-of-range page accepted: "+number);}catch(IllegalArgumentException expected){}}
 public static void main(String[] args){
  eq(0,ReaderPosition.openPage(94,0,1897),"Upgrade old default at PDF95 to PDF1");
  eq(0,ReaderPosition.openPage(300,0,1897),"First opening after upgrade begins at PDF1");
  eq(0,ReaderPosition.openPage(0,0,1897),"Fresh installation begins at PDF1");
  eq(300,ReaderPosition.openPage(300,2,1897),"Subsequent opening resumes saved position");
  eq(0,ReaderPosition.openPage(-2,2,1897),"Negative restored position clamped");
  eq(1896,ReaderPosition.openPage(9000,2,1897),"Oversized restored position clamped");
  eq(0,ReaderPosition.jump(1,false,1897),"PDF1 is the actual first file page");
  eq(1896,ReaderPosition.jump(1897,false,1897),"Last PDF page");
  eq(94,ReaderPosition.jump(1,true,1897),"Body1 is PDF95");
  eq(1859,ReaderPosition.jump(1766,true,1897),"Last body page is PDF1860");
  eq(0,ReaderPosition.bodyNumber(0),"Front matter has no body number");
  eq(1,ReaderPosition.bodyNumber(94),"Body page label");
  eq(1766,ReaderPosition.bodyNumber(1859),"Last body label");
  eq(0,ReaderPosition.bodyNumber(1860),"Appendix is not body page1767");
  invalid(0,false);invalid(-1,false);invalid(1898,false);invalid(0,true);invalid(1767,true);
  System.out.println("PASS: "+checks+" reader pagination and upgrade checks");
 }
}

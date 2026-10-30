package io.github.huades.hanyudictionary.offline;

/** Page arithmetic shared by the reader and executable regression checks. */
public final class ReaderPosition {
 public static final int START_REVISION=2, BODY_OFFSET=94, BODY_PAGES=1766;
 private ReaderPosition() {}
 public static int openPage(int saved,int revision,int count){
  if(count<1||revision<START_REVISION)return 0;
  return Math.max(0,Math.min(count-1,saved));
 }
 public static int jump(int number,boolean body,int count){
  int maximum=body?Math.min(BODY_PAGES,Math.max(0,count-BODY_OFFSET)):count;
  if(number<1||number>maximum)throw new IllegalArgumentException("页码超出范围");
  return number-1+(body?BODY_OFFSET:0);
 }
 public static int bodyNumber(int page){return page>=BODY_OFFSET&&page<BODY_OFFSET+BODY_PAGES?page-BODY_OFFSET+1:0;}
}

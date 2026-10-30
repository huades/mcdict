package io.github.huades.hanyudictionary.offline;
public final class InsetsGeometry {
 private InsetsGeometry(){}
 public static int[] merge(int[] bars,int[] cutout,int imeBottom,boolean keyboard){
  int[] result=new int[4];for(int i=0;i<4;i++)result[i]=Math.max(0,Math.max(bars[i],cutout[i]));
  if(keyboard)result[3]=Math.max(result[3],imeBottom);return result;
 }
}

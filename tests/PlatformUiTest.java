import io.github.huades.hanyudictionary.offline.ThemePolicy;
import io.github.huades.hanyudictionary.offline.InsetsGeometry;
import java.util.Arrays;
public class PlatformUiTest {
 private static int checks;
 private static void theme(String mode,boolean system,boolean expected){checks++;if(ThemePolicy.isDark(mode,system)!=expected)throw new AssertionError(mode+"/"+system);}
 private static void insets(int[] bars,int[] cutout,int ime,boolean keyboard,int[] expected){checks++;if(!Arrays.equals(expected,InsetsGeometry.merge(bars,cutout,ime,keyboard)))throw new AssertionError("Insets mismatch");}
 public static void main(String[] args){
  theme("auto",true,true);theme("auto",false,false);theme("light",true,false);theme("dark",false,true);theme(null,true,true);
  insets(new int[]{0,24,0,24},new int[]{0,0,0,0},0,true,new int[]{0,24,0,24});
  insets(new int[]{0,24,0,24},new int[]{0,44,0,0},0,true,new int[]{0,44,0,24});
  insets(new int[]{0,0,0,24},new int[]{44,0,0,0},0,true,new int[]{44,0,0,24});
  insets(new int[]{0,24,0,24},new int[]{0,0,0,0},300,true,new int[]{0,24,0,300});
  insets(new int[]{0,24,0,24},new int[]{0,0,0,0},300,false,new int[]{0,24,0,24});
  insets(new int[]{0,0,0,0},new int[]{0,0,0,0},0,true,new int[]{0,0,0,0});
  System.out.println("PASS: "+checks+" native theme and status/cutout/keyboard inset checks");
 }
}

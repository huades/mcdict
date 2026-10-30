package io.github.huades.hanyudictionary.offline;
import android.app.Activity;import android.os.Build;import android.view.*;import android.graphics.Insets;

/** Apply window insets to a layout container, never to WebView's ignored padding. */
public final class SafeInsets {
 private SafeInsets(){}
 public static void attach(Activity activity,View container,boolean keyboard){
  Window window=activity.getWindow();
  if(Build.VERSION.SDK_INT>=30)window.setDecorFitsSystemWindows(false);
  else window.getDecorView().setSystemUiVisibility(window.getDecorView().getSystemUiVisibility()|View.SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
  container.setOnApplyWindowInsetsListener((view,source)->{
   int[] bars,cutout={0,0,0,0};int ime=0;
   if(Build.VERSION.SDK_INT>=30){
    Insets b=source.getInsets(WindowInsets.Type.systemBars());Insets c=source.getInsets(WindowInsets.Type.displayCutout());
    bars=new int[]{b.left,b.top,b.right,b.bottom};cutout=new int[]{c.left,c.top,c.right,c.bottom};
    if(keyboard)ime=source.getInsets(WindowInsets.Type.ime()).bottom;
   }else{
    bars=new int[]{source.getSystemWindowInsetLeft(),source.getSystemWindowInsetTop(),source.getSystemWindowInsetRight(),source.getSystemWindowInsetBottom()};
    if(Build.VERSION.SDK_INT>=28&&source.getDisplayCutout()!=null){DisplayCutout c=source.getDisplayCutout();cutout=new int[]{c.getSafeInsetLeft(),c.getSafeInsetTop(),c.getSafeInsetRight(),c.getSafeInsetBottom()};}
   }
   int[] padding=InsetsGeometry.merge(bars,cutout,ime,keyboard);view.setPadding(padding[0],padding[1],padding[2],padding[3]);
   if(Build.VERSION.SDK_INT>=30)return WindowInsets.CONSUMED;
   return source.consumeSystemWindowInsets();
  });
  container.post(container::requestApplyInsets);
 }
}

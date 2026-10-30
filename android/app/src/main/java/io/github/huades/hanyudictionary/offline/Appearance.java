package io.github.huades.hanyudictionary.offline;
import android.app.Activity;import android.content.Context;import android.content.res.Configuration;import android.os.Build;import android.view.*;

public final class Appearance {
 private Appearance(){}
 public static boolean systemDark(Context c){return (c.getResources().getConfiguration().uiMode&Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES;}
 public static boolean dark(Context c){return ThemePolicy.isDark(c.getSharedPreferences("appearance",0).getString("theme","auto"),systemDark(c));}
 public static void apply(Activity activity,View root,boolean dark){
  int color=dark?0xff14251f:0xfff7f8f4;root.setBackgroundColor(color);Window w=activity.getWindow();
  w.setStatusBarColor(color);w.setNavigationBarColor(color);
  int flags=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
  View decor=w.getDecorView();int existing=decor.getSystemUiVisibility();decor.setSystemUiVisibility(dark?existing&~flags:existing|flags);
  if(Build.VERSION.SDK_INT>=30&&w.getInsetsController()!=null){int mask=WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS|WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;w.getInsetsController().setSystemBarsAppearance(dark?0:mask,mask);}
 }
}

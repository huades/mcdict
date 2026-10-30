package io.github.huades.hanyudictionary.offline;
public final class ThemePolicy {
 private ThemePolicy(){}
 public static boolean isDark(String mode,boolean systemDark){return "dark".equals(mode)||(!"light".equals(mode)&&systemDark);}
}

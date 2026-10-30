// All radical forms and stroke groups come directly from the seventh-edition DB.
export function residualLabel(min,max){
 if(min==null)return '原表未单列部外笔画';
 if(max===99)return min+'画以上';
 return min===max?min+'画':min+'至'+max+'画';
}
export function residualKey(min,max){return min==null?'none':min+':'+max;}
export function themeIsDark(theme,nativeDark,mediaDark){
  if(theme==='dark')return true;
  if(theme==='light')return false;
  return typeof nativeDark==='boolean'?nativeDark:!!mediaDark;
}

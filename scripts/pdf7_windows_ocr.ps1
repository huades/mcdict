param([int]$First=33,[int]$Last=91)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime] | Out-Null
$taskMethod=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {$_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'} | Select-Object -First 1
function AwaitResult($Operation,$Type){
 $task=$taskMethod.MakeGenericMethod($Type).Invoke($null,@($Operation));try{$task.Wait()}catch{throw $task.Exception.GetBaseException()};return $task.Result
}
$qa=Join-Path (Split-Path $PSScriptRoot -Parent) 'source-index7\qa'
$engine=[Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('zh-Hans-CN'))
if($null -eq $engine){throw 'Chinese Windows OCR engine unavailable'}
for($n=$First;$n -le $Last;$n++){
 $stem='page-{0:D4}' -f $n
 $output=Join-Path $qa ($stem+'-windows.json')
 if(Test-Path -LiteralPath $output){continue}
 $file=AwaitResult ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Join-Path $qa ($stem+'.png')))) ([Windows.Storage.StorageFile])
 $stream=AwaitResult ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
 $decoder=AwaitResult ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
 $bitmap=AwaitResult ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
 $result=AwaitResult ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
 $lines=@($result.Lines | ForEach-Object {$line=$_;@{text=$line.Text;words=@($line.Words | ForEach-Object {@{t=$_.Text;x=$_.BoundingRect.X;y=$_.BoundingRect.Y;w=$_.BoundingRect.Width;h=$_.BoundingRect.Height}})}})
 @{page=$n;engine='Windows.Media.Ocr zh-Hans-CN';lines=$lines} | ConvertTo-Json -Depth 7 -Compress | Set-Content -LiteralPath $output -Encoding UTF8
 $bitmap.Dispose();$stream.Dispose()
 Write-Output ('OCR PDF '+$n+'; lines '+$lines.Count)
}

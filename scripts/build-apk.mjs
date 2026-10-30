import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {randomBytes,createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const argument=name=>{const i=process.argv.indexOf(name);return i<0?null:process.argv[i+1];};
const javaHome=argument('--java-home')||process.env.DICT_JAVA_HOME||process.env.JAVA_HOME;
const sdk=argument('--sdk')||process.env.ANDROID_SDK_ROOT||process.env.ANDROID_HOME;
if(!javaHome)throw Error('Specify --java-home with a JDK 17+ directory.');
if(!sdk)throw Error('Specify --sdk with an Android SDK directory, or set ANDROID_SDK_ROOT.');
const executable=name=>path.join(javaHome,'bin',name+(process.platform==='win32'?'.exe':''));
const platform=[path.join(sdk,'platforms','android-35','android.jar'),path.join(sdk,'android-35','android.jar')].find(p=>fs.existsSync(p));
const tools=[path.join(sdk,'build-tools','35.0.0'),path.join(sdk,'android-15')].find(p=>fs.existsSync(path.join(p,'lib','d8.jar')));
if(!platform||!tools)throw Error('Android SDK platform 35 and build tools 35.0.0 are required.');
// aapt2 on Windows requires an ASCII working directory, including its inputs.
const build=fs.mkdtempSync(path.join(os.tmpdir(),'modern-chinese-dictionary-apk-'));
const run=(command,args,options={})=>{console.log('Build step: '+path.basename(command)+' '+args[0]);return execFileSync(command,args,{cwd:build,stdio:'inherit',...options});};
const native=path.join(build,'native');
const stable=path.join(root,'.android-build');
run(process.execPath,[path.join(root,'scripts','build-android-assets.mjs')]);
console.log('Preparing ASCII build directory: '+build);
function copyDirectory(from,to){fs.mkdirSync(to,{recursive:true});for(const entry of fs.readdirSync(from,{withFileTypes:true})){if(entry.isSymbolicLink())throw Error('Build inputs cannot contain symbolic links');const source=path.join(from,entry.name),target=path.join(to,entry.name);if(entry.isDirectory())copyDirectory(source,target);else if(entry.isFile())fs.copyFileSync(source,target);}}
copyDirectory(path.join(root,'android','app','src','main'),native);
console.log('Copied native sources');
copyDirectory(path.join(stable,'assets'),path.join(build,'assets'));
console.log('Copied local assets');
fs.copyFileSync(platform,path.join(build,'android.jar'));
for(const name of ['classes','dex','output','signing'])fs.mkdirSync(path.join(build,name),{recursive:true});
// Delete exact stale class/dex outputs only; signing material and APKs are retained.
for(const name of ['classes','dex']){const target=path.resolve(build,name);if(path.dirname(target)!==path.resolve(build))throw Error('Unsafe build output');fs.rmSync(target,{recursive:true,force:true});fs.mkdirSync(target);}
const localTools=path.join(build,'tools');fs.mkdirSync(localTools,{recursive:true});
for(const file of fs.readdirSync(tools))if(/\.(exe|dll)$/i.test(file))fs.copyFileSync(path.join(tools,file),path.join(localTools,file));
const tool=name=>path.join(localTools,name+(process.platform==='win32'?'.exe':''));
// Windows SDK tools still mishandle non-ASCII arguments; relative paths retain
// compatibility with projects stored in Chinese-named workspace directories.
const relative=p=>path.relative(build,p);
fs.mkdirSync(path.join(build,'compiled'),{recursive:true});
for(const file of walk(path.join(native,'res')))run(tool('aapt2'),['compile',relative(file),'-o','compiled']);
const base=path.join(build,'base.apk'),aligned=path.join(build,'aligned.apk');
run(tool('aapt2'),['link','-I','android.jar','--manifest',relative(path.join(native,'AndroidManifest.xml')),'--min-sdk-version','26','--target-sdk-version','35','--version-code','10201','--version-name','1.2.1','-o',relative(base),...walk(path.join(build,'compiled')).map(relative)]);
run(executable('javac'),['-J-Duser.language=en','-encoding','UTF-8','-source','8','-target','8','-bootclasspath',[path.join(tools,'core-lambda-stubs.jar'),platform].join(path.delimiter),'-classpath',platform,'-d',path.join(build,'classes'),...walk(path.join(native,'java')).filter(p=>p.endsWith('.java'))]);
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);}
run(executable('java'),['-cp',path.join(tools,'lib','d8.jar'),'com.android.tools.r8.D8','--lib',platform,'--min-api','26','--output',path.join(build,'dex'),...walk(path.join(build,'classes')).filter(p=>p.endsWith('.class'))]);
fs.mkdirSync(path.join(build,'packer'),{recursive:true});
run(executable('javac'),['-encoding','UTF-8','-d',path.join(build,'packer'),path.join(root,'android','tools','PackageAssets.java')]);
run(executable('java'),['-cp',path.join(build,'packer'),'PackageAssets',base,path.join(build,'dex','classes.dex'),path.join(build,'assets')]);
run(tool('zipalign'),['-p','-f','4',relative(base),relative(aligned)]);
fs.mkdirSync(path.join(stable,'signing'),{recursive:true});
const key=path.join(stable,'signing','offline-preview-signing.jks'),passwordFile=path.join(stable,'signing','offline-preview-signing.password');
if(fs.existsSync(key)&&!fs.existsSync(passwordFile))throw Error('Signing password file is missing; restore it to preserve update compatibility.');
if(!fs.existsSync(passwordFile))fs.writeFileSync(passwordFile,randomBytes(32).toString('hex'),{flag:'wx',mode:0o600});
const signingEnv={...process.env,DICT_APK_KEY_PASSWORD:fs.readFileSync(passwordFile,'utf8').trim()};
if(!fs.existsSync(key))run(executable('keytool'),['-genkeypair','-keystore',key,'-storepass:env','DICT_APK_KEY_PASSWORD','-keypass:env','DICT_APK_KEY_PASSWORD','-alias','modern-chinese-dictionary-local','-keyalg','RSA','-keysize','2048','-validity','10000','-dname','CN=Modern Chinese Dictionary Local'],{env:signingEnv});
const apk=path.join(build,'output','modern-chinese-dictionary-offline-1.2.1.apk');
run(executable('java'),['-jar',path.join(tools,'lib','apksigner.jar'),'sign','--ks',key,'--ks-key-alias','modern-chinese-dictionary-local','--ks-pass','env:DICT_APK_KEY_PASSWORD','--key-pass','env:DICT_APK_KEY_PASSWORD','--out',apk,aligned],{env:signingEnv});
run(executable('java'),['-jar',path.join(tools,'lib','apksigner.jar'),'verify','--verbose','--print-certs',apk]);
run(tool('zipalign'),['-c','4',relative(apk)]);
const output=path.join(stable,'output');fs.mkdirSync(output,{recursive:true});
const final=path.join(output,path.basename(apk));fs.copyFileSync(apk,final);
fs.writeFileSync(final+'.sha256',createHash('sha256').update(fs.readFileSync(final)).digest('hex')+'  '+path.basename(final)+'\n');
console.log(`APK ready: ${final} (${(fs.statSync(final).size/1024/1024).toFixed(1)} MiB), local development signing certificate.`);
if(path.dirname(build)!==os.tmpdir()||!path.basename(build).startsWith('modern-chinese-dictionary-apk-'))throw Error('Invalid temporary build path');
fs.rmSync(build,{recursive:true,force:true});

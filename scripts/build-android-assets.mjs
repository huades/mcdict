import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const root=fileURLToPath(new URL('../',import.meta.url));const target=path.join(root,'.android-build','assets');fs.mkdirSync(target,{recursive:true});
for(const [file,manifest,key] of [['dictionary7.db','manifest7.json','databaseSha256'],['index7.db','index7-manifest.json','database_sha256']]){const data=fs.readFileSync(path.join(root,'generated',file)),info=JSON.parse(fs.readFileSync(path.join(root,'generated',manifest),'utf8'));if(createHash('sha256').update(data).digest('hex')!==info[key])throw Error('Data fingerprint mismatch: run scripts/link_radical_text7.py before packaging.');}
for(const file of ['index.html','app.css','app.js','ui-utils.js'])fs.copyFileSync(path.join(root,'web',file),path.join(target,file));
for(const file of ['dictionary.db','manifest.json','dictionary7.db','manifest7.json','index7.db','index7-manifest.json','unicode-license.txt'])fs.copyFileSync(path.join(root,'generated',file),path.join(target,file));
fs.mkdirSync(path.join(target,'index7'),{recursive:true});
// Text-only radical/candidate UI no longer loads old scan sprites.
for(const file of fs.readdirSync(path.join(root,'generated','index7'))){const stale=path.join(target,'index7',file);if(fs.existsSync(stale))fs.unlinkSync(stale);}
fs.mkdirSync(path.join(target,'images'),{recursive:true});
for(const file of fs.readdirSync(path.join(root,'generated','images')))fs.copyFileSync(path.join(root,'generated','images',file),path.join(target,'images',file));
// Package decoded original scans; device PDF rendering is no longer required.
const stale=path.join(target,'book7.pdf');if(fs.existsSync(stale))fs.unlinkSync(stale);
fs.mkdirSync(path.join(target,'book7-pages'),{recursive:true});
for(const file of fs.readdirSync(path.join(target,'book7-pages')))if(/^p\d{4}\.(png|jpg)$/.test(file))fs.unlinkSync(path.join(target,'book7-pages',file));
const compact=path.join(target,'book7-compact');fs.mkdirSync(compact,{recursive:true});
for(const file of fs.readdirSync(compact))if(/^p\d{4}\.(png|jpg|webp)$/.test(file))fs.unlinkSync(path.join(compact,file));
const book=JSON.parse(fs.readFileSync(path.join(root,'generated','book7-pages.json'),'utf8'));
// Scanned pages are a separately imported offline pack; only its trusted manifest ships in APK.
fs.copyFileSync(path.join(root,'generated','book7-pages.json'),path.join(target,'book7-pages.json'));
console.log('Prepared seventh-edition primary text, fifth-edition backup and optional-book manifest.');

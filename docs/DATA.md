# 资料边界与本地输入 / Local data

Git源码只包含客户端、构建脚本、少量来源指纹及校对记录，不提交原书、词库正文、数据库、扫描页、截图、APK、离线原书包及签名材料。Releases单独提供的APK含查词数据；本次不提供原书离线包。

## 本地资料

以下是当前脚本校对过的样本指纹，不代表其他同版文件可直接混用。

| 资料 | 角色 | SHA-256 |
| --- | --- | --- |
| 第5版MOBI，2005版内容 | 独立备用词库 | `f0477703fb0b4b3b822ee18463b58f88324bf6317b9b462594bbbc3a7cd27855` |
| 第7版PDF，1,897页 | 部首索引及可选原书 | `efd0d6b626a306fd633a1ce1c970a03f10435c28be668014f05671c114b80216` |
| 社区第7版文本 | 默认词库输入 | `0e3d44357b005e2b216ad1a2c97cfa924fd5ab9777866569d18f9f5ba110fdc7` |

第7版文本来源为[ModernChineseDict](https://github.com/pampas9000/ModernChineseDict)，Git blob为`90dc7fb83197166ebd94516290252b78b5df31a8`。来源项目说明其最初经过OCR，并持续社区校订；它不是出版社官方数据。来源指纹见[source.json](../source-text7/source.json)，已确认的本地修订见[corrections.json](../source-text7/corrections.json)。8个未能解析到有效正文的跳转没有启用。不使用第5版义项补造第7版内容。

PDF第33—34页为部首目录，第35—89页为检字表；正文页码加94为PDF页码。归部、部外笔画范围及未单列情况均沿用这份原书。保留201个主部首和279个含附形项目；无法对应文字词条的记录仍可从“原书索引”核对。界面中的“社区校订”标签不表示完成了全书逐条校勘。

原书和社区数据的权利归相应权利人；代码公开不表示取得辞书内容的再分发授权。本仓库未附带辞书数据授权，也未为本项目声明开源许可证。

## English

Git commits distribute source code and build tools only. Books, dictionary text, generated databases, scanned pages, screenshots, APKs, optional book archives, signing keys and user backups are excluded from Git. The separate release APK includes lookup data; the optional book archive is not distributed in this release. The table identifies the exact local inputs reviewed by the current scripts. Obtain appropriate access to those inputs separately; a different scan requires a new index review rather than disabling hash checks.

The default text source is a community-corrected dataset, not an official publisher export. Source fingerprints and a small correction ledger are included. Fifth-edition definitions stay separate. The project's public visibility does not grant rights to dictionary content, and no open-source license is asserted here.

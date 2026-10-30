# 现代汉语词典 · mcdict

Android 8.0+ 的本地查词与原书阅读客户端。第7版社区校订文本为默认词库，第5版独立备用；支持部首查字、拼音检索、生词本和可选扫描原书阅读。

**源码提交不包含辞书文件、词库数据库、APK、原书离线包和签名密钥。** 安装包通过 [Releases](https://github.com/huades/mcdict/releases) 单独提供，内置查词数据；原书离线包不随本次发布提供。克隆源码后可以直接运行基础检查；自行构建完整App需要准备[指定本地资料](docs/DATA.md)。项目并非商务印书馆官方App，社区文本也不是官方电子词库。

[功能](#功能) · [基础检查](#基础检查无需辞书数据) · [本地构建](#本地构建完整app) · [使用与排错](#使用与排错) · [English](#english)

## 功能

| 功能 | 行为 |
| --- | --- |
| 字词 / 拼音 | 包含检索、拼音和首字母查询、释义反查；多音与同形记录分别保存 |
| 版本切换 | 第7版社区校订为主，第5版独立备用，收藏与历史保留各自版本ID |
| 部首查字 | 文字部首、笔画分组；默认显示关联到第7版文本的候选，原书索引可单独核对 |
| 生词本 | 分类、备注、到期翻卡复习、本地JSON备份及恢复 |
| 阅读 | 字号、浅/深色及跟随系统主题，手机与平板布局 |
| 原书 | 可选导入配套ZIP；核对全部1,897页后离线阅读，支持缩放、跳页和书签 |

运行时不依赖OpenAI API，不申请联网权限。系统朗读需要设备已安装中文离线声音。页图核对、原书导入及文字来源说明见[DATA.md](docs/DATA.md)。

## 环境与目录

- 基础检查：Node.js 22、Python 3.12、JDK17及以上。
- 完整构建：Windows、Android SDK platform35及build-tools35；Python的SQLite须启用FTS4（全文检索模块）。
- 资料处理：BeautifulSoup、Pillow、NumPy、pypdf、pypdfium2；索引重建另需Windows简体中文OCR与RapidOCR。版本见`requirements*.txt`。

```text
web/                  HTML / CSS / JavaScript界面
android/              原生Android服务、阅读器、资源与打包工具
scripts/              资料处理、构建及验证脚本
tests/                基础回归与本地数据检查
source-text7/         来源指纹、少量校订记录（无正文）
source-index7/        页码和笔画修订记录（无扫描页或完整转录）
docs/                 数据边界及验证说明
```

## 基础检查（无需辞书数据）

先安装Git、Node.js、Python和JDK。以下命令在PowerShell中执行：

```powershell
git clone https://github.com/huades/mcdict.git
cd mcdict
node --check web/app.js
node tests/ui.test.mjs
node scripts/check-native.mjs
python -m compileall -q scripts tests
```

预期会看到JS界面检查通过，以及原生页码、主题/安全边距、数据库更新检查通过。若找不到`javac`，将实际JDK安装目录设为`JAVA_HOME`，或把JDK的`bin`目录加入PATH。

GitHub Actions只运行上述不含辞书数据的源码检查；不构建APK、不获取辞书、不上传产物。实际验证范围见[VALIDATION.md](docs/VALIDATION.md)。

## 本地构建完整App

### 1. 准备资料和依赖

在仓库的上级目录放入一份匹配指纹的第5版MOBI和一份第7版PDF，勿同时放入多份同扩展名文件。文件保持原样；脚本会校验指纹，详见[DATA.md](docs/DATA.md)。

```text
workspace/
├─ dictionary5.mobi
├─ dictionary7.pdf
└─ mcdict/             ← 以下命令的工作目录
```

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
$env:PYTHONIOENCODING = 'utf-8'
```

下文用`python`代表`.\.venv\Scripts\python.exe`；可直接使用这个完整路径执行所有Python命令，无需修改PowerShell的脚本执行策略。

### 2. 生成本地词库和索引

在`mcdict`目录中依次执行：

```powershell
python scripts/build_data.py
python scripts/fetch_text7.py
python scripts/build_text7.py
python scripts/pdf7_prepare.py
powershell.exe -NoProfile -File scripts/pdf7_windows_ocr.ps1 -First 33 -Last 91
python scripts/pdf7_rapid_ocr.py
python scripts/pdf7_transcribe.py
python scripts/pdf7_catalog.py
python scripts/build_index7.py
python scripts/link_radical_text7.py
```

`build_data.py`处理第5版资料并下载辅助Unicode数据，`fetch_text7.py`获取当前锁定指纹的社区文本。两个OCR脚本仅用于重建原书索引；正常查词直接读结构化文字。脚本生成的数据只保存在本机忽略目录中。如果出现未解决的校对项，应对照原书修订，不能仅为通过构建而删除校验。

### 3. 准备原书清单和可选离线包

当前App用可信页面清单验证可选原书包，因此完整构建仍需先生成该清单。转换与压缩全部页面会花一些时间：

```powershell
python scripts/build_book_pages.py
python scripts/optimize_book_jpeg.py
python scripts/compact_book_pages.py
python scripts/build_optional_book.py
```

扫描页只进入独立ZIP，不进入APK。原始PDF保持不变。

### 4. 测试、配置并构建APK

```powershell
python tests/test_text7.py
python tests/test_data.py
node tests/ui.test.mjs
node scripts/check-native.mjs
```

将下面两个路径替换为你电脑上的真实目录；JDK目录内应有`bin/java.exe`，SDK目录内应有`platforms/android-35/android.jar`和`build-tools/35.0.0`：

```powershell
$env:DICT_JAVA_HOME = 'C:\tools\jdk-17'
$env:ANDROID_SDK_ROOT = 'C:\tools\android-sdk'
node scripts/build-apk.mjs
python scripts/verify_text7_release.py
```

APK生成在`.android-build/output/`，验证脚本会在上级目录复制中文命名的安装包。签名文件只留在`.android-build/signing/`，请私下备份；重新生成签名将无法直接覆盖安装原签名版本。

## 使用与排错

1. 从 [Releases](https://github.com/huades/mcdict/releases) 下载APK，或将本地生成的APK传到安卓设备，按系统提示安装。旧版应覆盖升级，收藏与书签按版本ID保留。
2. 等待首次词库准备完成，搜索“安静”“动车”或`anjing`；词条会显示实际版本。查词数据已在你构建的APK中，不需要另行导入。
3. 点部首笔画和文字部首，再选部外笔画，默认查内置文字释义。不能可靠关联的字保留在“原书索引”中。
4. 如需阅读原书，把本地生成的配套ZIP传到手机且不要解压，在“原书”中选择导入。仅文字查词无需这个ZIP。
5. 在设置中导出个人备份；卸载/清除应用数据会移除收藏及导入的原书。

常见问题：

- **克隆后缺少`generated/`？** 正常，数据库不随源码分发；按构建流程用自己的资料生成。
- **文件指纹不匹配？** 资料不是脚本所核对的同一份文件。先核对版本和来源，需要重新校对时保留新的来源记录。
- **没有Windows中文OCR？** 在系统语言设置中安装简体中文识别能力后重试。
- **找不到SDK/JDK？** 检查上面的两个环境变量，也可以向构建脚本传`--java-home`和`--sdk`。
- **无法覆盖安装？** 确保包名及签名相同；勿为了安装而先卸载尚未备份的数据。
- **原书ZIP导入失败？** 必须使用与APK页面清单匹配的配套ZIP，不能用PDF或其他版本的页图压缩包代替。

开发预览：生成数据后运行`python scripts/preview.py`，访问`http://127.0.0.1:4186`。预览只使用临时内存个人记录；TTS、安卓文件选择器和原书导入须在设备上测试。

## English

**mcdict** is an Android 8.0+ offline dictionary client. It supports word/pinyin/full-text search, source-backed radical lookup, edition-specific collections, notes, review cards, backups, themes and an optional scanned-book reader. Seventh-edition community-corrected text is the primary input; fifth-edition content remains separate. It is not an official publisher app, and targeted checks are not exhaustive proofreading.

Git commits contain code and build tools, **not books, dictionary databases, APKs, page images or signing material**. The APK is distributed separately through [Releases](https://github.com/huades/mcdict/releases), with lookup data included; the optional scanned-book archive is not part of this release. Clone the source and run the four commands under “基础检查” to validate it without dictionary data. Node22, Python3.12 and JDK17+ are required. GitHub Actions runs those source checks only; Android device behavior is not covered.

For a complete local build on Windows, obtain the exact inputs documented in [DATA.md](docs/DATA.md), place the MOBI/PDF beside the repository, install `requirements-ocr.txt`, then follow the numbered data/index/page-generation pipeline above. Configure `DICT_JAVA_HOME` and `ANDROID_SDK_ROOT` with your actual JDK and SDK35 paths. Run the data tests and `node scripts/build-apk.mjs`; outputs go to `.android-build/output/`. Keep the signing key private to support upgrades.

Install the release APK or your locally built APK and search immediately. Original scans are optional: select the matching generated ZIP from the Book tab. Import validates all 1,897 pages. Export personal backups before uninstalling. Missing generated files, hash mismatches and ZIP mismatches require completing or reviewing the local-data pipeline, not disabling checks. Repository visibility grants no dictionary-content rights; see [DATA.md](docs/DATA.md) for source and licensing boundaries.

# 验证范围 / Validation

本机发布准备检查（2026-10-30）：

- JavaScript语法与生产界面事件检查通过：版本路由、部首候选、主题变化、两版收藏ID、GitHub图标与原生跳转。
- 生产Java逻辑检查通过：19项页码/升级检查、11项主题/安全边距检查，以及数据库按指纹更新、缓存修复、失败回滚、个人数据保留。
- 本地数据检查：8项第7版及部首关联检查、12项第5版与原书索引回归检查。它们需要本地辞书数据，数据不会上传。
- 纯源码副本检查通过：JS语法、界面事件、Java回归和Python编译均不依赖本地辞书数据。
- 63个源码文件的严格UTF-8、JSON/XML格式、Git差异格式，以及敏感信息、个人路径和大文件扫描通过。
- APK本地编译、签名、ZIP对齐及完整性验证通过；打包界面与数据逐文件匹配，内置数据库指纹校验通过。APK及辞书数据不作为源码提交内容。

`.github/workflows/checks.yml`只覆盖不依赖辞书的源码检查。仓库首次推送前，不能把尚未运行的远程Actions称作“已通过”。

尚未执行安卓真机/模拟器安装运行验收；原生文件选择器、原书导入、设备语音与具体设备显示效果仍需设备测试。结构检查和原书抽查也不等同于全部义项逐条人工校勘。

## English

Local validation covers JS syntax and real event handlers, Java pagination/theme/inset/database-update logic, and data-dependent regression checks using private local assets. The public workflow runs source-only checks. It does not build an APK or download dictionary data. Android hardware/emulator installation and native device flows have not been verified. Local source-data review is targeted, not exhaustive.

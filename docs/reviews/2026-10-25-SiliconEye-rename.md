# SiliconEye名称与入口迁移

用户批准将仓库及项目展示名称由silicon-eye / Silicon Eye统一为SiliconEye。本轮基线c179e64。

- 现有仓库重命名为[XIAHONGYUU/SiliconEye](https://github.com/XIAHONGYUU/SiliconEye)，仓库ID1258358595保持，不新建或复制仓库。
- 作品入口为[SiliconEye Demo](https://xiahongyuu.github.io/SiliconEye/)，继续使用gh-pages根目录发布。
- 同步README、页面标题/页眉/页脚、作品案例与简历入口、开发指南和构建配置；本机origin更新为新仓库URL。
- 本机目录仍为silicon-eye，Python模块silicon_eye和silicon-eye命令保留兼容；原图、模型、数据哈希、审批、历史发布回执不改写。旧回执中的旧网址保留为当时事实。
- 原CI的workflow权限阻塞继续保留，本次不修改凭证权限或启用CI。

[迁移前记录](../../benchmarks/SiliconEye-rename-v1/before.json) · [本机验证](../../benchmarks/SiliconEye-rename-v1/verification.json) · [实际发布回执](../../benchmarks/SiliconEye-rename-v1/publication.json) · [迁移前任务原文](../history/current-task-before-2026-10-25-SiliconEye-rename.md)。

核对范围：来源42项/资产18项哈希、36条相关本地链接、旧入口归档原字节，以及390px手机/1440px桌面标题布局。改名不涉及识别算法，未重复运行全项目测试。公网核对结果以发布回执为准。

实际内容提交e574bf5，Pages提交01d621b并构建成功；23个公开文件HTTP读取和SHA比对通过，远端README字节一致。仓库名称为SiliconEye且ID保持1258358595。

# 2026-11-11 GitHub 节点证据

包含2026-11-09批处理、扩大批、全幅来源清查及实际裁决的320个文件；按内容哈希去重为242个数据块。原始路径保留，不改写已审页面、manifest或决策。

二进制归档分3片，总计98,731,508字节；完整SHA256见`evidence-manifest.json`。`runs/`继续被Git忽略，克隆后需要恢复证据才能打开文档中的本轮runs链接。

在仓库根目录恢复到全新临时目录，避免覆盖已有结果：

```bash
mkdir -p /tmp/siliconeye-checkpoint-20261111
cat benchmarks/github-checkpoint-2026-11-11/evidence.tar.gz.part* \
  > /tmp/siliconeye-checkpoint-20261111/evidence.tar.gz
sha256sum /tmp/siliconeye-checkpoint-20261111/evidence.tar.gz
# 应为63745525c2989939086f0c4517a78812893d01c09afc7efed225259ff83bd94b
mkdir -p /tmp/siliconeye-checkpoint-20261111/restored
tar -xzf /tmp/siliconeye-checkpoint-20261111/evidence.tar.gz \
  -C /tmp/siliconeye-checkpoint-20261111/restored
# 复制缺失文件回仓库，已存在文件不覆盖：
cp -an /tmp/siliconeye-checkpoint-20261111/restored/runs/. runs/
```

全幅首轮obsolete `full/`（重复约140MB）未收入；最终`final/`、原裁决、失败诊断、输入配置、路径、候选工作包、计时和逐步接续材料已收入。旧算法来源脚本一并保留。原照片及历史父基线仍由仓库已有data/docs/benchmarks提供。

已实际恢复所有文件并逐个核对SHA256，四套最终复核包通过`load_package`验证。源码/配置/测试是正常Git文件，证据包不是安装依赖或外部运行时。归档构建脚本见`build_evidence.py`，执行时要求使用新的输出位置或先另存已有归档，拒绝覆盖已有分片。

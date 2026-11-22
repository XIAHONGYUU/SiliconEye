# 2026-11-22：已审局部几何与可恢复证据

本节点保存25对来源关系、H01/H02与十组R01–R10的实际归档及接续结果。共12处局部矩形/线宽已审、27对直接来源关系、2条宽边缘；54金属、34局部连接、188候选设计孔保持。全局几何、位置、间距、端点、VIA和网表没有自动获批。

证据按原始runs路径去重打包：125文件、78个唯一数据块，压缩20,149,413字节；临时恢复125文件SHA及两套新固定复核包通过。初版和生成阶段页面只是过程，实际裁决以归档的review-decision.json为准。

克隆后按顺序恢复[11月11日父节点](../github-checkpoint-2026-11-11/README.md)、[11月21日增量](../github-checkpoint-2026-11-21/README.md)，再恢复本节点。新增源码与测试是正常Git文件，不由证据包替代。

```bash
mkdir -p /tmp/siliconeye-checkpoint-20261122/restored
cat benchmarks/github-checkpoint-2026-11-22/evidence.tar.gz.part* > /tmp/siliconeye-checkpoint-20261122/evidence.tar.gz
sha256sum /tmp/siliconeye-checkpoint-20261122/evidence.tar.gz
# 应为 ac3f79c709c0a6ee8630d79c9b1b6648ee83a21b307271b4d94637fca1f0b2bc
tar -xzf /tmp/siliconeye-checkpoint-20261122/evidence.tar.gz -C /tmp/siliconeye-checkpoint-20261122/restored
# 不覆盖已有证据；如同路径存在不同SHA，先单独排查
cp -an /tmp/siliconeye-checkpoint-20261122/restored/runs/. runs/
```

[清单](evidence-manifest.json)逐文件记录SHA；[验证记录](verification.json)保留软件、真实裁决、来源、父模型与展示保护检查。build_evidence.py复用上一节点的去重归档实现，拒绝覆盖已有归档。

本节点完成后下一步是H03宽母线真实上下边界分析：不能将其单条亮脊当中心扩成窄线。其余数值暂停和孔阵列上缘语义暂停保持；不重复审批12处已审局部形状。提交/推送状态以Git引用为准。

# 2026-11-21 M3裁决接续与可恢复证据

本增量归档保留`m3-triage-20261111`与`m3-identity-followthrough-20261119`两个runs目录，共99文件、70个去重数据块，压缩6,829,566字节。已在临时目录完整恢复并逐文件核SHA256，两套最终固定复核包通过检查。原路径/来源hash/已审文件不改写；过程输出仅为历史，当前有效分流用`verified/`，后续诊断用`verified-diagnostics/`。

旧父基线依赖[11月11日证据归档](../github-checkpoint-2026-11-11/README.md)，克隆后先按该说明恢复，再恢复本增量。源码/测试为正常Git文件，不在证据包中替代代码。

```bash
mkdir -p /tmp/siliconeye-checkpoint-20261121/restored
cat benchmarks/github-checkpoint-2026-11-21/evidence.tar.gz.part* > /tmp/siliconeye-checkpoint-20261121/evidence.tar.gz
sha256sum /tmp/siliconeye-checkpoint-20261121/evidence.tar.gz
# 应为 81699dcd99ec7fa9b5f6b3b43a89353e08b56c63ca99e5c1848b3a83e550a45e
tar -xzf /tmp/siliconeye-checkpoint-20261121/evidence.tar.gz -C /tmp/siliconeye-checkpoint-20261121/restored
# 仅复制缺失文件，不覆盖已有证据
cp -an /tmp/siliconeye-checkpoint-20261121/restored/runs/. runs/
```

重建工具沿用前一节点去重归档实现，见`build_evidence.py`；已有归档会拒绝覆盖。

实际11月19日G01/G05/G24均accepted：只接受两对直接来源关系，另将G24两片段分类为宽金属边缘，不作为新独立细导体。304组仍是AI候选，不升级为人审整链身份。下一待审批次为5组/25对未审直接关系；54金属、34局部连接、188候选孔不变。

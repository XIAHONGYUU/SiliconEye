# 版本化审核证据输入

`roi2-reviewed-inputs-v1.zip`只包含完整ROI2复核包读取、但原先未跟踪的9项历史runs输入，约1.9MB。逐项路径、字节数和SHA-256见同名JSON。原图已在仓库data中，不在此归档重复保存。

```bash
python -m silicon_eye.evidence_archive \
  --archive benchmarks/evidence/roi2-reviewed-inputs-v1.zip --root .
```

恢复只补缺失文件；已有字节相同则跳过，已有不同内容则失败，绝不覆盖原证据。请在明确仓库根执行。磁盘写入失败时可能已恢复部分正确文件，修复后可重复执行。

这恢复的是当前示例明确使用的输入，不是对所有旧反馈中任意深度引用的全量历史恢复。原始审核记录、哈希和矩阵不改，Git仍忽略普通runs产物。

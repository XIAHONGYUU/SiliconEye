# 统一局部复核包入口

首次克隆后，先恢复版本化的9项审核证据（保留原路径与字节，不覆盖已有不同文件）：

```bash
.venv/bin/python -m silicon_eye.evidence_archive \
  --archive benchmarks/evidence/roi2-reviewed-inputs-v1.zip --root .
```

随后在仓库根执行：

```bash
.venv/bin/silicon-eye annotate review-package \
  --spec benchmarks/review-package-roi2-v1.json --root . \
  -o runs/roi2-unified-next
```

输出目录必须不存在。入口重放现有判断，不识别新材料、不调用外部模型，不修改原图、裁决或电气关系。

## 输入

请求文件使用 `schema_version: 1`、`document_kind: block_review_package`，只包含：

- `case`：带 `path/sha256` 的统一 block case。
- `registrations`：已验收宏观配准列表；每项含 `profile`、`approval` 和 `frozen_matrix_pointer`。`approval.record`绑定原人工记录，`pointer`是JSON Pointer，`value`必须为 `accepted`。矩阵与原审核gate中绑定的冻结记录逐值核对，不能换成另一次变换。
- `materials`：带 `path/sha256` 的材料观察列表。模型候选须显式声明candidate状态；已复核观察须绑定人工 `review_source`，其 `sources.candidate_spec`必须是当时展示的原候选。材料ID、层、原图、核心/包络须与获复核的候选一致。

两个列表都可以显式为空，适用于仅有电路证据的案例；不会猜测未登记来源或自动寻找最新文件。v1支持当前AA/poly支持多边形与原生像素裁剪、homography矩阵及纯平移输出裁剪。其他观察格式应先明确规范化，不添加案例名称分支。

`--root`是全部来源路径的显式根，拒绝绝对路径/逃逸路径。核对case声明来源、所选配准/材料记录及其直接人工/证据引用；不递归恢复任意历史JSON的全部引用链。

## 输出

| 文件 | 内容 |
| --- | --- |
| report.md | 总览：同状态电路图、配准、材料身份状态及未知项 |
| bundle-state.json | bundle_id、block_state_id、配准/材料记录、保守验收标志 |
| circuit/ | 复用原block导出器的电路图、端子表、同网矩阵与独立manifest |
| registration-NNN-*.png | 从原图一次重采样的对齐图、叠图、有效mask、已复核范围mask |
| material-NNN-LAYER-*.png | 原生像素裁剪与AI核心/包络展示；不是完整材料分割 |
| manifest.json | 已读取输入的哈希、代码哈希及全部产物哈希 |

包生成图携带bundle_id PNG元数据；电路子包携带原block_state_id，顶层manifest绑定全部文件。电路与材料/配准各保留自己的状态，不因打包自动升级验收。

宏观配准批准不等于CT落点/精细配准；材料身份确认不等于核心/包络像素真值。所有材料边界保留candidate，尺寸仍unknown。不自动重新运行CT阈值或拟合配准；CT/其他局部信息保留在绑定观察中。

## 失败、重放与验证

来源漂移、缺失人工记录、非人工批准、批准对象/原候选不匹配、错误坐标系/矩阵方向、越界/退化多边形均报错。先预检，再在临时目录生成，成功后移入新目录；中途失败不发布半成品，不覆盖已有目录。冲突case只保留诊断包，CLI返回2，不生成正常图片/连接表。

输入清单可用于复放：只复制manifest.inputs中明确列出的文件到一个新根，再使用同一请求与新 `--root` 运行。保持请求和代码相同，bundle_id及产物哈希可一致；这证明软件重放，不证明照片物理事实或跨芯片泛化。

验证包含已知平移的真实像素位置、来源/批准绑定、候选保留、材料包络约束、未知端子不合并、冲突诊断、生成失败不留半包和仅声明来源的隔离重放。

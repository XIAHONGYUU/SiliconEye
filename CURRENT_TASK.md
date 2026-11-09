# 当前任务

## 当前目标与授权

用户已导出扩大批裁决，授权再次扩大范围。本轮覆盖整张M3照片，处理已有身份之外的来源候选；从局部规则外延转入全幅来源清查，不将候选清单冒充几何完成。

## 当前队列

| 项目 | 状态 | 下一步 |
| --- | --- | --- |
| 固定外延入口 + 全幅来源清查入口 | 已验证 | 复用现有命令 |
| M3-FULL-INVENTORY-20261109-V1 | accepted | 来源清单已归档；后续身份对应/几何接入待新任务授权 |
| 后续几何 | 未开始 | 从已审清单建立新身份对应，再批量接入；不得直接采用片段 |

## 最新交付

- [全幅复核页](runs/m3-wide-inventory-20261109/final/review/index.html) · [一页摘要](docs/reviews/2026-11-09-m3-full-inventory.md) · [覆盖图](runs/m3-wide-inventory-20261109/full-atlas.png) · [清单](runs/m3-wide-inventory-20261109/final/inventory.json)。
- 全幅5712×4284，共24470208像素；672亮脊线片段，30旧路径上下文、642未分配/部分新增；8区域、16证据图。片段数不是金属身份数，当前没有新增规则几何或连接。
- [优先候选133个](runs/m3-wide-inventory-20261109/priority-candidates.json)仅按跨度及风险排序，不是已确认正确。239组件存在分叉/并行合并风险，20个外围边缘风险，两类可能重叠。
- 程序识别4.35秒、材料全包23.67秒；本轮首次实现/两次运行/测试/检查至交付记录462.02秒（7.7分钟），初始读取、导出查找及最终聊天未计时。
- 2项针对性测试、Ruff、diff检查通过；坐标界限、片段无重复分区、复核包哈希检查通过。抽查三张区域对照及全幅图，确认边缘/密集结构风险；没有672条逐项人工验证。
- `python -m silicon_eye.ridge_inventory --spec configs/m3-full-ridge-inventory.json --output 新runs目录`。最终输出为final/；full/是更宽松旧路径重叠分类的首轮，不作为当前复核入口。

## 已归档与当前父基线

- [扩大批六组裁决](runs/batch-expanded-20261109/review-final/review-record.md)全部accepted且实际归档；页面交互至导出21.772秒，不含交互前读图。LOWER局部身份检查随组接受，不升级精确投影或承载。
- [全幅来源清单裁决](runs/m3-wide-inventory-20261109/final/review/review-record.md)8区域全部accepted，页面首次交互至导出29.725秒；只认可来源片段清单，不批准身份、几何、连接或物理端点。
- [当前已审范围基线](runs/m3-wide-inventory-20261109/reviewed-baseline.json)绑定LOWER-SAFE最终工作包、扩大批裁决和之前的已审合并基线。新全幅清查不修改该模型。
- [第一批](runs/batch-production-20261109/review/review-record.md)、[第二批](runs/batch-production-round2-20261109/package-final/review/review-record.md)已归档。54金属、34已审局部连接、188候选设计孔保持。
- [原历史基线](benchmarks/w34-left-m2-reviewed-v2/working-baseline.json)保留旧身份/接口来源。全幅候选身份unassigned，不能直接采用到网表。

## 唯一下一步

全幅来源清单已归档；下一轮若要继续，先从已审清单建立新身份对应/候选几何，需用户确认范围与优先级。不得把672片段直接当导体，也不得由区域通过升级身份、连接或物理端点。

## 生效边界与未提交工作

- 稳定决定见[DECISIONS.md](DECISIONS.md)，阶段历史见[CHANGELOG](docs/history/CHANGELOG.md)及[旧入口归档](docs/history/current-task-before-2026-11-09-workflow-efficiency.md)。
- L01几何G1、短头V2身份I1已审；承载/上层ID/物理孔数未知，未建新VIA或连接。N1/N2/N3/S1仍为非孔，不重审、不推导全局断开。
- source_to_design_transform=null、geometry_adopted=false、net_edges=[]、complete_network=false，skill为LIMITED_TRIAL_V2；不导出自动网表，不采用精确共同几何。
- 六处材料、BF25及返回路径、旧配准拒绝项、AA/POLY/CT保护和其它未决按原历史保留。
- 固定入口代码/配置/测试/说明和本轮材料已本地 checkpoint（不推送、不覆盖旧证据）；新增ridge_inventory模块和对应测试/配置，原外延算法不变。 [入口说明](docs/metal-extent-batch.md)。
- 每批周期记录继续写入[cycle-time-v1](benchmarks/cycle-time-v1/README.md)，默认复核窗口周二/周五各30分钟，可随用户安排调整。

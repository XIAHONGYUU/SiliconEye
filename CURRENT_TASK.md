# 当前任务

## 任务合同

- **目标**：将用户复核后的当前局部材料提取版本提交到GitHub，明确保留CT漏检问题。
- **基线**：`XIAHONGYUU/silicon-eye`，main，`90695080352f7a8e7396cdfecdd84dacca13a7ad`；保留前序本机骨架修改。
- **范围**：新增示例引导材料工具、CLI子命令、参数/测试/文档和runs证据；冻结配准及原图不变。
- **不变量**：原图、配置、依赖声明及无关算法不变；本轮用户明确授权更新GitHub开发版本，不调用外部模型、不宣称正式算法验收通过。
- **优先级**：可回查的证据和真实验证优先于功能数量；先设计，再实现。
- **授权**：用户明确表示AA/poly当前结果还好、CT有漏检，并授权更新GitHub版本；沿用已确认的XIAHONGYUU GitHub noreply身份，不调用外部模型。
- **输出**：本机可重复命令、逐层变换/参数/输入哈希/叠加图/局部图/对应点误差；不将未复核候选点称为人工真值。
- **完成条件**：局部像素坐标/来源哈希/候选与确认状态受校验；首批标注对照图可复核；未知尺度不产生物理尺寸，候选不成为器件真值；测试通过；实际未通过不能被改写为完成配准。
- **证据**：固定历史基线见 docs/baseline.md；本轮验证见 docs/registration-validation.md。
- **停止条件**：缺凭证、源图破坏风险、外部变更或需要人工裁决的物理事实。

## 当前结果：三类材料按序检查包

2026-10-15：用户认可AA中心/内环间隙修正，并要求同一区域AA/poly/CT依次提取供检查。已输出 runs/material-review-v1/report.md。

- 仍为同两张1500×850原生裁剪，单位px。AA从aa.jpg，poly/CT从poly.jpg；各自native坐标和裁剪偏移记录，未直接混合不同照片像素。
- AA：示例邻域严格保留v2修正，邻域外Gaussian/Otsu扫描增加未复核候选，保留未知拓扑修剪和中心/内环不合并检查。新区域不视为真值，较暗内部可能漏检或碎片。
- poly：上一版连续条带可见支持逐像素不变，没有补被CT遮挡的下层几何。
- CT：对第二张整幅裁剪运行紧凑亮斑检测，不限poly提示域。亮边可能误选/弱CT可能漏检，不按CT位置推断AA/poly。
- 每类提供01-AA/02-poly/03-CT的mask、overlay、extracted原像素图及geometry JSON；另保留原图、AA未复核新增支持和拓扑未知支持。AA/poly/CT候选分量50/26/508，不是确认对象数。
- 中心/内环原生检查点分别处在分量29/26，均为前景且不相连；poly逐像素一致已核验。三张叠加已视觉复核。原图/原guided证据/参数/源码快照哈希通过。
- 新增3项行为测试，全套125 passed；相关Ruff、git diff --check通过。原图、人工标注、冻结配准及旧证据不变，没有本轮提交/推送/外部模型调用，设备阶段仍关闭。
- 输入 benchmarks/material-review-v1.json；工具 material_review.py；说明 docs/guided-material-extraction.md。

## 命令

```bash
.venv/bin/silicon-eye annotate materials \
  --spec benchmarks/material-review-v1.json \
  -o runs/material-review-next
```

新输出目录；依赖本机已有人工引导证据，没有宣称缺输入的检出可直接运行。

## 用户复核与GitHub版本

2026-10-15：用户反馈“除了CT有漏检之外其他的还好”，明确要求更新一个GitHub版本。AA/poly为当前局部目视可接受；CT有漏检，位置/召回率尚未独立标注或量化。复核记录 benchmarks/material-review-feedback-v1.json 绑定当前报告及三类mask哈希，不升级为全片/精确材料/器件真值。

本轮提交示例引导提取、AA拓扑纠错、三类顺序检查导出、参数、测试、说明与人类复核记录；人工标注/批量runs/.venv继续留本机。125 tests passed，相关Ruff、git diff --check通过；远端已fetch核对无新增提交。用户选择的提交身份XIAHONGYUU <280077814+XIAHONGYUU@users.noreply.github.com>，账号已核验。

这是保留CT已知缺陷的开发快照，不在发布动作中继续调参；具体提交和同步状态以Git HEAD及origin/main为准。

## 唯一下一步

补充漏检CT的位置/范围标注，再改进CT召回；保持当前获目视认可的AA/poly局部基线不退化。不将未量化的目视认可当作像素精度或器件/连接验收通过。

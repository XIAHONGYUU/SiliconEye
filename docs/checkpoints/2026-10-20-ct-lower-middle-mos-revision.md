# 中下部CT局部修订：三排源漏、边列与F双孔

用户已确认C/D上下排大多数源漏为三排孔，C下排右侧有孔而红叉不是孔，D边侧漏孔，F单独栅孔应为两个；其他橙色候选全部批准。[原话及执行范围](../../benchmarks/ct-lower-middle-mos-revision-v2/human-review-v1.json)。

[新版复核页](../assets/ct-lower-middle-mos-revision-v2/index.html)保留原图、规则图、PNG预览、修订前图和独立M1区域。本轮只需看C/D孔列及边列、F双孔相对位置，不重复验收143处已批橙框，A/B/E仅保留上下文。

## 问题原因及修订

原剖面只检测到两排亮峰时，实际峰数被当成了完整行数，再将两行拉满AA高度。这既漏第三行，也放大孔距。原几何门检查方孔、间距、材料包围，不能发现“少了一整排但仍合法”。问题属于观察完整性与结构验证缺项，不能归因于AA内只能容纳两排。

- C上排11个完整源漏列：原橙色第一排按批准纳入，成为三排。阶梯最右列保留两个合法位置；红叉明确排除，不移动AA去容纳它。
- C下排11个完整源漏列：已有第二行由AA下端回到中排，补第三行。最右阶梯边列补两个局部候选，只有下半段有合法AA承载。
- D上下排各11个完整源漏列：按共同行相位恢复三排。上排原第一行回中间、补首行；下排原橙色第三行纳入。两排阶梯最左各补一个候选；不将阶梯边列盲目复制成三排。
- F的G47-P01：原单孔设计坐标左移6px，补右孔，孔距12px。原实测亮峰及来源保持。
- 143处已批橙框使用human_confirmation、algorithm_detected=false。额外27处按本次数量/存在裁决及邻近相位定位，精确位置仍为局部候选，不伪造算法亮峰或人工精确像素标注。D边列源图与AA具体行相位仍有不确定，不自动改变AA。

[CT模型](../../benchmarks/ct-lower-middle-mos-revision-v2/model-v1.json)共7044孔；新增170＝143已批橙框＋27数量/边列/栅孔补充。34条原CT记录局部修订，其中23条中心变化，其余为行索引重编；6840条父记录完全不变。原6874条来源证据全部保持，原4940条完整快照完全不变；695POLY/335AA对象不变。历史661环孔几何细节意见和其他局部批准范围继续继承，不因模型锁定自动升级。

## 检查与验收边界

[结构与防退化检查](../../benchmarks/ct-lower-middle-mos-revision-v2/stage-quality-v1.json)：44个完整源漏列均三排且组内共相位、等节距；阶梯边列按2/1/2/1检查；红叉范围无CT；F两孔；另四条未裁决单峰栅不自动补满。原版本有44个本轮数量要求不满足，修订版本全部满足。这是用户裁决驱动的样本检查，不是算法独立发现所有漏孔的证据。

7044孔整组几何PASS：重叠0、最小间距违规0、最小孔边距4.4px。保留5px方孔、3px孔距、1px包围/沟道避让预算；AA/POLY包围通过。不是实际PDK DRC。

49项相关测试通过（5.55s）；输入与父快照哈希、SVG/PNG/本地资源和模拟切换通过；C/D/F规则预览已目视检查。真实浏览器渲染未实测。原图精确中心、工艺尺寸、新CT的M1/net归属及全幅完整性仍未知。[验证锁定](../../benchmarks/ct-lower-middle-mos-revision-v2/verification-v1.json)。

复现：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-lower-middle-mos-revision-v2/spec-v1.json --output runs/新的中下部CT局部修订目录`。

下一门只复核C/D边列与三排相对排布、F双孔；已批143橙框和原4940不重审。

## 验收追记：C、D、F均批准

用户确认“C，D,F三项均批准”。[本次原话](../../benchmarks/ct-lower-middle-mos-revision-v2/human-review-v2.json)、[当前分项状态](../../benchmarks/ct-lower-middle-mos-revision-v2/scoped-acceptance-v2.json)、[验收锁定](../../benchmarks/ct-lower-middle-mos-revision-v2/acceptance-v1.json)。本轮要求审批已清零；模型、来源和几何均不重算。上文待审描述保留为生成时状态。C/D显示三排与边列、F双孔相对位置已获认可；精确原图定位估计仍保持估计身份。143橙框及C红叉非孔裁决继续有效。

当前无必须新增的人工作业。全幅仍需覆盖盘点：当前695个POLY材料对象中，286有直接CT承载ID引用，409未见直接引用；共栅/子对象别名、碎片、特殊结构和旧网络不能据此直接算漏检。[覆盖审计](../../benchmarks/ct-lower-middle-mos-revision-v2/full-frame-coverage-audit-v1.json)保存逐对象清单。应先由Agent复核上方其他密集小MOS、下部/边缘部分组及环的覆盖，再形成整批候选；不请用户重审当前C/D/F或逐孔裁决四条已有单栅CT的精确数量。

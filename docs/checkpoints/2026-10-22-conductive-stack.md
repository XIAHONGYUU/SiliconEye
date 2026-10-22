# 第一份连续五层联合中样

2026-10-22。用户批准统一金属／Via接口并生成连续五层联合中样。本轮接续已审J1/J2及K1，不新增器件或网络判断。

[交互复核页](../assets/conductive-stack-v1/index.html)、[统一数据](../assets/conductive-stack-v1/model.json)、[共同快照v4](../../configs/joint-work-layer-v4.json)、[可复跑输入](../../benchmarks/conductive-stack-v1/request-v1.json)、[读取接口](../architecture/conductive-layer-interface-v1.md)。

## 交付

共同设计画布5860×4587，显示窗口仅用于检查，不改变长线／对象的空间范围。22个记录：M1九条、V1九个候选孔、M2一条、V2一个支持区、M3两条。M2-J01去重后连接两组接口；M1-P08原接续片原样合成，其他M1保持原几何；B0及其他邻线仅为隔离上下文。

连续链为**M1-P08 → V1组 → M2-J01 → J-M2-EDGE-V2 → M3-J-B1**，两处接入均来自已有人工裁决，新增物理连接判断为0。源图分别保留M1／M2／M3原生坐标，提供宽上下文、4倍局部和原图／标记切换；统一几何支持五层及AA／POLY／CT背景切换，编号表可突出显示对象。

模型保留原编号、原记录、源图与包哈希、观察、几何候选状态和出窗未知。注册表接入`joint_layers`共同快照及`layer_review`读取／显示接口，支持重新加载、联合检查与保存；不再只是将两张图拼在一页。

## 验证及限制

[最终验证](../../benchmarks/conductive-stack-v1/verification-v1.json)记录相关测试、共同快照真实加载／保存／复核、图页核验及六份旧包回放。原材料AA334／POLY696／CT10287与所有六处来源／接入限制保持。原模型／图片／裁决不改写。

局部接口已审与几何边界候选分开。V2支持区不是实测单孔，9个V1孔形也不等于9个逐孔人工测量；物理完整孔数null。没有独立合格精确投影、真实工艺标尺或PDK DRC。M2／M3出窗未知、其余分支未查完，不称全网点亮，不新增自动网表边。

## 恢复

```bash
.venv/bin/python -m silicon_eye.conductive_layers \
  --request benchmarks/conductive-stack-v1/request-v1.json \
  --output runs/新的五层中样目录
.venv/bin/python -m silicon_eye.joint_layers \
  --snapshot configs/joint-work-layer-v4.json --output runs/新的共同层检查目录
```

下一步是在该模型中验证新增的真实分支／隔离，尤其高层金属与多根下层金属的接口遍历；复用旧结论，只提交新增歧义。未在本轮扩全幅、追完整网络或封装通用skill，未推送GitHub。

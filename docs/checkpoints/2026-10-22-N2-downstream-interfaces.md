# N2向下追踪：端部D1

用户要求沿N2的M2向下检查其余接口并生成结果。[复核页](../assets/n2-downstream-interfaces-v1/index.html)、[事前AI观察](../../benchmarks/n2-downstream-interfaces-v1/initial-ai-observation-v1.json)、[请求](../../benchmarks/n2-downstream-interfaces-v1/request-v1.json)、[核验](../../benchmarks/n2-downstream-interfaces-v1/verification-v1.json)。

## 结果及待审

- 起点N2经V2接B1的已审关系保留。本轮R1观察认为同一窄M2沿照片中轻微倾斜连续到约(1526,2795)的可见下端。没有连接到右侧另一根宽M2，也不沿空白向下补线。
- 下端D1的M2观察窗[1508,2705,1543,2802]内有规则孔阵列，初判V2。M3候选为紫色L1宽横母线；上方黄色H1细线为对照。多行孔组需要足够的承载面积，宽母线是更合理的结构解释；这是定性先验，不是标定后的包围测量或真实PDK DRC。
- M3的D1承载观察窗[1470,2740,1590,2835]不是V2孔坐标；不强行叠图、不借用已撤回的9对跨Via坐标。L1是新局部标签，不自动与B1或历史同名对象合并。
- 中段S1未找到足够清楚的其他V2组；这不证明没有弱小接口，更不代表所有接口完整。
- M1的U1上部交汇、U2中部交叉、U3下部宽M1交汇保持未知。没有合格M1↔M2对应，不能因相近或交叠就将其作为N2的V1落点；也没有宣称无V1。这些是独立观察窗，不改动共同层的六处既有未知。

只提交两项新增裁决：R1连续且在下端收口；D1为V2并接L1宽M3而非H1细线。M1三处不强迫判断，先保留未知；N2上端不重审。孔数、精确几何及L1全部其他分支未知，没有整网完成结论。

复核页含M2／M3完整可见路径与4倍宽局部，M1可切换显示，另提供明确标为关系示意的SVG。复用`metal_via_pilot.source_panels`；未新增案例脚本、提取算法或共同几何。当前v5及33条导体、AA/POLY/CT保持，自动网表边仍空。事前评价真值为null，尚无新已审接口。

## 证据图恢复

在项目虚拟环境中用已有API读取请求，再调用`source_panels`：

```python
from pathlib import Path
import json
from silicon_eye.joint_layers import load_snapshot
from silicon_eye.metal_via_pilot import source_panels
root = Path.cwd()
request = json.loads((root / 'benchmarks/n2-downstream-interfaces-v1/request-v1.json').read_text())
snapshot = load_snapshot(root, root / request['snapshot']['path'])
output = root / 'runs/新的N2向下证据目录'
output.mkdir()
source_panels(root, snapshot['manifest'], request, output, frames=('m1', 'm2', 'm3'))
```

只复跑证据图片，不生成批准或网络。页面为本地静态审阅稿；未验证浏览器交互，不声称已完成投影配准。

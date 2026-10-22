# N2：B1旁相邻M2接口检查

用户要求先核V2身份，再判断B1／B0承载。[原生证据页](../assets/b1-neighbor-interface-v1/index.html)、[裁决前观察](../../benchmarks/b1-neighbor-interface-v1/initial-ai-observation-v1.json)、[请求](../../benchmarks/b1-neighbor-interface-v1/request-v1.json)、[核验](../../benchmarks/b1-neighbor-interface-v1/verification-v1.json)。

AI初判为`M2-N2-LEFT-RAIL → V2-N2-GROUP → M3-J-B1`。左侧窄M2上端有规则孔阵列，观察窗口[1480,1903,1518,1959]。孔证据只取M2；不把M3的亮纹当V2，不借M1的V1或撤回的9对对应点。

承载判断使用两个方面：N2与已审J01的孔组在M2照片中处于相近的端部行列；M3的B1宽母线在两个位置之间连续，B0是其上方细线。此为宏观相对对应的AI判断，不能替代独立精确配准，也不能从J01的批准推导N2自动批准。M3橙框[1460,1945,1540,1995]仅作承载检查窗，不是观察到的V2孔坐标。

只提交一个新增接口问题：橙框N2是否为V2，并把左侧窄M2接到B1而非B0。孔数及精确边界仍未知，不要求逐孔批准；B0本处接入依据不足也不表示全局不同网。

本轮复用`metal_via_pilot.source_panels`生成两层宽原图、4倍宽局部及定位图，沿用原图／标记切换脚本。没有新案例脚本、模型重提取或算法修改。证据页的两层使用各自原生坐标，不作未核准的叠图。当前v5及原33条导体、AA/POLY/CT及六处未知保持；无新已审连接／自动网表边。裁决前评价真值保持null。

本地证据裁片可用现有API复跑到新目录：

```python
from pathlib import Path
import json
from silicon_eye.joint_layers import load_snapshot
from silicon_eye.metal_via_pilot import source_panels
root = Path.cwd()
request = json.loads((root / 'benchmarks/b1-neighbor-interface-v1/request-v1.json').read_text())
snapshot = load_snapshot(root, root / request['snapshot']['path'])
output = root / 'runs/新的N2原生证据目录'
output.mkdir()  # 必须新目录，禁止覆盖
source_panels(root, snapshot['manifest'], request, output, frames=('m2', 'm3'))
```

这是证据图复跑，不生成批准记录、共同几何或新网表。现有页面作为静态审阅稿保存。下一步只等待N2裁决，随后对照本次事前观察记录正确／修订情况。

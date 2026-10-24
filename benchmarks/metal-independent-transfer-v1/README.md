# 独立区域工具迁移样本

`request-v1.json`是新的空间区域、金属片段及接口支持区候选；`initial-ai-observation-v1.json`保留送审前判断。当前人工结果读取`reviewed-state-v2.json`与`evaluation-reviewed-v2.json`，不要将旧的null或原页面当成最新结论。

本轮直接复用了项目现有函数，未新增案例生产脚本。统一`conductive_medium` CLI暂不接受未审接口，不能将此请求硬塞到已审接口清单或声称同一CLI完整迁移。

可在内层仓库复核几何与包围（项目`.venv`）：

```python
import json
from pathlib import Path
from silicon_eye.metal_reconstruction import geometry_audit
from silicon_eye.metal_via_pilot import interface_audit
from silicon_eye.conductive_medium import source_order_audit

r = json.loads(Path('benchmarks/metal-independent-transfer-v1/request-v1.json').read_text())
polygons = {}
for layer, features in r['features_by_layer'].items():
    audit, shapes = geometry_audit(features, r['metal_budget'], r['canvas_wh'])
    assert audit['status'] == 'PASS'
    polygons.update({f['id']: p for f, p in zip(features, shapes, strict=True)})
for c in r['interfaces']:
    audit = interface_audit([c], polygons[c['lower_metal_id']], polygons[c['upper_metal_id']],
                            r['via_budget'],
                            layer_stack=(c['layer_pair'][0], c['layer'], c['layer_pair'][1]))
    assert audit['status'] == 'PASS'
assert source_order_audit(r['features_by_layer'], r['source_order_checks'])['status'] == 'PASS'
```

来源门使用`source_identity_audit`，参数来自候选模型的来源观察及共同快照的已审来源策略。复核图参数在`source_panels`，可用`metal_via_pilot.source_panels`写到新的本地目录，原照片不改。软件PASS不代表Q1或全部真实接入已正确。

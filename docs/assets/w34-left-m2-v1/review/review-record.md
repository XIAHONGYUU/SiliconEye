# 验收确认记录

- 送审包：W34-LEFT-M2-20261105-V1
- 阶段：金属（METAL）
- 日期：2026-11-05
- 送审版本：0bb2cde885f74ee0aa03f9e086b65c5b
- 范围：m2 原生窗口 [180, 1680, 280, 2410]

## 逐项确认

| 项目 | 类型 | 结论 | 检查 | 备注 |
| --- | --- | --- | --- | --- |
| L01：左侧细 M2 整段几何（G1） | metal_fragment | 通过 | 整段走向、上端位置及向左回折合理=是；与邻线保持间隙，没有误连=是 | — |
| I1：M2短头亮点是否为 V2（I1） | via_interface | 通过 | 在M2短头可辨认V2，而非仅有金属边缘或拍屏纹理=是 | — |

## 未批准边界

- I1接哪条M3、完整孔组包围或新电气连接
- 物理孔数/孔径/节距、精确投影或真实工艺尺寸
- PDK DRC、共同GDS采用、全幅完成或完整网表
- L01上端无孔或电气终止结论

## 来源绑定

- submitted_package：docs/assets/w34-left-m2-v1/review · f3e4c11032ffa29c12016687a7e67e940b80a0b34ade3b2768962ce9e31edfde
- submitted_page：docs/assets/w34-left-m2-v1/review/index.html · 5b3962efb8957eee3e17c2e87e63862f7b4471e3701b943871c33d5c3b977e63
- submitted_spec：docs/assets/w34-left-m2-v1/review/review-spec.json · ce38080310959835a8bab4bf01e616f0a636b5b1c1706db4e6369525269faee9

## 声明

本记录只记录对送审内容的判断，不自动批准精确尺寸、物理孔数、PDK/DRC、完整网表或共同几何采用。

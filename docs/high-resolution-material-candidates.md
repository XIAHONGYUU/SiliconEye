# 高清SEM与模拟照片候选筛选 v1

2026-10-15。用户已授权多Agent筛选；三条只读支线（模拟SEM、模拟光学、现代混合信号模拟区）均已返回。主Agent独立下载、解码及目视核查，最终取得五组候选。候选不等于可直接训练或通过材料验收。

## 结论

未找到同时满足真实SEM、模拟MOS区域、清楚独立AA/poly/CT、同颗多阶段、可直接下载的完整公开栈。避免继续将旧模糊图片或高清表面照片当作完整替代。

- AD9361提供现代模拟FET去金属局部，但原生细节仍有光学模糊；适合结构参考，不是CT精确真值。
- MCP6V27和U1001C原图分辨率更高、图面相对清楚，但金属遮挡底层；只有表面状态。
- emsec真实SEM图与用户灰度/亮点外观较接近，但内容是金属/via，不是AA/poly，未证明是模拟区。
- STM32L431南侧模拟区具有同颗逐步去层来源，高倍图库是值得继续取得的线索；文章版局部细节不足，图库403受限。

## 实际取得的五组

| ID | 候选 | 原图px | 成像/状态 | 许可 |
|---|---|---|---|---|
| A | [AD9361 analog FET region](https://zeptobars.com/en/read/AD9361-SDR-Analog-Devices-DAC-ADC-65nm) | 2997×2184 | optical; after metallization etch; isolated AA/poly/CT masks unavailable | CC BY 3.0 |
| B | [ZMD U1001C CMOS speech-band filter](https://zeptobars.com/en/read/ZMD-U1001C-CMOS-speech-band-filter) | 5576×3267 | optical; surface, metal present; no multi-stage stack documented | CC BY 3.0 |
| C | [real metal-layer SEM excerpt](https://github.com/emsec/unsupervised-ic-sem-segmentation) | 4096×3536 | SEM; metal layer; not AA/poly/CT | CC BY 4.0 |
| D | [STM32L431 south analog region](https://serd.es/2025/01/02/STM32L431-teardown.html) | 4096×4071 | optical; substrate floorplan; article version, high-magnification stack not obtained | article CC BY-SA 4.0; gallery images separately attributed |
| E | [Microchip MCP6V27 auto-zero CMOS opamp](https://zeptobars.com/en/read/Microchip-MCP6V27-opamp-auto-zero-input-offset) | 7440×7104 | optical; surface, metal present; no separated AA/poly/CT stack | CC BY 3.0 |

Zeptobars三组图片授权依据：[作者版权说明](https://zeptobars.com/en/about-us)，CC BY 3.0。SEM图片许可依据作者GitHub README，CC BY 4.0。STM32文章图与图库分别核实，不能互相套用许可。

下载文件、来源URL、SHA-256、尺寸和原生裁剪坐标见本机`runs/high-resolution-material-search-v1/manifest.json`。五组原图均完整解码，五处ROI均与源窗口逐像素一致。浏览总览缩放，不用于量测；原生ROI无放大锐化或补图。

## 局部检查包

- A：`ad9361-native-roi.png`；源图xywh=[1550, 650, 1000, 800]，原点左上，单位源像素。
  来源原图：[下载入口](https://s.zeptobars.com/AD9361BBCZ-Si-3-HD.jpg)。
- B：`u1001c-native-roi.png`；源图xywh=[1600, 1000, 1000, 800]，原点左上，单位源像素。
  来源原图：[下载入口](https://s.zeptobars.com/ZMD-U1001C-HD.jpg)。
- C：`sem-native-roi.png`；源图xywh=[1000, 800, 1000, 800]，原点左上，单位源像素。
  来源原图：[下载入口](https://raw.githubusercontent.com/emsec/unsupervised-ic-sem-segmentation/main/dataset/sems/sem0000.png)。
- D：`stm32-analog-roi.png`；源图xywh=[275, 2750, 1250, 750]，原点左上，单位源像素。
  来源原图：[下载入口](https://serd.es/assets/stm32l431-floorplan.jpg)。
- E：`mcp6v27-native-roi.png`；源图xywh=[3000, 1900, 1000, 800]，原点左上，单位源像素。
  来源原图：[下载入口](https://s.zeptobars.com/MCP6V27-HD.jpg)。

本机总览`candidate-contact-sheet.png`；建议先打开原生ROI评价可见性。每组尺寸不同，不以相同显示大小推断物理尺度相同。

## 保留线索与排除项

- [Cypress CY8C4245AXI](https://siliconpr0n.org/archive/doku.php?id=azonenberg%3Acypress%3Acy8c4245axi)：作者记录130nm及active area SEM，“Analog block. Comparator?”带问号，模拟功能未确认；原站403，未下载核验，不能列作已获得样本。
- [STM32L431高倍逐层图库](https://siliconpr0n.org/map/st/stm32l431/)：正常访问403，未绕过。支线读取索引记载100x图37050×36722，但主Agent未获得该图，不宣称实测尺寸或清晰度。
- LH0042CH虽有SEM，但老BJT/JFET混合结构，与MOS材料分层目标不一致，排除优先组。
- REFICS是合成SEM，不作为真实制样照片替代。
- IOActive有SEM/光学同区域解释材料，但网站声明保留版权并限制未经同意使用；本轮仅作阅读来源，不下载进入检查数据集。

## 输入条件已确认与后续方向

2026-10-15用户明确：八层照片是光学显微镜成像，后由用户手拍拍屏；设备原始导出图无法取得。因此不再把索取原图作为下一步或前置条件。

主基准改为公开高清光学模拟去层照片；SEM只作辅助，不默认其灰度/亮度/边缘能直接迁移到光学照片。继续筛选小规模CMOS模拟开关及有明确授权的光学多阶段样本，按局部AA/poly/接触的真实可辨性验收。

建立可用基准后，再设计拍屏失真验证：屏幕像素纹理、摩尔纹、模糊、倾斜等只能是明确标记的人工干扰实验，不能当作已测量的用户相机/屏幕模型；用户原图与公开照片保留各自独立来源，不相互冒充。

算法与既有AA/poly/CT基线未修改，未训练、未推送。

## 光学方向复筛补充

用户确认光学后拍屏条件后，新增CD4046BE三状态及AAT4292前后两状态并实际下载检查。当前优先级和证据以[两组光学去层筛选](optical-delayer-pairs.md)为准；既有五组保留作历史候选，不能继续将“未找到任何可下载模拟光学去层组”视为当前结果。

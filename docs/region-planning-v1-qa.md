# 区域规划 v1 图稿检查

NEEDS REVIEW

2026-10-18。依据 technical-infographic-qa 检查流程及区域 JSON 对照图稿；本报告不批准物理分类。

| ID | 严重性 | 类别 | 位置 | 观察 | 预期 | 证据 | 置信度 | 建议 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q01 | 待核覆盖 | HTML 运行 | 八帧选择/原尺寸打开按钮 | 静态结构与嵌图已检查，未运行浏览器交互 | 用户打开后可选择各帧并放大 | review.html 有 8 选项、8 张可解码图片、21 条区域表 | 高 | 优先用 PNG/区域表核对，HTML 交互可用性待使用时确认 |
| Q02 | 待核覆盖 | 物理分类 | 全部新区域，尤其 R01 | AI 候选尚无新人工批准 | 独立核查关键类别 | 区域 JSON 与表均保留 candidate/unknown | 高 | 首先核对 R01 电阻候选，不升级为确认 |

未发现已查看 PNG 中阻断阅读的 P0/P1 图稿缺陷。Q01/Q02 为未核覆盖，不作为已确认缺陷，也不转为物理 PASS。

| Gate | 状态 | 证据或限制 |
| --- | --- | --- |
| Artifact integrity | PASS | 四 PNG 可解码；HTML 八嵌图可解码；输出哈希见 artifacts-v1.json |
| Exact content | PASS | 21 区域 JSON/CSV/HTML 编号顺序一致，58 原生检查窗均在 5712×4284 内；来源/引用检查通过 |
| Technical relationships | PASS（表示范围） | 各帧独立画框，未画跨层投影或新增电气边；不表示物理分类通过 |
| Typography and layout | PASS（四 PNG） | 查看 poly/AA/M1/M3 标题、图例、标签与边框，无发现标签相互遮挡或标题溢出；HTML 未渲染 |
| Readability | PASS（原尺寸 PNG） | 1714×1422 图稿可读取标签；较小窗口需打开原尺寸 |
| Reference isolation | 不适用 | 新建候选，不承诺修改旧图；原始照片字节哈希未变 |
| Provenance and release | PASS（候选身份） | v1 候选有唯一文件清单与哈希，不标为最终批准；从源图直接缩放后绘框 |

阻断图稿缺陷：未发现。未完成：浏览器交互、区域物理分类。下一步：用户打开区域图，对主要类别及 R01 作重点核查；M05 既有 Q1/Q2 子区随后用于分层样稿。

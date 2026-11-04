# 固定验收确认单协议 v1

## 目的

过去每次人审都由当轮临时生成页面、问题和答案字段，AA、POLY、CT、金属各阶段的确认格式不同。本协议把“送审页面 + 人审判定 + 归档记录”固定为一套可复用工具：

- 同一个 HTML 模板和同一套分区顺序；
- 同一组结论词表：通过、需修改、不确定、不适用；旧批准与上下文可设为只读参考；
- 同一个答案 JSON 结构和归档文件名；
- 同一套来源哈希、必答项、必查项和边界确认；
- 阶段差异只体现在预设问题、检查项和边界文本，不改变页面骨架。

工具只渲染送审方声明的证据并记录人的判断。它不做图像识别、配准、几何生成、连接推断，也不自动批准任何物理事实。

## 固定产物

一次送审固定生成以下文件：

    review-spec.json      规范化的送审定义（输入）
    index.html            固定验收确认页
    manifest.json         构建版本、页面/定义/资源哈希
    review-decision.json  人审回传（下载后校验归档）
    review-record.md      人审可读记录（归档时生成）

固定命名意味着下一次对话、下一轮补建和不同层级的复核都使用同一套入口，不再各自发明确认文件。

## 固定结论词表

| 值 | 页面文字 | 含义 |
| --- | --- | --- |
| accepted | 通过 | 本项声明内容在本确认单范围内合理 |
| needs_revision | 需修改 | 本项存在需要修订的具体问题，必须写备注 |
| uncertain | 不确定 | 证据不足或存在替代解释，不当作通过 |
| not_applicable | 不适用 | 本项不属于本轮判断范围 |

整体问题只使用前三项。逐项“通过”还要求所有带“必查”的检查项为真；未勾选必查项时页面和校验命令都会拒绝通过。整体问题判“通过”时，其覆盖项不能未答、为“需修改”或“不确定”，且至少有一项适用并通过；页面和校验命令都会拒绝这种自相矛盾的记录。至少勾选“我已阅读并理解范围与未批准边界”后才能导出正式 JSON。

## 页面固定分区

所有阶段使用同一顺序：

1. 总览：包编号、阶段、原生范围、日期、数量、使用步骤、结论图例、来源绑定。
2. 逐项确认：左侧索引、搜索和筛选；右侧优先显示本轮变化与大图切换，坐标和路径折叠。参考项只读，其余项有必查、结论和备注。
3. 整体问题：把逐项结论汇总成 Q1/Q2/Q3 的整组判断，附覆盖项跳转。
4. 边界与未批准：本确认单的限制、明确不批准的清单、边界确认勾选。
5. 导出：总体意见、JSON 预览、下载/复制按钮、归档命令。

页面底部固定显示必答进度和导出按钮；答案尝试暂存在浏览器本地，按送审版本 build_id 隔离；页面显示保存状态。存储不可用时明确提示，可下载草稿文件。只有下载出的 review-decision.json 才是正式回传。

## 阶段预设

预设命令：

    python -m silicon_eye.review_sheet preset --stage METAL

| 阶段 | 主要项目类型 | 默认整体问题 | 默认必查示例 |
| --- | --- | --- | --- |
| AA | aa_polygon | Q1 形状/台阶/间隙；Q2 可见片段无明显遗漏 | 形状、间隙、无漏段 |
| POLY | poly_fragment | Q1 走向/转折/相对宽度/AA 关系；Q2 无明显遗漏 | 走向、相对宽度、AA 关系、无漏段 |
| CT | ct_array | Q1 行列/节距/覆盖；Q2 无遗漏（不把未检出当不存在） | 阵列规律、覆盖、上下关系 |
| METAL | metal_fragment、via_interface | Q1 无漏段；Q2 可见片段/端点/细支路无遗漏；有孔组时 Q3 身份/层对/承载 | 端点状态、无漏段、原生路径；孔可见、层对、上下承载 |
| VIA | via_interface | Q1 身份/层对/承载；Q2 孔组落点/上下金属相对位置，不要求逐孔计数 | 孔可见、层对、上下承载 |
| REGION | region_boundary | Q1 边界覆盖/出口状态；Q2 适合作下一轮固定范围 | 覆盖可见结构、出口状态 |

如果送审定义显式提供 questions，则使用显式问题；否则按项目和预设自动生成。METAL 的 Q3 只在存在 via_interface 项目时出现。每个阶段有默认限制和“不批准”文本，送审方可覆盖，但页面结构不变。

## 命令

模块入口和 silicon-eye 子命令等价：

    python -m silicon_eye.review_sheet build --spec configs/review-sheet-demo-m2.json --output runs/review-sheet-demo-m2-v1
    python -m silicon_eye.review_sheet check --package runs/review-sheet-demo-m2-v1 --decision ~/Downloads/review-decision.json --archive
    python -m silicon_eye.review_sheet preset --stage AA

    silicon-eye review build --spec ... --output ...
    silicon-eye review check --package ... --decision ... --archive
    silicon-eye review preset --stage METAL

build 的约束：

- 输出目录必须新且位于项目根目录内；已存在目录不覆盖。
- 证据图必须位于项目根目录内且可读；按 SHA256 复制到输出资源的 assets/ 下。
- 生成 manifest 时记录页面、规范化定义、模板、代码和每个资源的哈希。
- 生成后临时目录原子重命名为目标目录，失败不留下半成品。

check 的约束：

- 校验页、定义和资源哈希没有变化；页面被改动则拒绝。
- 校验 build_id、package_id、stage、actor=human、日期和边界确认。
- 必答项和必答整体问题必须齐备；未知/重复 ID 拒绝。
- 逐项结论必须在固定词表内；通过时必查项必须为真；需修改时备注非空。
- archive 写入 review-decision.json 和 review-record.md；已有不同记录时拒绝覆盖，相同记录幂等。

## 送审定义

最小结构如下（完整示例见 configs/review-sheet-demo-m2.json）：

    {
      "schema_version": 1,
      "kind": "silicon_eye_review_sheet",
      "stage": "METAL",
      "package_id": "M2-W34-SOURCE-REVIEW-V1",
      "title": "W3/W4 邻近 M2 来源清单确认",
      "date": "2026-11-03",
      "summary": "本批只判断声明窗口内的 M2 片段与接口。",
      "scope": {
        "frame": "m2",
        "native_bounds": [280, 1870, 850, 2840],
        "note": "固定原生窗口；范围出口不是物理终点。"
      },
      "items": [
        {
          "id": "M2-W3",
          "type": "metal_fragment",
          "title": "W3 M2 主干",
          "prompt": "该片段几何是否合理，端点状态是否正确？",
          "facts": {"模型 ID": "WEST-M2-W3-SOURCE"},
          "evidence": [
            {"path": "docs/assets/west-w34-reviewed-v9/west-m2-wide-marked.png", "label": "M2 宽图", "role": "marked"}
          ]
        }
      ],
      "sources": {
        "reference_model": {"path": "benchmarks/west-w34-reviewed-v9/S3-W34-metal/model.json", "sha256": "<sha256>"}
      }
    }

字段约定：

- stage 为 AA、POLY、CT、METAL、VIA、REGION、OTHER。
- items 非空；每项必须有 id、type、prompt；required 默认 true；review_mode=context 时默认 false，不能设为 true。
- evidence 只接受项目内图片；role 为 source、marked、design、paired、overlay、detail、other；frame 可声明来源帧或 design。跨层并列图用 paired，保持独立坐标；overlay 只用于已有配准依据的叠加图，工具不代为验证配准。
- checks 省略时使用阶段预设；显式给出时完全按定义使用，可写空列表。
- note_required_on 默认 ["needs_revision", "not_applicable"]；可加入 not_applicable 等。
- questions 可省略；显式给出时每项用 item_ids 或 item_types 指定覆盖范围。
- limits、not_approved 省略时使用预设；显式空列表表示没有额外文本。
- sources 是额外证据绑定；每项必须给 path 和 sha256，构建时校验。

## 人审闭环

1. AI 依据当前工作模型、来源观察和证据，写出 review-spec.json；证据图可以是已有标记图、放大图或规则图。
2. 工具构建固定页面；AI 只报告页面路径、范围和未批准边界，不把构建成功说成人审通过。
3. 人打开 index.html，查看本轮变化并逐项判断；可用“本项必查均确认，通过并下一项”明确确认当前项，或分别选结论、勾检查。随后核对整体问题与边界，点击导出得到 review-decision.json。
4. 人或 AI 运行 check --archive，校验通过后 review-decision.json 与 review-record.md 成为本轮固定记录。
5. 后续接续只引用该归档记录和 manifest 哈希；聊天中的口头“通过”不能替代归档。
6. 旧 human-review.json 不改写、不重解释；新批次从本协议 v1 开始使用固定格式。

## 不做什么

- 不从页面选择自动生成或修改几何、孔数、承载或网表。
- 不用页面重叠推导连接，不把配准算法返回 success 当作真实对应。
- 不把“通过”当作物理孔数、精确尺寸、PDK/DRC 或全幅覆盖的批准。
- 不把 AI 未检出当作物理不存在；边界与未知继续保留。
- 不启动网络服务、不调用视觉模型、不发送数据到外部。

## 版本与扩展

schema_version=1 是当前固定契约。新增阶段或项目类型时：

- 在 STAGE_PRESETS 增加预设；
- 在 STAGE_PRESETS 的 checks 中增加项目类型检查；
- 加对应测试；
- 不 fork 页面模板，不改变既有 JSON 键名。

manifest 记录模板和代码哈希；旧送审包即使工具后续升级，也能按自己的 manifest 和归档记录复核。模板本身的视觉改动需要重新构建新包，不回头修改旧包。

## 示例

- 定义：configs/review-sheet-demo-m2.json
- 改版构建：runs/review-sheet-refined-v1/index.html（构建命令的输出目录必须新建）
- 示例明确标注“非送审”，不产生新的人审、几何或连接事实；只用于检查确认页、结论选择和导出格式。


## 2026-11-04：按真实审查工作方式使用

### 先组织本轮改动，再组织页面

- `items[].review_mode`：默认 `decision`。`context` 为只读参照，不要求作答，不进入整体问题或新答案；它本身不证明已获批准。旧批准仍须通过 sources 绑定原记录，不复制为新裁决。
- `items[].change_summary`：用一句话指出新增、局部修订或仅参考的内容；已有同 ID 几何修订应附新旧规则图。工具不修改几何，也不替送审方生成实际变化。
- `evidence[].frame`：标明 m1/m2/m3、aa/poly 或独立 design 坐标。图像切换保持各自完整视图，不自动套用其它帧的缩放或叠加。
- 自动预设问题排除 context；显式问题引用 context 会被拒绝。参考项获得新裁决时，服务端校验拒绝，避免重审旧批准。

### 一项只提一个必要判断

优先按连续来源清单、片段或接口组送审，不按每个实孔拆问。示例中的旧 W3/W4 V2 接口仅参考，待判项只剩演示 M2 几何。真正遇到新接口时，再分清孔身份与两侧承载；几何批准、连接批准、数量批准分别按实际送审内容记录。

送审方应准备能作判断的最小证据组合：

| 判断 | 至少准备 | 避免的问题 |
| --- | --- | --- |
| AA | 原图宽邻域、规则几何、相邻间隙 | 用CT亮点的中断替代AA环的连续性；合并相邻环 |
| POLY | POLY及AA上下文、规则联合图、端部引出 | 所有POLY都按栅处理；漏掉实际栅端引出 |
| CT | 真实来源侧、AA/POLY归属、相邻端子 | AA与POLY的CT混用；为孔数细节反复打断连接核查 |
| 金属几何 | 原图宽邻域、标记图、规则图，修订时有前后图 | 只给标记照片而没有可评审的重建几何；截窗太小 |
| VIA接口 | 对应的下层来源侧孔组、独立上层承载图，必要时联合规则图 | 用V1图充当V2证据；只凭上下投影重叠作连接结论 |

图像哈希保证文件绑定，不保证图中圈的是正确对象。本次修正的示例原先以 W3-N/W4-N 的 M1/M2 V1 对比图说明 W3-U/W4-U 的 M2/M3 V2；现已改为真实对应的 U 端证据，并将旧接口设为只读参照。

### 减少重复操作

- 默认打开逐项确认，以大图标签切换证据；需要同时看邻层时切换并排，左侧用当前标签、右侧单独选择一张对照图，避免把所有图缩成小格。放大窗口也能切图、缩放及拖动，切图重置视角，避免暗示未经验证的精确对应。
- 搜索编号或标题，筛选待完成／需修改／不确定／仅参考。下一个待完成项只寻找本轮必答，跳过参考项。
- 快捷通过是操作者明确声明“本项必查均已确认”，只填写当前项的必查与结论；不填写下一项或整体问题，不取消其它未知。
- “按已填逐项结论填写整体结论”仅在全部覆盖项记录完整时汇总尚未填写的问题。需修改优先，其次不确定；没有适用通过项时不会填成通过。已有整体结论保留，可手工修改。
- 进度按有效记录计算。通过但必查未齐、需修改但缺备注都仍是待完成；不确定是有效回答，完成记录不等于全部通过。
- 简明结论可复制回聊天供阅读，正式闭环仍使用固定 JSON 及 check；摘要会明确标出未完成草稿。

### 中断与恢复

可随时保存 `review-draft-包编号.json`，未完成也可保存；其 kind 为 `silicon_eye_review_draft`，不是人审确认。导入时同时匹配 build_id、包编号、阶段与 spec 哈希，拒绝异版、未知编号和非法检查值，再整体恢复。浏览器本地保存失败时可改用草稿文件；新 build 不自动继承旧草稿或旧批准。

新增字段保持 schema_version=1 的可选扩展，未使用这些字段的旧定义仍可构建；不回改旧包、旧裁决或 manifest。新校验补上“整体通过但覆盖项未答／全不适用”的拒绝规则，不倒写历史记录。

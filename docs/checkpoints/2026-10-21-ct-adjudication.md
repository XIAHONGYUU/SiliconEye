# Q1／Q2／Q3裁决执行：人审门关闭，整层仍待技术回查

[修订后复核页](../assets/ct-full-frame-adjudication-v2/index.html)提供修改前／后、规则联合图、原图及裁决标记切换。[裁决原文](../../benchmarks/ct-full-frame-adjudication-v2/human-review-v1.json)完整保留用户表述，原v1问题图、模型、观察和批准记录不覆盖。本轮没有请求重复审批，也未推送GitHub。

## 人工裁决与执行边界

| 项目 | 已确认语义 | 本轮执行 |
| --- | --- | --- |
| Q1 | 左侧四管下端栅CT；上方红X为环CT | 重查下端亮条，8个栅CT候选；恢复此前暂缓的16个源漏候选；不改四管数量与材料 |
| Q2 | 两条POLY共用下端引出，CT在连接处 | 新增G68-BOTTOM-BUS-01，共用端2个CT候选；原两指和全部AA保留 |
| Q3A | G为上端栅端，非下端引出；A是靠近栅极的内环 | A从外侧H2标记改对应H3；撤回P02下端2条未审CT；同组P01/P03经AI原图一致性复查另撤3条，未声称用户逐项批准这3条 |
| Q3B/C | G/A身份及对应正确 | 记录范围内的对应确认，保留已有对象 |

表中的孔数、精确坐标、正交连接外形均为AI测量／重建候选，不是用户逐像素标注。POLY共用连接不代表新M1/net已证实，也不据两指推断器件数或极性。

## 旧证据修订与防退化

Q1的反例揭示：G18-P03及G18-P07的5条旧CT取点误落在前一排器件亮条。独立按同组上端亮条复测后，只修订照片来源坐标和测量记录，CT的ID、目标、几何、数量、材料及原审批不变。每条在source_correspondence_history中追加完整before／after与裁决引用；同步更新native_center、source_native_center_xy以及新观察ID，保留旧原始观察供追溯。

现有ct_transfer受控局部修订入口新增单独的source_correspondence_corrections：必须列明允许ID、匹配原证据、记录原因和观察支持；不得通过普通几何修订顺带改来源，同一ID不允许同时删除／改几何和修来源。有限坐标、来源别名一致性、越权、旧父版本、重复对象和不支持的观察均有回归检查。

[保护检查](../../benchmarks/ct-full-frame-adjudication-v2/preservation-and-source-check-v1.json)：原7044条的几何和目标全保留，7039条完整记录相同，5条仅来源修正；原10004中9994条完整相同，5条未审CT撤回，5条仅来源修正。335 AA与原695 POLY完整相同，另加1个共用端POLY；新增26条CT候选，当前10025条工作记录。新／重定位观察与不同目标在3px内没有来源争用。数量均不是确认真实孔总数。

## 质量门与下一步

几何检查PASS：重叠0、孔距违规0、最小孔边距4.4相对px。原5px方孔、3px最小孔距、1px包围及沟道避让预算保持；共用POLY与两个原指均有正面积相接，CT受其包围。

人审门为PASS_Q1_Q2_Q3_scoped_decisions，pending_human_questions为空；整层保持HOLD_technical_source_path_reinspection、whole_frame_complete=false。旧版描述写7条暂缓路径，但锁定清单实际有8条，新版按真实清单修正数量，不改历史。不能因3处身份对应已确认就自动释放整段旧路径，也不把几何PASS当作全层通过。

唯一下一步：对这8条旧源路径独立重定位与回查，保留冻结基线及已审关系；有新歧义时才提出具体新问题，不再让用户重复回答Q1／Q2／Q3。不封装CT skill、不启动新增金属追踪，不宣称真实PDK DRC/LVS或完整网表。

## 验证与复现

- 全量454项测试通过（19.20s），相关Ruff及git diff --check通过。
- 新增来源修订回归覆盖历史保留、设计不变、授权范围、父证据过期、重复、非有限坐标、不支持的观察及来源坐标别名冲突；实际CLI对新冻结spec执行成功。
- v1锁定JSON和所有输入哈希保持，43条页面本地资源链接、SVG解析及PNG解码通过；Q1/Q2/Q3A新规则图及Q1/Q2原图标记已目视检查。浏览器真实渲染未自动实测。
- 复现：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-full-frame-adjudication-v2/spec-v1.json --output runs/新的裁决执行目录`；最终页面额外附有阶段状态、PNG备用及对照标记。provenance仅为审计配方，不是新增生产案例脚本或skill。

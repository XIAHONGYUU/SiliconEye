# 历史观察适配样例

`roi2-historical-observations-v1.json`依据以下既有记录转写，用于观察→case／材料卡→统一复核包的接口与使用体验核查：

- `../agent-eval/roi2-seed-v1/reference.json`：10条部分参考断言及逐条人工来源。
- `../block-roi2-material-support-reviewed-v2.json`：材料身份/大致位置与候选包络；仅用于选择有留白的观察窗口。
- `../review-package-roi2-v1.json`：既有case、宏观配准和材料复核输入。

purpose明确为historical_reexpression，model_id为null。没有新模型预测、没有新物理批准，不写入evaluation_runs或宣称识别准确率。运行方法及限制见`../../docs/observation-adapter-v1.md`。

# 上方40栅CT验收与T右端局部修订

用户批准T全部CT、L/M/R右侧30长栅源漏和下端栅CT、外围环及待查位置，并指出T右侧MOS的AA/POLY偏上。原话保存在[裁决](../../benchmarks/ct-upper-small-mos-reviewed-v2/human-review-v1.json)。

## 本次执行

- [新对照页](../assets/ct-upper-small-mos-reviewed-v2/index.html)保留同样T/L/M/R/上下环和纯原图/M1切换；T另有修订前模式。
- 右端小MOS按T最右器件解释：AA-F01669及SG-U06-010的设计几何下移7相对px。尺寸和横向位置不变；其2个上端栅CT随端部下移，4个源漏CT保持不动。原图坐标、观察框及亮峰证据不重写。
- 51个原橙框以human_confirmation纳入，algorithm_detected=false；原图定位只是原复核格点估计，不冒充逐像素人工标注或新测亮峰。
- 本批824个CT（原773＋51），完整模型2709孔；此前1885不重验。2656条原CT完整记录、335无关AA、694无关POLY保持一致。[逐对象前后台账](../../benchmarks/ct-upper-small-mos-reviewed-v2/ledger-v1.json)。
- [CT快照](../../benchmarks/ct-upper-small-mos-reviewed-v2/model-v1.json)、[有效材料快照](../../benchmarks/ct-upper-small-mos-reviewed-v2/material-model-v1.json)、[范围锁定](../../benchmarks/ct-upper-small-mos-reviewed-v2/acceptance-v1.json)。历史版本不覆盖。

## 验证与边界

2709孔整组质量门PASS：无重叠、无最小间距违规，材料包围与AA/POLY避让通过。439项全套测试、相关Ruff、源哈希、静态资源和模拟切换检查通过，T规则预览已目视核查。浏览器安全策略禁止file协议，因此本轮未做真实浏览器渲染，不绕过该限制。

不是实际工艺DRC；M1归属及网络仍未知。旧661环/电阻CT保留“连接基本通过、几何细节待优化”状态，不随本批升级。不宣称全幅CT已完成。

复现：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-upper-small-mos-reviewed-v2/spec-v1.json --output runs/新的上方CT已审目录`。

下一步沿既定顺序覆盖剩余左侧／左下大MOS，再处理中下部宽MOS和其他未覆盖环；每批先源漏、栅端和环联合自检，再整批提交审批，不重算本批已审对象。

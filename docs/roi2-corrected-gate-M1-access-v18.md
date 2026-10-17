# 真实gate长M2的M1接入高亮 v18

本轮按用户要求从M1的V1核查接入，不按M2端头列表宣告完整性。原图未修改。

|标号|当前判断|边界|
|---|---|---|
|M1-GATE|原共栅M1双横线，经右侧折返处V1接入当前长M2|已有接口事实，显示中心线不代表精确金属边界|
|M1-B|B经V1接M1已审；具体候选为约(2372,3885)起向右延伸的最下方M1长横线|候选落线及几何需整组核对；沿原生M1追至约(5104,3776)，右侧转角后的续段未追|

已有C/D局部对齐中，本轮用D显示gate与B落点。B端单独对照源图有一致的左端加宽区和M2覆盖，但不把这当作整片配准验收。全跨度投影仅用于搜索，不用于自动并网。上半段约(2323,2502)的V1样区域不在所选长M2覆盖处，未列为接入；不声称该邻线在全网中绝缘。

已扫描所选长M2对应M1的上下范围，但未以穷尽/无人审的空输出证明其他V1均不存在。目前只高亮有依据的两组，T和中间V2通往M3的目标仍待定位，旧A链共栅归属继续挂起。

- [原图/高亮总览](../runs/roi2-gate-M1-access-v18/M1-accesses-highlight-review.png)
- [原尺寸M1高亮](../runs/roi2-gate-M1-access-v18/M1-highlight-native.png)
- [Gate局部覆盖](../runs/roi2-gate-M1-access-v18/GATE-V1-M2-coverage-review.png)
- [B局部覆盖](../runs/roi2-gate-M1-access-v18/B-V1-M2-coverage-review.png)
- [源、坐标与边界记录](../benchmarks/metal-extension/roi2-corrected-gate-M1-access-candidates-v18.json)

验证：来源SHA-256、JSON可读、P1/P2未合并、图稿目视检查通过。未改生产代码，未新增全套测试，未推送。统一复盘留到追踪完成后。

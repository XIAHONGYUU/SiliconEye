# CT工作层全幅收口候选 v3

有效入口：model-v1.json＋stage-gate-v1.json＋review-questions-v1.json。最终状态HOLD，新增R1A/R1B/R2来源裁决待完成；旧Q1/Q2/Q3已关闭。freeze-manifest-v1.json冻结的是待审候选，不是已批准层。

10226条＝原10025－撤回33＋新增234，另5条只修正来源保留历史。原7044在v2中的记录与全部材料保持。8条旧轨迹逐项调查，但物理未知不等于已解决；20条旧候选保留处置证据，不自动释放。端口统计846区域中7无直接CT证据，不是7漏孔，内部扩散本来就可能不打孔。V3主体截段引用旧端子，不伪造新材料或孔。

生产执行复用：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-work-layer-closeout-v3/spec-v1.json --output runs/NEW_DIR`。CLI输出基础候选／几何／端口表；最终包装附全幅开关、源图问题、明确HOLD和冻结清单。provenance仅审计，不是新生产案例脚本或skill；不原地覆盖冻结版本。

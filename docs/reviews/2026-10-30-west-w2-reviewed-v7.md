# W2两端V2联合接续与M1/V1新接口

已保存本轮两条人审原话：“W2-U：是 V2，接 B-U”“W2-D：是 V2，接 B-D”，来源绑定原请求与原图。身份/承载批准不覆盖尺寸、数量或精密投影。新上端3×2、下端5×2为完整AI候选阵列，物理孔数仍未知。

[复核页](../assets/west-w2-reviewed-v7/index.html) · [五层切换](../assets/west-w2-reviewed-v7/S4-W2-interfaces/index.html) · [规则几何](../assets/west-w2-reviewed-v7/joint-work.png) · [唯一恢复请求](../../benchmarks/west-w2-reviewed-v7/next-request.json)。

通过四个独立事务：S1仅左扩视口450至[-1950,0,780,1440]，原点/尺度保持；S2只给RT-M3-UP、RT-M3-DOWN追加来源连续的西侧局部块；S3新增W2金属和来源清单；S4加入两处已审V2及完整候选阵列。现有37金属、20已审接口、125设计候选孔；旧18裁决与109孔边界/中心保持。旧金属骨架、宽度、原生锚点和旧局部块精确保留；M3原几何均被新几何包含。20组候选包围和间距通过，不是精密原图包围或真实PDK DRC验收。

继续查看M1源图，在W2相应位置，上横条的下突台阶N[1085,1898,1138,1948]、下宽横条S[1118,2688,1175,2735]各见待辨孔组。上下横条同帧连续至已建C-M1-SPINE的西侧横条，但经本处V1接W2尚未批准。已生成宽图、大邻域整数放大、较大标记和无标记切换；新V1仍是来源候选、未加入工作接口，不用M2的V2反充V1证据，也不桥接邻近细竖M1。

[W2-N上部两层](../assets/west-w2-reviewed-v7/W2-N-paired.png) · [W2-S下部两层](../assets/west-w2-reviewed-v7/W2-S-paired.png) · [来源观察](../../benchmarks/west-w2-reviewed-v7/W2-M1-source-observations.json) · [新裁决请求](../../benchmarks/west-w2-reviewed-v7/W2-V1-review-request.json)。下一步只判两处新V1身份/承载，不要求孔数，不重问W2 V2或旧W1/F1/N/Q1。

58项左扩视口、来源块、金属和接口扩展、原生裁决适配器测试通过。四事务/恢复精确回放、旧对象防退化、原图裁片逐像素、来源/资源/脚本/SVG/PNG核验见[verification](../../benchmarks/west-w2-reviewed-v7/verification.json)。浏览器交互未实测。程序未改，README/site的25文件和gh-pages保持，无提交/推送；skill仍LIMITED_TRIAL_V2，source_to_design_transform=null，geometry_adopted=false，net_edges=[]，complete_network=false。

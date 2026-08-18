# 主题遗漏候选 · 第二轮(2026-08-18,描述库反查)

**方法**:2,604 只 tradeable 票的 yfinance 业务描述 × 每个业务主题的关键词档(命名机制/产品,不用相邻概念),命中且不在名单的进候选池(28 主题 ~700 条),再由数据端按 `MEMBERSHIP_STANDARD` 四条判据逐条过。**关键词命中 ≠ 该在**——"space" 命中仓储 REIT,"uav" 命中 Duavee 药名,"gold" 命中 Goldman;这些不列。
**已直接做的**(按你既定规则"TSF 有我们没的加进去",上一轮漏了五个主题):Quantum +7(QNT INFQ HQ IQMX ALMU BTQ XNDU)· Gold Miners +20 · Defense +25(CACI LDOS SAIC BAH PSN PLTR BBAI ATI CRS BWXT RBC RGR SWBI POWW IRDM…)· Solar +9 · Clean Energy +44。
**下面是非 TSF 来源的候选,等你签**:✅ = 数据端建议加(主体业务就是它、定价跟主题);⚠️ = 相邻业务 / 稀释风险,你定。不列的都是不建议。

| 主题 | ✅ 建议加 | ⚠️ 存疑(理由) |
|---|---|---|
| AI - Datacenters | **PENG** $3.2B(Penguin Solutions,AI 基础设施/GPU 集群部署) | BTDR $2.5B(HPC 托管但盘面仍是加密,按"盘面压叙事"留 Crypto) |
| AI Power & Infrastructure | **FRMI** $3.9B(Fermi,给 AI 算力建吉瓦级私有电网,TSF 把它放 AI DC)· **EROC** $3.8B(分布式发电系统,TSF 亦放 AI DC) | RRX $11.6B(Regal Rexnord,ATS/开关柜只是一段)· GHM $1.4B(Graham,核电/海军真空设备) |
| Cybersecurity | — | AMTM $5.0B(Amentum,联邦 IT/网络安全——TSF 收了 CACI/LDOS/SAIC/BAH,同类) |
| Cloud Software | **ZETA** $7.2B(营销云 SaaS,TSF Software 有它) | QLYS · NTSK · RBRK · VRNS(都是 SaaS 但安全为主,已在 Cyber;要不要双挂) |
| Fintech | **GRAB** $14.6B(GrabPay/GrabFin,TSF 收了 SE 和 MELI,同逻辑) | FRHC $9.6B(Freedom Holding,券商+支付) |
| Homebuilders | **LEN** $20.8B(Lennar!TSF 名单写的是 LEN.B,我们池里是 LEN,漏了)· **QXO** $14.5B(Beacon 屋面建材分销,同 BLDR/UFPI)· **FOR** $1.5B(Forestar,给建商供地,DHI 子公司) | TGLS $1.8B(Tecnoglass 门窗)· HHH / JOE(社区开发商) |
| Medical Devices | — | WST $24.4B(West Pharma,药物递送组件,TSF 放 Healthcare) |
| Defense | (TSF 25 只已加) | ESE $8.0B(ESCO,海军/航空过滤)· TDY $31.4B(Teledyne 防务电子约一半)· OSK $9.5B(防务车辆是一段) |
| Robotics & Automation | — | RRX(自动化与运动控制段)· TNC $1.1B(Tennant 自主清洁机器人) |
| Physical AI & Humanoid | — | LSCC $18.8B(边缘 AI FPGA,TSF 收了 AMBA/INDI 同类)· TER $69B(Universal Robots 协作机器人,TSF 放 Robotics)· ARM(机器人是一小段) |
| Genomics | — | TECH $11.3B(Bio-Techne,细胞/基因治疗试剂)· RVTY $13B(Revvity 基因组学工作流)· AZTA $1.5B(GENEWIZ 多组学) |
| Uranium & Nuclear | **STDN** $2.1B(Standard Nuclear,先进核燃料——纯核) | — |
| Steel | **NWPX** $1.1B(钢管,原来在我们名单里,TSF 没有) | — |
| Crypto Equities | **XXI** $3.2B(Twenty One Capital,比特币金库) | STRC(Strategy 的优先股,不是普通股,不加) |
| Rare Earth Metals | — | ALM $4.7B(Almonty 钨,关键矿物但不是稀土;TSF 放 Metals & Mining)· PPTA $3.0B(Perpetua 金+锑,TSF 稀土表有 UAMY/NB 这种锑/铌,同逻辑) |
| Clean Energy | **AES** $10.5B(可再生开发商) | — |
| Solar | **TE** $1.4B(T1 Energy 光伏组件制造,TSF 放 Clean Energy) | — |
| Drones | — | AXON $49B(Skydio/Dedrone 无人机与反无人机,但主业是 TASER/体感摄像;稀释) |
| Memory & Storage | — | MRVL $205B(存储控制器是一段;稀释)· ALAB(CXL 内存互连) |
| Semis Broad / Optics / Silver / Copper / Coal / Lithium / Space | — | 无值得加的:命中的是分销商、次要段或大票稀释(NEM/AEM 的银副产、TTE/BP 的可再生段、NOC/RTX 的太空段) |

**你签完我做的**:✅ 进 `extra`(note 记 "候选反查 2026-08-18 Andy 签"),⚠️ 你勾哪个加哪个;然后 verify_members + build + validate。

# 主题分类审计 · 2026-08-18(第一轮)

**判据**:`pipeline/themes/MEMBERSHIP_STANDARD.md`(收入 ≥30% / 定价跟主题走 / 稀释:市值 > 主题中位 20× 且成员 <15 不进 / 流动性 $3 亿 + $200 万);业务主题必须答得出「同时变好变坏的共同原因」;因子主题不适用共同原因判据;proxy 只问「这基金是不是你实际买的」;叙事定候选、**盘面定成员**。
**范围**:Andy 08-18 定的:① 分类对不对(什么算主题) ② proxy 16 个不优先 ③ 有个股的 52 个逐个核成员和遗漏。
**数据**:`data/output/groups.json`(08-17 bar)+ `theme_review.md`(成员来源)+ `theme_verification.md`(223 手写成员的描述关键词校验:PASS 79 / FLAG 2 = IBM、ABT)。
**结论标签**:✅ 通过 · ⚠️ 成员要改 · ❌ 概念/名字有问题 · 🏷 是板块桶不是主题(产品决定要不要单列)。

---

## 一、分类层面(什么算主题)

75 个 = industry 28 + etf 24 + proxy 16 + rule 8。

**rule 8 个(Growth / Value / High Beta / Small Caps / Mega Caps / IPOs / High Octane / 52-Week High Leaders)**:标准里明确是"因子主题",按属性定义,有意保留。Small Caps 不是"主题"是**因子**——分类没错,是**要不要和业务主题混在一页**的产品问题。**建议**:数据端给每个主题加 `kind ∈ {theme, sector, factor, proxy}`,前端分组摆放;不删。

**🏷 板块桶(industry 联合、成员 60–185)**:Software 185 · Regional Banks 155 · Oil & Gas 152 · Financials 143 · Industrials 134 · Real Estate 126 · Energy 99 · Insurance 85 · Utilities 80 · Semiconductors Broad 74 · Travel & Leisure 69 · Consumer Retail 61 · Chemicals & Materials 53。这些是 TSF 的"板块视图",共同原因是**宏观**(利率/油价/资本开支周期),不是产业叙事。它们的四态读数有用(板块轮动),但和 Drones/Uranium 放同一栏会让"主题"这个词失焦。**建议 `kind: sector`**,不删。其中两处**重叠要处理**:
- **Energy(99)⊂ Oil & Gas(152)+ Uranium + Solar + Coal**:Energy 把 E&P/Midstream 又数了一遍,还把铀/光伏/煤塞进来(它们各有自己的主题)。**建议删 Energy** 或改成 proxy XLE(你实际买的是 XLE)。
- **Fintech(37)⊂ Financials(143)**:见下,Fintech 现在的成员根本不是 fintech。

---

## 二、逐主题(etf 24 + industry 28,按问题大小排)

### ❌ 名不副实 / 概念要重定

| 主题 | 问题 | 建议 |
|---|---|---|
| **AI Power & Infrastructure**(44) | 成员 = Utilities-Regulated + IPP 全部,含 HE(夏威夷电力)、CIG/ENIC/CEPU(拉美电力)——和 AI 无关;和 Utilities(80)重叠 100% | 改成手写名单:与数据中心供电直接相关的 IPP/核电/电力设备——VST CEG TLN NRG OKLO SMR NNE BWXT GEV BE VRT PWR;或删掉(AI-Datacenters 已覆盖 GEV/VST/CEG/TLN/PWR/VRT) |
| **Fintech**(37) | 成员 = Credit Services + 交易所/评级(CME ICE NDAQ CBOE SPGI MCO MSCI FDS TRU MORN)——交易所和评级机构不是 fintech;真 fintech(SOFI AFRM UPST HOOD TOST XYZ PYPL SEZL KLAR NU PAGS STNE DLO FOUR FLYW PAYO MQ DAVE)散在 Software / Capital Markets / Credit 里 | 改手写名单;删 industry 映射 |
| **Speculative Tech**(14) | = ARKK+ARKF 前几大持仓:AMZN 2.8T、TSLA、AMD、PLTR、SPCX——"ARK 的持仓"是名单不是主题;稀释判据全违反 | 按标准 proxy 规则改成 **proxy ARKK**(你会买的就是 ARKK) |
| **Genomics**(41) | ARKG 伞:mRNA 疫苗(MRNA BNTX)+ RNAi/反义(ALNY IONS)+ 基因编辑(CRSP NTLA BEAM)+ 液体活检(NTRA GH)+ AI 制药(TEM SDGR RXRX)+ 罕见病(SRPT KRYS RARE)。共同原因答不上——和 Biotech 被降级为 XBI 的理由一样 | 二选一:降级 proxy ARKG;或拆成「基因测序/诊断」(ILMN PACB TWST TXG NTRA GH GRAL VCYT NEO CDNA WGS)与「基因编辑」(CRSP NTLA BEAM EDIT PRME),其余出 |
| **Robotics & Automation**(60) | ROBO/DRIV 种子带进 NVDA GOOGL MSFT INTC QCOM NBIS **ILMN**(测序仪?)TER;骨干 Specialty Industrial Machinery 又把 GEV/ETN/PH/EMR/CMI/ITW 这些通用工业全收了。既污染又稀释 | 删 ETF 种子;手写:ROK SYM TER ISRG(?)NDSN IEX ATS NOVT AMBA PATH(RPA)+ 人形/协作机器人概念(TSLA 按盘面不进);或承认它是 Specialty Industrial Machinery 板块桶改名 |
| **Grid & Electrification**(28) | PAVE 种子带进 UNP CSX NSC(铁路)DE HWM TT NUE ROK——没有一个是电网 | 删 PAVE;Electrical Equipment & Parts 骨干 + 手写 VRT ETN PWR GEV HUBB NVT POWL AYI ATKR MYRG PRIM IESC EME FIX(后四个是电气承包商) |
| **Reshoring / Industrial Renaissance**(46) | 同一个 PAVE 种子,同一批铁路;和 Grid 高度重叠;"共同原因"= 美国资本开支/IRA/CHIPS,能答但松 | 删 PAVE;骨干 Engineering & Construction + Metal Fabrication 已经是它的实体;和 Grid 二选一保留 |
| **Steel**(15) | 名字 Steel,成员含 Aluminum(AA CENX KALU CSTM)——铝价和钢价不是一个驱动;标准自己拆过 Metals & Mining | 拆:Steel(NUE STLD RS CLF MT PKX TX GGB SID WS NWPX)/ Aluminum(AA CENX KALU CSTM)或 Aluminum 并入 Chemicals & Materials |
| **Homebuilders**(34) | 含 Building Products & Equipment:TT 105B、JCI 93B、CARR 52B 是商用暖通,不是建房;主题中位 ~5B,TT 是 20× | Residential Construction 骨干(DHI PHM LEN NVR TOL MTH KBH GRBK SKY CVCO MHO IBP DFH LGIH)+ 与住房直接相关的建材(BLDR TREX LPX MAS FBIN OC AWI);**exclude TT JCI CARR LII SPXC AAON**(暖通/商用) |
| **Agribusiness**(26) | Farm & **Heavy Construction** Machinery 把 CAT 405B、PCAR(卡车)、OSK、TEX、FSS、BLBD(校车)带进来;主题中位 ~7B,CAT 是 58× | exclude CAT PCAR OSK TEX FSS BLBD;留 DE AGCO CNH LNN ALG + Agricultural Inputs + Farm Products |
| **Defense**(55) | Aerospace & Defense 全收:**SPCX 1,984B**(SpaceX)+ GE 383B(民航发动机)+ HWM/TDG/HEI(民航售后)——一半是航空不是国防;SPCX 一只 = 其余 54 只市值之和 | 要么改名 Aerospace & Defense;要么 exclude SPCX GE HWM TDG HEI HEI-A FTAI AIR ACHR(eVTOL)RKLB PL LUNR RDW(太空,已有 Space) |
| **Broad AI Theme**(137) | industries 把 Software-Infrastructure 整体收进来:CPAY GPN TOST KSPI PAYP VRSN GDDY AKAM(支付/域名/CDN)都成了 AI;AAPL AMZN 也在(AI-Datacenters 已因稀释移除它们) | 只留 AIQ 种子 + Semiconductors 骨干,删 Software-Infrastructure 整段映射;或承认它是"AI 大票篮"改 proxy AIQ |
| **Optics & Networking Equipment**(19) | = Communication Equipment 整个桶:ASTS(卫星)ONDS(无人机)MSI(对讲机)ZBRA(条码)VSAT DGII VISN 不是光模块/网络设备;**COHR 68B(相干,Scientific Instruments)漏了** | 手写:LITE CIEN AAOI COHR FN(Electronic Components)CSCO ANET(在 AI-DC)HPE UI EXTR VIAV NOK ERIC;exclude ASTS ONDS MSI ZBRA DGII VISN |
| **IT Services**(41,val=weak) | Finviz 桶:APLD CIFR(AI/加密数据中心)GDS VNET(中国 IDC)SHAZ PONY BBAI 混在 IBM/ACN 里;四态验证本来就弱 | 标 provisional 或 exclude APLD CIFR GDS VNET SHAZ PONY BBAI |

### ⚠️ 概念对、成员要改

| 主题 | 问题成员(判据) | 建议 |
|---|---|---|
| **Cybersecurity**(15) | CIBR 种子带进 **AVGO 1,867B**(稀释:n=15,中位 ~25B,20× = 500B,AVGO 违反)、CSCO 445B(边缘)、AKAM/FFIV/NET(CDN/ADC,半沾边) | exclude AVGO;CSCO 二选一;NET/AKAM/FFIV 留(有安全收入,盘面跟) |
| **Lithium & Battery Tech**(9) | LIT 种子带进 **TSLA 1,340B、RIO 122B**(n=9,中位 ~2B,20× = 40B,两只都违反);**SQM(锂,10.7B)漏了**——它被 REMX 塞进了 Rare Earth | exclude TSLA RIO;add SQM;ENS(铅酸)按 note 保留最松 |
| **Rare Earth Metals**(6) | REMX 带进 **ALB SQM(锂,不是稀土)**;TMC(深海多金属结核,不是稀土) | exclude ALB SQM;TMC 二选一;留 MP USAR UUUU(有 REE 分离线);IDR/CRML 不解析已掉 |
| **Solar**(9) | TAN 带进 **HASI**(气候金融,Asset Management)、CWEN(yieldco) | exclude HASI;CWEN 二选一 |
| **Uranium & Nuclear Energy**(8) | 名字含 Nuclear Energy,但 **SMR NNE**(Specialty Industrial Machinery)、**BWXT**(Aerospace & Defense)不在;OKLO 在(经 URA) | add SMR NNE BWXT;OKLO 留 |
| **Space**(6) | **SPCX 1,984B 不在**(它在 Defense 里);MDA(MDA Space 5.7B)VOYG(2.7B)KRMN(8.2B,航天/防务部件)在 Defense 不在 Space | add SPCX MDA VOYG(KRMN 二选一);SPCX 进来后稀释判据会响——它就是这个主题的定价者,建议接受并在 note 记 |
| **AI - Datacenters**(16) | 手写名单干净;但 **DELL 311B**(AI 服务器)、MRVL 205B、ALAB CRDO(互连)、FN CLS(光模块/EMS)、HPE 不在 | add DELL MRVL ALAB CRDO FN CLS(HPE 二选一);IREN/CORZ 按盘面留 Crypto |
| **Medical Devices**(60) | 手写 80 只里 **LNTH**(放射性药,Drug Manufacturers)、**OMCL**(药房自动化,Health IT)、**IDXX**(宠物诊断)、DRTS(Biotechnology)不是器械;ABT 被 verify FLAG 但器械是其四段之一,留 | exclude LNTH OMCL IDXX DRTS |
| **Quantum Computing**(4,不发布) | IBM 已在 note 里承认违反收入/定价判据,"操作者要求保留" | 维持;成员少是事实 |
| **Crypto Equities**(14) | 按"盘面压叙事"规则留 IREN/CORZ/WULF/HUT;COIN/MSTR/GLXY/BMNR/SBET 都对 | ✅ |
| **Copper**(7)/ **Silver**(6)/ **Gold**(30)/ **Coal**(6) | Gold 含 PAAS/CDE(银为主)——Finviz 归 Gold,盘面跟金银都动,可留;**HL(Hecla 12.6B,Other Precious Metals)不在 Silver** | Silver add HL;其余 ✅ |
| **Memory & Storage**(5) | 干净 | ✅(PSTG 不在池) |
| **Drones**(5)/ **Semis Large Caps**(10)/ **Tech Mega Caps**(9)/ **Clean Energy**(19) | 干净;Clean Energy 的 BE/PLUG(燃料电池)按 ICLN 算合理 | ✅ |
| **Beverages / Household / Tobacco / Banks-Money Center / Electronic Components** | 单一 industry,机械映射,无问题 | ✅ 🏷 |
| **Transportation & Logistics**(46) | 含 JOBY(eVTOL,Airports & Air Services)PAC/ASR/OMAB/CAAP(机场) | JOBY exclude;机场留 |
| **Consumer Retail / Travel & Leisure / Insurance / Utilities / Real Estate / Regional Banks / Oil & Gas / Chemicals / Industrials / Software / Semis Broad / Financials** | 板块桶,映射本身对 | 🏷 见第一节 |

---

## 三、遗漏候选(第一轮,按行业反查;描述库齐后补第二轮)

| 主题 | 候选 | 依据 |
|---|---|---|
| Uranium & Nuclear | SMR NNE BWXT | 小堆/核燃料/核部件,行业归错桶 |
| Space | SPCX MDA VOYG KRMN | 全在 Aerospace & Defense 桶 |
| AI - Datacenters | DELL MRVL ALAB CRDO FN CLS HPE | AI 服务器/互连/光模块 |
| Lithium | SQM | 在 Rare Earth 里放错 |
| Silver | HL | Other Precious Metals |
| Optics & Networking | COHR FN | Scientific Instruments / Electronic Components |
| Fintech(重建) | SOFI AFRM UPST HOOD TOST XYZ PYPL SEZL KLAR NU PAGS STNE DLO FOUR FLYW PAYO MQ DAVE | 现在散在 Software / Capital Markets / Credit |
| Grid(重建) | MYRG PRIM IESC EME FIX + Electrical Equipment 骨干 | 电气承包 |

---

## 四、给数据端自己的动作(等 Andy 签)

1. `taxonomy.py` 加 `kind` 字段并导出到 groups.json(theme / sector / factor / proxy)——**不删任何主题**,只分组。
2. 按第二节改 `extra/exclude`;每处在 note 记日期理由(标准 §三)。
3. 改完跑 `verify_members` + `build_groups` audit CLEAN,再 `validate_taxonomy` 看 excess 变化;**成员改动和验证不能用同一窗口**。
4. 第二轮:描述库齐后,对每个业务主题按关键词在全池反查候选,列表给 Andy 签。

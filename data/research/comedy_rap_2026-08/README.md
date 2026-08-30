# 喜剧与说唱的语言技法研究 · 第一轮

**任务书**：[`Fluxus_Brand/ops/briefs/2026-08-30_zac_comedy_rap_study.md`](../../../Fluxus_Brand/ops/briefs/2026-08-30_zac_comedy_rap_study.md)（Andy 2026-08-30 立项）
**本轮**：Nighty Zac · 2026-08-31 夜间窗口

---

## 🎯 一句话结论

**技法层已经建好（15 条 device + 一份减法清单），但这一轮它一个字都还不能进 Voice Bible——
因为任务书的通过线是「Andy 盲选 ≥7/10」，而盲选还没发生。** 要的就是你 20 分钟。

## ⚠️ 需要 Andy 做的唯一一件事

打开两张卷子，各回一串字母。**别看别的文件**（答案卷会污染盲选）：

| 卷 | 是什么 | 花多久 |
|---|---|---|
| [`BLIND_A_compression.md`](BLIND_A_compression.md) | 10 组，每组两版，选你更愿意发出去的那版 | ~10 分钟 |
| [`BLIND_B_closings.md`](BLIND_B_closings.md) | 10 个收口位，每位 4 个候选，选一个 | ~10 分钟 |

回给我 20 个字母就行（`C1:A C2:B …`）。答案卷 `ANSWER_KEY_A/B.md` **选完再开**。

---

## 一、这一轮实际做了什么

| # | 交付 | 文件 | 状态 |
|---|---|---|---|
| 1 | 名单 **+ 判据**（喜剧 8 · 说唱 8 · Rubin 单列），含**被判据挡住的人** | [`roster.md`](roster.md) | ✅ |
| 2 | **Device 库 15 条**，每条含机制/动作/用在哪/**怎么证伪** | [`devices.md`](devices.md) | ✅ |
| 3 | **A/B 盲选卷 20 组**（压缩 10 + 收口 10），不标哪版是哪版 | `BLIND_A/B_*.md` | ⏳ 等 Andy |
| 4 | 通过 A/B 的 device → 追进 `Fluxus_Swipe_File.md` | — | 🚫 **本轮不做，见 §四** |
| 5 | **「试过但不该用的」6 条**，每条带数字或具体失败句 | [`null_results.md`](null_results.md) | ✅ |
| + | Rubin 线：**「删什么」七问**，逐条在 MRNA 长文上跑过 | [`subtraction_checklist.md`](subtraction_checklist.md) | ✅ |

---

## 二、⭐ 实验设计：这一轮不是「让 Andy 挑好句子」

**如果我只交 10 组「原句 vs 我的改写」，他大概率整体偏好改写——那什么也没证明**，
只能说明「花时间重写过的句子更好」。这跟本仓那条坑一模一样：
`pitfall_borrowed_list_as_a_ruler`（尺子内置了要测的那道闸）。

所以压缩卷是 **6 + 4 的设计**：

| 组 | 是什么 | 我的**预注册预测** |
|---|---|---|
| **C1–C6**（expository） | 原文在做说明/铺陈的段落 | **改写胜** |
| **T1–T4**（tight，对照组） | 原文已经是一句一画面的句子 | **原句胜** |

**⚠️ 预测封存在本 commit 里，Andy 还没选。** 三种结果三种读法：

- **改写在 C 组胜、在 T 组输** → device 成立**且有边界**（这是最有用的结果，边界比技法值钱）
- **改写在两组都胜** → 说明赢的是「重写」不是 device；**下一轮必须改设计**（同一个意思两种 device 配对，去掉「谁被重写过」这个混淆）
- **改写在两组都输** → 整个方向重估，不修补

收口卷里另有一个**校准位**——**我不说是哪一个，也不说它长什么样**（说了就等于给他答案）。
它的判读规则封在 [`ANSWER_KEY_B.md`](ANSWER_KEY_B.md) 与本 commit 里，选完再开。
它测的是**这份研究对 Andy 偏好的读法本身**：若校准位翻车，后面 9 个位的结论一并打折。

---

## 三、本轮已经拿到的三个可用结论（不依赖盲选）

这三条是**脚本算的或在他自己文本上跑出来的**，Andy 选不选都成立：

1. **「比喻优先于数据」有边界，而边界现在能写成一句可执行的话。**
   C6 是 expository 组里唯一没过 −30% 词数线的（**9%**）。病因不是画面差，是那两个宽度数字
   **是判断的证据**，替掉它省下的词全来自删证据。
   → 建议 Voice Bible §4.8 第 3 条改成：**「比喻优先于当修饰用的数据。当证据用的数据不参与比喻，它换个位置。」**
   （改 Voice Bible 是 Marketing Steve / Studio Q 的文件，我只提议，见门铃。）

2. **Andy 已经在用其中 6 条 device，只是没有名字。**
   `device-04` 反高潮（*"I was asleep."*）· `device-06` 自我引述（*"the frightened version of me"*）·
   `device-09` 一词双义（*"carrying you"*）· `device-02` 具体名词（*"a fish breaks the surface"*）·
   `device-05` 前提当事实（*"Even in hard times, people smoke."*）· `device-15` 画面替数据（甜点那句）。
   **这条的意义是防止走偏**：这份研究不是给他换一种写法，是**把他已经会的那几件事写成可以被 Steve/Q 复现的动作**。

3. **减法清单里有一条在他身上报不出阳性，如实记录。**
   S2「删限定词」在 1,678 词的 MRNA 长文里**零命中**——他的散文里本来就没有 `basically`/`arguably` 这类护身符。
   一份每条都命中的清单是可疑的；这条空命中反而是清单没在自说自话的证据。

---

## 四、⚠️ 三处我没有照任务书做，逐条说明

### ① 没有交语料（任务书 §三：每位 20–40 个单条）
**不复制歌词与逐字稿**（任何长度）。任务书 §六自己写着「入库的是 device 和你的改写，不是别人的作品」，
我把这条执行到了**中间产物**上。**代价**：device 库没有「原句」栏，你无法从本文件反查我读得对不对。
**补救路径**：下一轮可以补**指到具体一条的链接**（官方视频时间戳），由你自己点开对照，仍然不落原文。
详见 [`roster.md`](roster.md) §五。

### ② 没有追进 `Fluxus_Swipe_File.md`
任务书 §三第 4 步：**「没通过 A/B 的 device 不进 Voice Bible」**。A/B 还没判，所以**一条都不该进**。
现在写进去 = 把「我认为好」当成「已验证」（`pitfall_shipped_before_out_of_sample` 同形）。
另：`Fluxus_Brand/voice/` 是 Marketing Steve 的地盘，**不在我的 safe-merge 白名单内**——
即便通过了，落盘也该由他做，或由我出补丁他合。**盲选结果回来后我出现成的 append 块。**

### ③ Andy 给的那条 Instagram reel 没看
`instagram.com/reel/DcQtt9uoXkE/` 需登录（红线：不抓需登录站点）。
**所以 Jay-Z / Rubin 那两格的理由是从两人公开的创作方法推的，不是从那条 reel 来的**——
和 Steve 08-30 的处理一致。**如果那条 reel 讲的是别的，以它为准，这两格重写。**

---

## 五、复现

```bash
cd data/research/comedy_rap_2026-08
python3 verify_originals.py   # 核对每条「原句」逐字来自已发布正文（阳性对照见 §六）
python3 build_ab.py           # 重新渲染 4 张卷子；词数与减幅全部现算
```

**为什么词数不手打**：本仓 `pitfall_i_misread_my_own_table`——我曾经抄了相邻的一列，
拿一张否定我的表当成支持我的证据。**散文里不许出现手打的数字。**

### 六、这一轮自己做的阳性对照

- `verify_originals.py` 先注射一处改词（`pain unit` → `pain metric`），确认它 **exit 1 且点名 C3**，再信它的 `all verbatim ✅`。
- 打乱用 `zlib.crc32` 不用 `hash()`——Python 对字符串哈希每进程随机化，
  本仓 08-26 那份 smoke fixture 就栽在这里（同一支票的收盘在三个 seed 下是三个数）。
  **盲选顺序必须每次一致**，否则你回给我的字母对不回去。

---

## 七、下一轮（等盲选结果）

1. 按 `ANSWER_KEY` 判 15 条 device 的生死，出 Swipe File append 补丁给 Marketing Steve
2. NULL-2（对仗）**配对同义**重测 ≥12 对——本轮它的分辨率不足以判定，只能给方向
3. NULL-1/4/6 三条目前只是「作者自述」级证据，塞进下一轮盲选升级成实测

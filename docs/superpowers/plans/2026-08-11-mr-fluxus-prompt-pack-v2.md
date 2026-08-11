# MR. FLUXUS Prompt Pack v2 + 定妆表 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把已定稿的角色 spec 落成两份 v2 品牌文档 + 一套可直接投喂图像模型的定妆表提示词，并完成出图验收闭环。

**Architecture:** 纯文档/设计工作，无代码。`Fluxus_Character.md` 做外科手术式修订（保留 v1、标注改动），`Fluxus_Character_Prompt_Pack.md` 整体升 v2（master prompt 重写 + 新增定妆表 prompt）。出图由 Andy 在外部图像模型执行，Claude 按验收清单审图。

**Tech Stack:** Markdown · 外部图像模型（Midjourney / GPT-image / Gemini 任一）· 图片落盘走素材库（不进 git），选定稿进 `Fluxus_Brand/visual/explorations/`

**Spec:** `docs/superpowers/specs/2026-08-11-mr-fluxus-character-design.md`（已确认定稿）

## Global Constraints

- 工作目录：`/Users/taolezhu/Documents/AI-Trading-System/.worktrees/MarketingVisualDesign`，分支 `design/marketing-visual`
- 色：纸色底 `#F4F3F0`；橙 `#D1600F` 全画面**一处**，不超过一处
- 线：手绘墨线、粗细有变化；阴影只用交叉排线；画内文字全手写
- 角色三件套（不可省略）：黑色针织渔夫帽、金丝圆框眼镜、格子衬衫
- 去英雄化：deadpan 基线略带不耐烦；**永不画**变身特效、发光眼、英雄机位、慢镜语法
- 否定清单 v1 全保留（Corporate Memphis / 牛熊箭头 / 禅意大师 / 3D 渐变 / 动漫大眼…）
- 素材库 `Fluxus_Marketing_Visual_Design/` 是指向主 checkout 的软链，**不进 git**；生成图落这里
- 文档语域：中文为主，设计术语/CSS 值/提示词英文照抄仓库惯例
- 提交信息风格照仓库惯例（诗性 conventional commits），尾行 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: `Fluxus_Character.md` 升 v2（外科手术式修订）

**Files:**
- Modify: `Fluxus_Brand/visual/Fluxus_Character.md`

**Interfaces:**
- Consumes: spec 全文（角色气质、双层结构、猫、四景）
- Produces: v2 角色简报，后续一切画面工作的中文母文件；Task 2 的 prompt 与其一致

- [ ] **Step 1: 文件头部插入 v2 变更记录块**

在第 5 行 `*配套:...*` 之后插入：

```markdown

---

## v2 变更记录（2026-08-11）

定稿 spec：`docs/superpowers/specs/2026-08-11-mr-fluxus-character-design.md`。本文件按 spec 修订，v1 设定不删，改动处以 **[v2]** 标注。要点：

| 项 | v1 | v2 |
|---|---|---|
| 长相 | 匿名四十岁上班族 | **漫画化本人**：黑针织渔夫帽 + 金丝圆镜 + 格子衬衫，圆脸 deadpan（参考照片在素材库 `Reference/`） |
| 命名 | 首选叙事者 / 备选职务名 | **锁定 MR. FLUXUS** |
| 气质 | 一个在等的人 | 保留，叠加 **grumpy 止损文员**：亏钱和盖章是日常，胜率四成写在画面里；牌子 "NOT FINANCIAL ADVICE — 别问我你的股票" |
| 戏剧机关 | —— | **Anderson/Neo 双层**：现实层反高潮（大事发生时画面毫无变化，食指点一下鼠标）；锋利全在脑内层由企鹅化身演。禁一切变身语法 |
| 配角 | —— | **猫**（真实存在）：键盘旁睡觉 / 踩键盘下单；家里的 Market God 化身 |
| 世界 | 单景（读数墙前） | **四固定景**：交易室（真实的家）· 华尔街机房（Algo Monkeys）· 散户厕所隔间（the Herd 代表）· 脑内世界（企鹅 + Market God，1970 模拟仪表 + 激浪派引用库，TV Buddha 复盘位） |
| 真实裂缝 | —— | **那个抽屉**（H1 行为审计的 re-attack 弱点）：贴标签的抽屉，明知不该开，手又伸过去 |
```

- [ ] **Step 2: 命名节改为锁定**

把「### 命名」小节的两个列表项（`- **首选:...**` 至 `- 备选:...` 两行连同中间的风险/解法行）整体替换为：

```markdown
**[v2] 锁定:MR. FLUXUS。** 与 MR. UPDATE 命名结构对仗(MR. + 品牌真正在做的事;
flux = 流、变化 —— 活在变化里的人)。栏目名可直接用 "THE DAILY LIFE OF MR. FLUXUS"。
v1 的两条备选(叙事者拿脸 / THE OPERATOR / MR. WAIT)作废。
```

- [ ] **Step 3: 固定道具表补三行**

在「二、固定道具」表格末尾（`| 计数 | ...` 行之后）追加：

```markdown
| **[v2]** "NOT FINANCIAL ADVICE" 的牌子 | 对仗 Mr. Update 的 BUSY 牌;社群戏的核心冲突:都想让他荐股,他烦 |
| **[v2]** 那个贴标签的抽屉 | 真实弱点(对破碎论点的反复进攻);明知不该开,手又伸过去 |
| **[v2]** 猫 | 键盘旁睡觉(常态)/踩键盘下单(偶尔);家里的 Market God 化身 |
```

- [ ] **Step 4: 验证修订完整性**

Run: `grep -c '\[v2\]' Fluxus_Brand/visual/Fluxus_Character.md`
Expected: ≥ 6（变更记录块 1 处标注说明 + 命名 1 + 道具 3 + 表内引用）
Run: `grep -n '首选:让声音圣经' Fluxus_Brand/visual/Fluxus_Character.md`
Expected: 无输出（旧命名首选已被替换）

- [ ] **Step 5: Commit**

```bash
git add Fluxus_Brand/visual/Fluxus_Character.md
git commit -m "docs(design): the character brief learns its own name — Character.md v2

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: `Fluxus_Character_Prompt_Pack.md` 整体升 v2

**Files:**
- Modify: `Fluxus_Brand/visual/Fluxus_Character_Prompt_Pack.md`（整体重写，v1 结构保留、内容升级）

**Interfaces:**
- Consumes: Task 1 的 v2 简报；spec 第一、二、三、六节
- Produces: ① Master prompt v2（场景图用）② Model-sheet prompt（定妆表用）③ 验收五条 —— Task 3 直接复制投喂

- [ ] **Step 1: 重写 SUBJECT 段（master prompt 内）**

把第四节 master prompt 的 `SUBJECT —` 段替换为：

```
SUBJECT — MR. FLUXUS: a middle-aged East Asian man with a round face and
full cheeks, slightly heavyset. He wears a black knitted bucket hat with a
visible crochet texture, pulled low; thin round gold wire-rimmed glasses;
and a rumpled checked button-up shirt, sleeves pushed up. Expression:
deadpan with a faint hint of grumpiness — the face of a man who has been
asked for stock tips one time too many. Not sad, not smug, never smiling.
He must NOT look cool, heroic, or successful — he looks like an ordinary
tired man doing paperwork. He is small in the frame. His hands are still,
one holding a transparent ballpoint pen.
```

- [ ] **Step 2: 重写 ENVIRONMENT 段**

替换为（现实层=真实的家；模拟仪表条款移交脑内层）：

```
ENVIRONMENT — A small home trading den, not an office: a desk with several
monitors on arms, the charts on them drawn as loose hand-inked squiggles
(never realistic UI), lace curtains behind, a half-finished mug of tea,
and geological strata of paper on the desk — stopped-out order slips, each
stamped NO. A plump indifferent cat sleeps next to the keyboard. One desk
drawer sits slightly open, with a small hand-lettered label reading
"OLD THESIS". Domestic, cluttered, unglamorous.
```

- [ ] **Step 3: 重写 THE JOKE 与 PROPS 段**

```
THE JOKE — Everything about him says small, ordinary, losing-most-days.
The stack of NO-stamped slips keeps growing. He is completely fine.

PROPS — A hand-lettered cardboard sign propped on the desk reading
"NOT FINANCIAL ADVICE". A rubber stamp. One small open notebook with a
single line written in it. The stamped word NO may be the picture's single
burnt-orange (#D1600F) element.
```

- [ ] **Step 4: DO NOT INCLUDE 段追加去英雄化条款**

在 v1 列表句尾（`no monk, no meditation pose.` 之前）插入：

```
no glowing eyes, no transformation effects, no heroic low-angle shot, no
lens flare, no clenched fist of determination, no "focused genius" trope,
```

- [ ] **Step 5: 新增第 4.5 节「Model-sheet prompt（定妆表，第一批产出）」**

在第四节与第五节之间插入完整新节：

````markdown
## 四点五、Model-sheet prompt（定妆表 —— 第一批产出）

*定妆表先于一切场景图。五个场景必须是同一个人,这页就是「同一个人」的定义。*

```
A character model sheet, hand-drawn in pen and ink on a flat warm off-white
page (#F4F3F0), laid out like an animator's reference sheet with small
hand-lettered labels. Cross-hatched shading only, no grey fills, no
gradients. Roughly 4:3 landscape.

ROW 1 — THE SAME MAN, THREE VIEWS: front view, three-quarter view, profile.
A middle-aged East Asian man, round face, full cheeks, slightly heavyset,
wearing a black knitted bucket hat with visible crochet texture pulled low,
thin round gold wire-rimmed glasses, and a rumpled checked button-up shirt.
Identical hat, glasses, shirt and body in all three views.

ROW 2 — EXPRESSION STUDIES, three heads: (a) baseline deadpan; (b) faintly
annoyed, eyes half-lidded, being asked for a stock tip; (c) asleep upright
in a chair, glasses slipping, a small hand-drawn "zzz". No smiling, no
glowing eyes, no heroic expressions.

ROW 3 — PROP STUDIES, drawn separately and labelled by hand: the black
knitted bucket hat; the round gold wire glasses; a rubber stamp and the
stamped word "NO" (this stamped NO, in burnt orange #D1600F, is the only
colour on the page); a transparent ballpoint pen; a mug of tea; a
hand-lettered cardboard sign reading "NOT FINANCIAL ADVICE"; a desk drawer,
slightly open, with a hand-written label "OLD THESIS".

ROW 4 — THE CAT: a plump indifferent cat, two poses: curled asleep beside
a keyboard; standing on the keyboard mid-mischief, one paw on a key.

DO NOT INCLUDE — no charts, no candlesticks, no arrows, no bulls or bears,
no currency symbols, no computer screens, no neon, no 3D rendering, no
gradients, no flat corporate vector style, no anime, no oversized head
proportions, no smiling, no suit, no glowing eyes, no heroic poses.
```

*猫是真实存在的那只 —— Andy 若提供猫的照片,把品种特征(毛色/花纹)补进 ROW 4;
没有照片就先按 "plump indifferent cat" 出,后补。*
*抽屉标签公开版用 "OLD THESIS";内部版可用 "BABA"(H1 审计的实价出处)。*
````

- [ ] **Step 6: 第七节验收由三条扩为五条**

在验收清单追加：

```markdown
4. **剪影测试:** 涂黑整个人形,只留轮廓 —— 渔夫帽 + 圆镜 + 格衬衫的组合还认得出是他吗?
   认不出就是三件套画弱了。
5. **反英雄测试:** 他看起来像一个会赢的人吗? —— **像就重来。**
   这张脸必须属于一个胜率四成、靠纪律活着的人。
```

- [ ] **Step 7: 验证 v2 完整性**

Run: `grep -c 'FLUXUS\|bucket hat' Fluxus_Brand/visual/Fluxus_Character_Prompt_Pack.md`
Expected: ≥ 4（master + model sheet 两处 prompt 都含三件套）
Run: `grep -n 'forties\|unremarkable haircut' Fluxus_Brand/visual/Fluxus_Character_Prompt_Pack.md`
Expected: 无输出（v1 匿名上班族描述已被替换干净）
Run: `grep -c 'glowing eyes' Fluxus_Brand/visual/Fluxus_Character_Prompt_Pack.md`
Expected: ≥ 2（master 与 model sheet 的 DO NOT 都含去英雄条款）

- [ ] **Step 8: Commit**

```bash
git add Fluxus_Brand/visual/Fluxus_Character_Prompt_Pack.md
git commit -m "docs(design): the prompt pack gets a face and loses its hero — v2

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: 出图工单 + 验收闭环

**Files:**
- Create: `Fluxus_Marketing_Visual_Design/Model_Sheet_Drafts/`（素材库目录，不进 git）
- Create（验收通过后）: `Fluxus_Brand/visual/explorations/2026-08-11_mr_fluxus/`（选定稿，进 git）

**Interfaces:**
- Consumes: Task 2 的 model-sheet prompt 与验收五条
- Produces: 通过验收的定妆表 PNG（≥1 张），作为后续一切场景图的一致性基准

- [ ] **Step 1: 建草稿目录**

```bash
mkdir -p "/Users/taolezhu/Documents/AI-Trading-System/Fluxus_Marketing_Visual_Design/Model_Sheet_Drafts"
```

- [ ] **Step 2: 给 Andy 发出图工单**

把 Task 2 的 model-sheet prompt 原文发给 Andy（SendUserFile 或消息内代码块），附操作说明：

> 模型任选（Midjourney / GPT-image / Gemini 都可），同一 prompt 出 **≥4 个种子**；
> 比例 4:3，长边 ≥3000px，PNG；生成图丢进素材库 `Model_Sheet_Drafts/`；
> 顺带一张猫的照片（可选，用来补品种特征）。

- [ ] **Step 3: 验收（Andy 回图后执行）**

对每张草稿跑验收五条（缩 400px / 遮字 / 不像理财 App / 剪影认人 / 反英雄），
用 Read 逐张看图，给出 每张:通过项+落选原因 的点评；全灭则修 prompt 回 Step 2 重跑。

- [ ] **Step 4: 归档选定稿**

```bash
mkdir -p Fluxus_Brand/visual/explorations/2026-08-11_mr_fluxus
cp "/Users/taolezhu/Documents/AI-Trading-System/Fluxus_Marketing_Visual_Design/Model_Sheet_Drafts/<入选文件>" Fluxus_Brand/visual/explorations/2026-08-11_mr_fluxus/model_sheet_v1.png
```

- [ ] **Step 5: Commit**

```bash
git add Fluxus_Brand/visual/explorations/2026-08-11_mr_fluxus/
git commit -m "feat(design): MR. FLUXUS stands for his first portrait — model sheet v1

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Self-Review 记录

- **Spec 覆盖:** spec §1(角色/三件套/气质/抽屉)→Task 1+2;§2(双层/去英雄)→Task 2 Step 1/4;§3(猫)→Task 1 Step 3 + Task 2 Step 5 ROW 4;§6(画法两处更新)→Task 2 Step 2;§8(定妆表先行/交付规格/验收)→Task 2 Step 5-6 + Task 3。spec §4 四景标准照与 §5 场景图属生产路线第 2-3 步,**明示不在本计划**,下一计划承接
- **占位符扫描:** 无 TBD;所有 prompt 全文在场
- **一致性:** 三件套措辞在 master/model-sheet 两处 prompt 逐字一致;橙色唯一落点统一为 stamped NO

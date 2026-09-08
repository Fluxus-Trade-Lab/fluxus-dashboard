# 🔧 产线维修单 · 2026-09-08

> **Andy 09-08 原话：「整包维修」。** 起因是当天日推 C1 被否，他的原话是
> 「挺ai的，就是说了几句话不知道在说什么」。同一天他补的第二句是维修的方向：
> **「你已经读取了大量人说的话，X日调研每天的数据都在那里。」**
>
> ⛔ **本单未结案之前，夜间六站产线停产**：不开新 campaign 卡，日推站不从待批包取 C1。
> 现有四张卡原地封存，status 不动。

## 一、台账（事实，不是感想）

四张卡，零发布，三条 rejected 全部发生在 Gate 判「过闸」之后。

| 卡 | Gate 判定 | Andy 判决 | 他点的是什么 |
|---|---|---|---|
| `2026-08-29_extension-arithmetic` | 4 轮，放行子集 | ❌ 09-04「太ai slop了，也不行」 | **味道** |
| `2026-09-01_august-scorecard` | 2 轮过闸 | ❌ 09-08「挺ai的，就是说了几句话不知道在说什么」（V2） | **空** |
| `2026-09-03_noise-with-structure` | 3 轮过闸 | 未裁 | — |
| `2026-09-06_autumn-effect-decay` | 4 轮过闸 | ❌ 09-06「olden September, silver October这个话题删除」 | **题目** |

味道、题目、空——三次形状不同，但**三次都是过了六道闸之后才被人拦下**。
按宪法三次律：不再记 memory，升级为机制。

## 二、三条缺口（每条可复现，别信我的形容词）

### 缺口 1 ⭐ 产线不看外面（Andy 09-08 亲指）

信号站的 `reads` 有 11 条，**全部是我们自己仓库里发生的事**：素材箱、posts.csv、收藏夹、receipts、claims、incidents、growth、Andy 口述。
没有一条是「外面的人今天在说什么」。

而 `data/content/x_watch/` 每天都在长：**mentions 433 行 · posts 500 条/3 天 · 睡前速报 3 份 · ticker_daily 152 行 · board_data 353KB · lookback 两支专题**。
里面有蹭位榜（谁的屋子满、底下有没有人说话）、有 stance、有 views/bookmarks——**这是唯一一份读者需求的现场读数。**

复现（返回空＝零站引用）：
```bash
for f in $(git ls-tree --name-only -r origin/main Fluxus_Brand/ops/campaigns/roles/ \
  Fluxus_Brand/ops/campaigns/PIPELINE.md Fluxus_Brand/BRAIN.md Fluxus_Brand/brain/); do
  n=$(git show origin/main:$f | grep -ci "x_watch\|蹭位\|nightcap\|mentions.csv"); [ "$n" != 0 ] && echo "$n $f"
done
```

**后果直接对上 09-08 那句判决。** 四张卡的题目是：延伸度算术、我们自己的月报归因表、我们自己的 CI 字节码缓存、黄金季节性。
前三个是**我们仓库里发生的事**。读者没在那间屋子里，所以「说了几句话不知道在说什么」——他不知道，是因为这些话本来就不是对他说的。

### 缺口 2 · 负面清单挂错了站

`verdicts.jsonl` 的自述是「旗舰站/日推读它当负面清单」，`roles/04_flagship.md` 的 reads 里确实有它。
但三条 rejected 里 **两条（09-04 V1、09-08 V2）是 ⑤ 分发站的变体**，而 `roles/05_distribution.md` 的 reads **没有 verdicts**。
清单挂在了不生产它们的那一站。

09-08 被否那条的收口是 `Stamped at entry… / Stamped at exit…` 一对对仗——
verdicts **第一条**（08-24「The news is never in the chart」，他亲手删的）点的就是这一刀。
**同一把刀，隔 15 天，从没被挂清单的那一站原样再出一次。**

### 缺口 3 · Gate 逐卡不查判决账

`roles/06_gate.md` 只在**每周附加任务**里用 verdicts（出 keep/test/stop 周报）。
逐卡过闸的 checklist 里没有它。所以缺口 2 那把刀，在逐卡链路上**没有任何一站会拦**。

### 缺口 4 · 我自己的（日推站，本班犯的）

我把 09-08 的 C1 排在第一位，写的理由是「落地成本最低」——零数字不用跑复算、零配图不用等人画。
**零数字零票根，正好等于零内容。** 我拿"最省事"当"最该发"，亲手把全包最空的一条顶上去。
医生查房，漏了自己的床。

## 三、修完算什么（可证伪，别拿"感觉好多了"验收）

1. **信号站加一条硬 reads**：`data/content/x_watch/`（nightcap + mentions + ticker_daily）。
   取用信号的六件里增第七件：**「这个题目今天外面有谁在说、屋子多满」，出处必须是 x_watch 的具体行**；
   答不出＝不是信号，退回重选。⚠️ 不是「蹭热点」——是**先确认屋子里有人**，再决定端什么进去。
2. **具体物闸**（新增，⑤ 分发站 done-when + Gate 逐卡 checklist 各一份）：
   每条变体必须占到**一笔具体交易 / 一个能查的数字 / 一个能查的时间戳**中的至少一样，占不到就退回。
   09-08 那条三样全无，六道闸零拦截——这道闸就是冲它加的。
3. **verdicts 上闸**：加进 `roles/05_distribution.md` 的 reads，并进 Gate 的**逐卡** checklist（不只是周报）。
   Gate 报告里逐条写「撞没撞历史判决」，撞了指名哪一条。
4. **日推排序键改掉**：C1 按「有没有一个具体的东西」排，落地成本降为并列时的次级判据。

## 四、复产条件

上面四条全部落地 + 下一张卡的信号站能指名「今天外面谁在说这个题目」，才解除停产。
**解除由 Andy 说了算，产线不自己宣布修好了。**

## 五、谁接

产线属 **Marketing Steve 线**（TEAM.md：夜间六站内容流水线含 Gate 子 agent 均属本线边界）——
**这是本线自己的活，不外派。** 由夜间产线工头接单：今晚不产卡，改产这四条修法。
日推站（备稿工序）从 09-09 起按第 4 条排序，C1 只出金句库与 Andy 原料两个来源，直到复产。

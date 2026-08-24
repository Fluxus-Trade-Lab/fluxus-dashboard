# 产品定义 —— 两档的分界线在哪

*2026-08-25。起因:Andy 看 About 草稿「一堆很空的话,没有实质」→ 追问才发现**我一直不知道产品是什么**。*
*本文件是那次追问的答案 + 由它炸出来的三处矛盾 + 建议的解法。**未定案前不要再往站上粘任何文案。***

---

## 一、Andy 的原话(2026-08-25,四问四答)

| 问 | 答 |
|---|---|
| 每周那封信里是什么 | **前瞻 + 复盘 + 市场状态/名单**(三个都要)。并且他自己指出:*「这也就意味着我每周都要发多于 1 封的信。所以这是我对产品打磨还不明确的原因。」* |
| 持仓公开度 | **每封信都附实时持仓表** |
| Dashboard 订阅者能否用 | **能用**。它是 *screener + 自建 database + self-training database*,**仍在建** |
| Discord 和 Substack 的关系 | **Discord 是主战场,$99/月**,给实时信息和进出场。**Substack $39/月不给实时信息和进出场**,其余(复盘、盘前等)都给。Substack 用户可以进 Discord,但看到的内容不升级,除非自己从 $39 升到 $99 |

---

## 二、🔴 三处矛盾

### 矛盾 1(⚠️ 现在就在站上)—— 付费权益承诺了「进出场」,而那是 $99 档的东西

我 2026-08-25 粘上去的 paid benefit 第一条:

> `How Much — every idea with its entry, its stop, and what I'm risking in percent`

**但 Substack $39 档明确不给进出场。** 这条现在是站上的付费权益文案。
*(缓解因素:付费档尚未开启,买家看不到这条;但 free benefit 和 hero 里的同类表述**已经对所有访客可见**。)*

**同样受影响的还有:**
- **Hero / 简介**(已可见):`Every idea arrives with its size and its stop.`
- **Welcome 邮件 free 版**(已生效):`You'll see the entry, the stop, the trade risk in percent, and the portfolio risk in percent — on every single one.`

### 矛盾 2 —— 「每封信附实时持仓表」和「Substack 不给实时信息」直接打架

实时持仓表(ticker + entry + stop + 仓位%)**就是**实时信息。
这两条不能同时对 $39 档成立。

### 矛盾 3 —— 「一周一封」和三段内容对不上

Andy 自己点破的那条。我今天刚把「一周一封,每周日」**硬写进六个位置**
(hero / free benefit / paid benefit / welcome 邮件 / 页脚 / X bio)。
若产品实际是每周两封,这六处全部要改;若维持一封,那封信要装下三段内容。

---

## 三、建议的解法(每条都给理由,Andy 定)

### 解法 1:把「size and stop」的口径从**信号**改成**复盘**

品牌承诺(`every idea arrives with its size and its stop`)**不用放弃** —— 换一个读法就成立:

| 读法 | 含义 | 属于 |
|---|---|---|
| ❌ 信号口径 | 「给你一个能照着下单的 entry/stop」 | **$99 Discord** |
| ✅ 复盘口径 | 「我讲的每一个想法,都带着**当时**的仓位和止损,可核对」 | **$39 Substack** |

**这正是 MRNA 那篇实际做的事** —— 它给了 62.72 / stop 60 / 0.217%,但那是**五天后写的**,
没人能照着它下单。这个口径下承诺一个字不用改,而且它是真的。

> **需要在文案里加一句消歧。** 建议:
> `Every idea arrives with its size and its stop — after the fact, with the arithmetic, so you can check it.`
> 或更硬:`These are not alerts. Nothing here is timed for you to copy.`(这句 `_BOILERPLATE` 块 A 里已经有了)

### 解法 2:持仓表给「截至发信时」,不给实时

- **$39 Substack**:每封信附**截至发信当刻**的持仓表(顺序、仓位%、trade risk、port risk)。
  这不是实时 —— 周一开盘它就旧了,而这正是它和 $99 的分界。
- **$99 Discord**:实时变动、进出场当下播报。

**这和 TSF 的做法同构** —— 他的 `Momentum Leaders Portfolio` 也是按档位分闸,不是所有人都拿实时。

### 解法 3:频率 —— 建议维持**一周一封,三个固定栏目**,不拆成两封

| | 一封三栏 | 一周两封 |
|---|---|---|
| 承诺难度 | 一个承诺 | **两个承诺,断更风险翻倍** |
| 读者认知 | 「周日那封信」= 一个仪式 | 要记两个时间 |
| 结构 | **固定栏目本身成为格式**(TSF 的做法) | 每封都要单独起结构 |
| 你的产能 | 一次写完 | 一周两次坐下来写 |

**建议的固定三栏(每封信都一样,顺序不变):**

```
① The Weather      —— 市场状态:regime / breadth / dealer gamma 的读数
② The Watch        —— 在看什么:名字 + 为什么在名单上（不给 entry）
③ The Ledger       —— 复盘:这周平掉的仓,逐笔带数字,含亏损
   The Book        —— 截至发信的持仓表（固定尾块）
```

> 「前瞻」不单独成栏 —— **它就藏在 ② The Watch 里**。区别在于给不给可执行的 entry:
> 给了就变成 $99 的产品,不给就是 $39 的观察名单。这条线正好是两档的分界线,
> **让栏目结构自己守住这条线**,比靠每次写作时自律要牢。

### 解法 4:Dashboard —— About 里写「订阅者能用」,但**别写成已完工**

Andy 原话是「**仍然在建立**」。建议文案口径:
> 承诺**访问权**(这是真的、且是 TSF/JB 结构性够不到的东西 —— 他们买第三方工具,你自己造),
> 但**不列举它还没有的功能**。self-training database 在跑通之前一个字都不要写进 About。

---

## 四、⏸ 在 Andy 定案前,冻结的动作

- ❌ 不再往站上粘任何文案(About / Welcome / benefits 全部暂停)
- ⚠️ **站上现存的三处表述需要在开付费之前修**(见矛盾 1),但**不急于今天**——
  付费未开启,当前暴露面只是 hero 和 free benefit 的措辞
- ✅ 可以继续做的:五篇文章的竞赛(那是结构/修辞层,不依赖两档分界)

---

## 五、给 Andy 的三个问题(定了就能一口气写完 About + 权益 + Welcome)

1. **频率**:一周一封三栏(建议)· 还是一周两封?
2. **持仓表**:截至发信(建议)· 还是干脆不给 $39 档?
3. **`every idea arrives with its size and its stop` 这句品牌承诺**:
   按复盘口径保留(建议)· 还是让它专属 $99 档、Substack 换一句?

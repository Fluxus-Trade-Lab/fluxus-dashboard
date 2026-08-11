# Discord 语料存档 — 断点记录

*用途:抓取 Fluxus_Z 本人在 Fluxus Trade Lab 的发言,做语感分析 + 金句挖掘。*
*产出:`../../Fluxus_Brand/voice/Fluxus_Voice_Audit_Discord.md`(语感分析)· `../../Fluxus_Brand/voice/Fluxus_Own_Lines.md`(金句库)*

---

## ✅ 抓取已完成(2026-07-29)

**`fluxus_corpus.json` — 中文 4,714 / 英文 8,346 / 合计 13,060 条**

| 频道 | 覆盖范围 | 状态 |
|---|---|---|
| **#🤝互帮互助**(中文,对话/教学) | **2025-11-14 → 2026-07-29** | ✅ 完整。频道从 2025-11-14 开始,已翻到第一页 |
| **#🌛live-commentary**(英文,单向播报) | **2026-01-20 → 2026-07-29** | ✅ 完成。用户明确指示 1/21 之前的不需要 |

`fluxus_corpus.bak.json` 是合并前的备份。

**频道 ID:** 互帮互助 `1438755476459225150` · live-commentary `1136817146542960680` · server `1136815190688669736`

---

## ⭐ 方法(全部实测有效,下次直接照抄)

### 1. 用 Discord 搜索,不要滚频道

搜索框依次输入并**从下拉里点选绑定**(只打字不点选 = 当成字面文本,会返回错的结果):

```
in: <频道>      → 点下拉里的频道
from: Fluxus_Z  → 点下拉里的用户
before: YYYY-MM-DD   （可选,用来绕过 400 页上限 / 接续断点）
```

⚠️ **搜索是频道内的,不是全服务器的。** 每个频道要单独搜一次。

每页 25 条,右下角 Back / 1 2 3 … N / Next。

### 2. 抓取器(保留整条多行内容)

```js
window.__S=new Map();
window.__sgrab=()=>{document.querySelectorAll('.searchResult__80bf8').forEach(r=>{
  const c=r.querySelector('[id^="message-content-"]');
  if(c){const t=c.innerText.replace(/\(edited\)/g,'').replace(/\n{2,}/g,'\n').trim();
    if(t)window.__S.set(t,t);}});return window.__S.size;};
```

> 早期版本用了 `.split('\n')[0]` 只取首行 —— **英文频道是多段长贴,那样会丢掉大半内容**。别再这么写。

### 3. 翻页:必须用 `computer.left_click`,不能用 JS

Next 按钮截图坐标 **(1443, 769)**(1449 有时不响应)。

一个 batch 排 12 组「点击 → `await sleep(2000)` → `__sgrab()`」,是这个环境的效率上限。

> ❌ **别用 JS 循环点 Next。** `setTimeout` 会被后台标签页节流到近乎停滞(实测 4 分钟只翻 5 页)。`computer` 点击会激活标签页,反而快 10 倍。
> ❌ CDP `Runtime.evaluate` 45 秒超时,单次 JS 里也塞不下长循环。

### 4. ⭐ 导出:浏览器 POST 到本地 HTTP sink(**这是最大的解锁**)

下载被 Chrome 静默拦截、`get_page_text` 在 ~50KB 处截断 —— 都绕开:

```bash
# 起一个接收端(带 CORS),写到 dump.txt
python3 sink.py &   # 见下方
```
```js
// 页面里,一次全发出去,不受大小限制、不占上下文
const msgs=[...window.__S.keys()];
await fetch('http://127.0.0.1:8791/',{method:'POST',body:msgs.join('\n@@\n')+'\n@@\n'});
window.__S=new Map();
```

sink.py 关键点:`do_OPTIONS` + `Access-Control-Allow-Origin: *`,以 `ab` 追加写入。

然后 Python 端按 `\n@@\n` 切分、用 `[一-鿿]` 分中英、`dict.fromkeys` 去重、写回 JSON。合并脚本模板见 `/tmp/merge_corpus.py`(可重建)。

**节奏:每累积约 1,100 条导出一次并清空 `__S`。**

---

## ⚠️ 踩过的坑

1. **合并脚本要先确认 JSON 的键名。** 本档用 `chinese` / `english`,不是 `zh` / `en`。写错会凭空多出两个键(数据没丢,但要清理)。**改之前先备份。**
2. **搜索框会坏。** 反复改条件后会出现 `Filters (5)`、"We dropped the magnifying glass"、或 `from:` 掉绑定 → 换一个干净的标签页重建搜索。
3. **别点结果里的图**,会开 lightbox;要点空白处。
4. **搞坏 DOM 后 `history.back()` 会丢掉内存里的 `__S`** —— 曾经因此丢了约 797 条。**先导出,再动 DOM。**
5. 直接 `navigate` 到频道 URL 会掉登录态 → 从侧边栏点频道进去。
6. 去重时注意:首行版和完整多行版是两条不同的字符串,要按「首行相同且一方是单行」的规则清掉短的。

---

## 还没碰的频道(如需扩充)

`#trading-floor` · `#swing-positioning` · `#option-tactical` · `#day-trades` · `#music-n-art`(艺术表达)· `#课程素材` / `#作业`(教学语料,「教学长文」的好原料)· `#24h-random-chats`(最松弛的语感)

## ⭐ 需求侧扩充(2026-08-12,方法已立,未执行)

**上次抓取只留了 Fluxus_Z 本人的发言 —— 对「挖声音」这个目的是对的,但它导致「八万行自己说的话,零行别人问的话」。**

互帮互助频道:**总消息 944,落盘 514(全是本人)→ 别人问的 430 条从没抓过。**

要补的话,照本 SOP,两处改动:
1. **搜索条件去掉 `from: Fluxus_Z`** —— 那正是只拿到自己发言的原因
2. 抓取器额外取作者与时间戳用于配对 **问题 → 回答**,**落盘前去标识**

三档隐私方案和完整理由见 `../../Fluxus_Brand/research/Fluxus_Demand_Side_Method.md` §二。
⚠️ **外部服务器(用户只是成员)只做统计不落盘原文** —— 见该文件 §三。

---

## 隐私说明
只提取 `Fluxus_Z` 本人的发言。频道内其他成员的消息在抓取过程中会被看到,但**不写入任何存档文件**。

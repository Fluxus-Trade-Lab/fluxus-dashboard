# X 账号历史帖库 —— 采集方法（SOP）

*2026-08-10 立。用途：给任何一个对标账号建「过去 N 年头部帖子 + 数据」的库。*
*第一个目标：@ohiain（未跑）。以后每个「成长股」类对标（@ZaStocks · @thesetupfactory …）都照这个做。*
*方法脉络承自 `data/discord/README.md`（Discord 全量爬取）—— 同一套思路：登录态浏览器 + 搜索窗口切分 + 本地落盘 + 断点记录。*

---

## 〇、先想清楚要什么（别一上来就爬）

**目标不是「全量」，是「每个时期的头部」。**

X 的 Top 排序是黑盒，「全局 top 100 by views」拿不到也不需要。实际做法：

> **按季度切 8 个窗（2 年）→ 每窗收 Top 15–20 条 → 合并按数据排 → 取前 100。**

这样得到的是「他每个阶段什么在涨」——比全局 top 100 **更有用**，因为能看到转型点（ohiain 的三级跳、Za 的爆款-市场状态相关性，见 `../../Fluxus_Brand/research/Fluxus_Za_Ohiain_Study.md`）。

**每条帖要存的字段：**

```json
{
  "id": "2084717176909447635",
  "date": "2026-08-05",
  "text": "全文，含换行",
  "views": 8300, "likes": 52, "bookmarks": 22, "reposts": 3, "replies": 5,
  "has_chart": true, "is_thread": false, "is_qt": false,
  "form": "",       // 后填：形态码，用 Fluxus_Fintwit_Voice_Codes.md 的分类
  "window": "2026-Q3"
}
```

**⭐ bookmarks/likes 比值是这个库最重要的产出** —— 收藏闸的量化指标（Tito 那条 0.67 = 极高；一般帖是零头）。views 是曝光，likes 是立场，**bookmarks 才是购买意向**。

---

## 一、工具选择

| 工具 | 用在哪 | 为什么 |
|---|---|---|
| **Claude in Chrome**（`mcp__claude-in-chrome__*`） | **正式采集** | 用户登录态 —— X 搜索必须登录；in-app browser 未登录只能看单帖 |
| in-app Browser（`mcp__Claude_Browser__*`） | 单帖核对 | 无登录也能读单条（如核对 Tito 帖） |
| WebFetch | ❌ 不能用 | X 对无头请求返回 402 |

---

## 二、采集流程

### 第 1 步 · 搜索 URL（模板）

```
https://x.com/search?q=from%3Aohiain%20since%3A2024-08-01%20until%3A2024-11-01&f=top
```

- `from:` 账号 · `since:/until:` 窗口 · `&f=top` = Top 排序（**必须**，Latest 是时间序会淹没在日常帖里）
- 8 个窗（2 年按季度）。窗口太宽 Top 会被最大爆款屠版，太窄翻页次数翻倍。**季度是实测的平衡点**

### 第 2 步 · 逐窗滚动 + JS 抓取

Discord 那套「JS 读 DOM → 去重 Map → 攒够导出」直接平移。核心抓取器（在 Chrome console / javascript_tool 里跑）：

```js
// 初始化一次
window.__X = new Map();
window.__xgrab = () => {
  document.querySelectorAll('article[data-testid="tweet"]').forEach(a => {
    const link = a.querySelector('a[href*="/status/"]');
    if (!link) return;
    const id = (link.href.match(/status\/(\d+)/) || [])[1];
    if (!id || window.__X.has(id)) return;
    const text = a.querySelector('[data-testid="tweetText"]')?.innerText || '';
    const time = a.querySelector('time')?.getAttribute('datetime') || '';
    // 数据条：aria-label 里是全量文字（"52 likes, 22 bookmarks, 8300 views"格式）
    const stats = a.querySelector('[role="group"]')?.getAttribute('aria-label') || '';
    window.__X.set(id, {id, date: time.slice(0,10), text, stats});
  });
  return window.__X.size;
};
```

**⚠️⚠️ 2026-08-10 首跑实测,三个 SOP 原方案不成立的地方（已修）：**

| 原方案 | 实际 | 改法 |
|---|---|---|
| **本地 HTTP sink 落盘** | ❌ **不成立** —— X 的 CSP `connect-src` 拦截,`fetch` 报 Failed to fetch,`sendBeacon` 返回 true 但一个字节都收不到 | **改走「JS 返回值 → 工具输出 → Bash 落盘」** |
| 一次导出整窗 | ❌ 工具返回值约 **1000 字符**就截断 | **两遍走**：第一遍只取 `id\|date\|flags\|stats`（约 12 条/次），排完序后第二遍按 id 补正文 |
| `-filter:replies` 过滤回复 | ❌ **过滤过头** —— 同一窗 5 条 → 1 条 | **不要用**。回复在后处理里按 `views < 1000` 丢 |

**另外两条实测:**
- **`f=top` 每窗返回的是封顶切片**（实测 1–20 条,不是「Top 15–20」保证）。窗口内容少时就是真的少,不是限流
- **滚动改用 `javascript_tool` 里的 `window.scrollBy()` + `await sleep`** —— `computer` 的滚动每次返回一张截图,8 窗下来图像开销极大。单次 scrollBy 不是定时器循环,不触发后台降频问题

**⚠️ 三个 Discord 爬取时踩过、这里同样适用的坑：**
1. **`stats` 存原始 aria-label 字符串，落盘后再解析** —— 别在浏览器里解析数字（"8.3K"/"12万" 格式随语言环境变，解析错了原始串还在）
2. **滚动用 `computer` 的滚动，不用 JS `setTimeout` 循环** —— 后台 tab 的 JS 定时器被降频，Discord 那次就是这么卡死的
3. **每窗结束立刻导出，别攒到最后** —— 限流/崩溃时已导出的部分不丢

### 第 3 步 · 落盘（本地 HTTP sink，Discord 同款）

浏览器下载被挡，用本地 sink：

```bash
# 终端起一个（Discord README 里有完整版）
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        open(sys.argv[1],'ab').write(self.rfile.read(int(self.headers['Content-Length'])))
        self.send_response(200); self.end_headers()
HTTPServer(('127.0.0.1', 8791), H).serve_forever()
" data/research/ohiain_raw.jsonl
```

```js
// 浏览器侧：每窗跑一次
await fetch('http://127.0.0.1:8791/', {method:'POST',
  body: JSON.stringify([...window.__X.values()]) + '\n'});
window.__X.clear();   // 清掉，下一窗从零计
```

### 第 4 步 · 断点记录

每完成一个窗，在本文件末尾的「进度表」记一行。**限流是常态不是事故** —— X 连续翻页十几页后会停止加载新内容，这时：停 15–30 分钟，或先换下一个窗口（不同 query 的限流桶有时分开）。

### 第 5 步 · 后处理（落盘之后，脚本做）

1. 解析 `stats` 原始串 → views/likes/bookmarks/reposts/replies 数值列
2. 合并 8 窗 → 按 views 排 → 取 top 100 → `ohiain_top100.json`
3. 算 **bookmarks/likes 比值列**，按它再排一次 —— 这个榜和 views 榜的差集就是「被低估的判据帖」
4. 形态标注（`form` 字段）用 `Fluxus_Brand/research/Fluxus_Fintwit_Voice_Codes.md` 的分类，标 top 100 就够，别标全量

---

## 三、分析产出的固定格式

每个账号出两个文件：

| 文件 | 内容 |
|---|---|
| `data/research/<handle>_top100.json` | 机器可读，字段见上 |
| `Fluxus_Brand/research/Fluxus_<Handle>_Corpus.md` | 人读的：**① views top 10 ② bookmarks/likes top 10（两榜差集单独标）③ 形态分布 ④ 按季度的转型点 ⑤ 和我们音区的重合/边界** |

分析框架直接接 `Fluxus_Za_Ohiain_Study.md` 的四点轨迹法 —— 这个库就是给那份定性研究补定量底座。

---

## 四、规矩

1. **只存不引。** 库里的每一个字都是别人的。引用走 Swipe File 的门槛（答不出「装我的哪段素材」不入库），拆结构走「只拆不引」。
2. **数据是快照。** views/likes 会继续涨，落盘时间就是口径时间，写进文件名或字段，别回头更新（没有意义，趋势才有意义）。
3. **别爬回复/评论区。** 只要主帖。评论区是蹭号（REPLY）的实时活，不是库的活。
4. **一个账号一次会话。** 限流按账号+登录态算，同一天爬两个号会互相挤兑。

---

## 五、进度表

| 账号 | 窗口 | 状态 | 落盘文件 | 日期 |
|---|---|---|---|---|
| @ohiain | 2024-Q3 → 2026-Q3（8 窗） | ✅ **完成** 79 条抓取 / 72 条有效 | `ohiain_index.csv` · `ohiain_top100.json` | 2026-08-10 |
| @ZaStocks | 2024-Q3 → 2026-Q2（8 窗） | ✅ **完成** 71 条有效 | `zastocks_index.csv` · `zastocks_top100.json` | 2026-08-10 |
| @thesetupfactory | 2025-01 → 2026-Q2（5 窗，他 2025-01 才开始发） | ✅ **完成** 39 条有效 | `tsf_index.csv` · `tsf_top100.json` | 2026-08-10 |
| @Clement_Ang17 | — | ⬜ **下一个**(音区标杆,小号) | — | — |

---

## 六、启动口令

下次要跑，对 Claude 说：**「按 `data/research/README_x_account_scrape.md` 爬 @某某」**。
Claude 应当：起 sink → 用 Claude in Chrome 开第一个窗 → 逐窗滚动抓取导出 → 更新进度表 → 跑后处理 → 出两份产出文件。

# x_watch · 抓取器

**这是机械活的那一半** —— 拉帖、落盘、算提及。判断(立场、日报、评分)由 Claude 读 jsonl 后写,不在这里。

## 一次性

1. Andy 去 https://twitterapi.io/dashboard 注册取 key(有免费额度,注册与付款只能他本人做)
2. 写进仓库根 `.env`(已被 gitignore):
   ```
   export TWITTERAPI_KEY=xxx
   ```

## 冒烟测试(先跑这个)

```bash
.venv/bin/python Fluxus_Brand/ops/tools/x_watch/fetch.py --probe
```

**要盯的是两行:** `bookmarkCount` 和 `viewCount` 有没有值。**收藏比是我们最重要的量,这两个字段缺一个,这条路就得重估。** 顺带确认 `/twitter/list/members` 能返回 Copybook 的成员 —— 那正是浏览器法一直读不出来的东西。

## 首跑(回抓周五周六)

```bash
.venv/bin/python Fluxus_Brand/ops/tools/x_watch/fetch.py --since 2026-09-04 --until 2026-09-06
```

## 每天

```bash
.venv/bin/python Fluxus_Brand/ops/tools/x_watch/fetch.py --days 1
```

09:00 JST(= 前一日 20:00 ET,收盘后 4 小时)。

## 产出

| 文件 | |
|---|---|
| `data/content/x_watch/posts/YYYY-MM-DD.jsonl` | 原始,一行一帖,含 views/likes/bookmarks/replies/reposts + 抽出的 ticker |
| `data/content/x_watch/members.json` | List 成员快照 —— **用它和 roster 对账** |
| `data/content/x_watch/mentions.csv` | 累加。`stance` 列留空,由 Claude 回填 |
| `data/content/x_watch/runlog.csv` | 每次运行的分钟数、页数、条数、人数 —— **这是「要不要继续花钱」的账** |

## ticker 抽取的诚实边界

带 `$` 的直接认。不带 `$` 的裸大写词认 2–5 字母、且不在停用词表里 —— **这一定会有假阳性**(人名、缩写)。停用词表在 `fetch.py` 顶部,发现漏网的往里加。**别把提及榜当成精确计数**,它是排序用的。

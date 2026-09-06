# 2026-09-06 · Vercel 部署存储 125.62 GB（上限 10 GB）

**发现方式**：Vercel 发邮件说接近上限。**不是我们量出来的** —— 这才是事故的本体。

## 读数

| 项 | 值 | 出处 |
|---|---|---|
| Deployment Storage | **125.62 GB** | Vercel Usage 页，2026-09-06 |
| Functions Storage | 173.02 MB | 同上（无关，静态站） |
| 套餐 | Hobby | 同上 |
| 每次部署产物 | ~100 MB（实测 100.6 MB 源侧） | `audit_deploy_cost` |
| 14 天 main commit | 781 次 | `git log origin/main --since='14 days ago'` |
| 其中触及前端产物 | **56 次（7.2%）** | 同上，按路径过滤 |

125.62 GB ÷ 30 天保留 ÷ 56 次每天 ≈ **75 MB/次**（压缩后），与源侧 100 MB 相符。

## 根因

**触发器比内容变得频繁。**

每推一次 main 就是一次生产部署。而 main 上 92% 的 commit 是研究笔记、契约行、
品牌稿、测试——一个字节都不进浏览器，却每次都重新构建并存下 100 MB 产物
（60 MB `data/output` + 40 MB `modelbooks/ohlcv` + 2 MB 应用代码）。

**真正的应用只有 2 MB，98% 的存储是数据；而这份数据被复制了 1600 多遍。**

三个乘数各自都对，没人管乘积：
- 写文档的人：每次 commit 都该 push（铁律一）✓
- 产线：每晚更新 `data/output` ✓
- 前端：产物就该带上它要服务的数据 ✓
- **乘积**：100 MB × 56/天 × 30 天 = 168 GB —— 没有主人

## 处置（当日完成）

1. **`vercel.json` 加 Ignored Build Step**（commit `89c59a1d`）
   `scripts/vercel_ignore_build.sh`：只有 `frontend/`、`data/output/`、`vercel.json`、
   `package.json`、`package-lock.json` 变了才构建。约定 exit 0 跳过 / exit 1 构建；
   拿不到父 commit 时**兜底偏向构建**。
   14 天回放：781 → 56 次。
2. **保留期分级**（Vercel 后台，当日改）
   Canceled 30天→**1天** · Errored 30天→**1周** · Pre-Production 30天→**1周** ·
   Production 30天→**2周**。已保存并刷新核实。
   （Vercel 侧删除的部署 30 天内仍可恢复，所以这不是不可逆动作。）
3. **`pipeline/tools/audit_deploy_cost.py`**（commit `4c7dd3c8`）接进 weekly-data-audit。

处置后预测：100 MB × 4/天 × 14 天 = **5.5 GB**，预算内。

## 三条可迁移的教训

**① 检查的对象是乘积，不是任何一个乘数。**
每条 commit 对、每次部署对、每份数据对——爆的是乘积。凡是「A × B × C 有上限」
而 A/B/C 分属不同的人，就必须有一个东西专门盯乘积。

**② 「有没有闸」是个 bool，缺口住在集合里。**（同 [[pitfall-has-x-is-a-bool-the-gap-is-a-set]]）
D1 查的不是 ignoreCommand 存不存在，是**产物的每一个来源是否都在闸的看管范围内**。
漏一条路径的后果比没有闸更坏：部署照跑、构建照绿，只有内容静默停在旧版。

**③ 检查的分辨率决定它的阴性有没有意义。**（同 [[pitfall-my-gate-had-no-resolution]]）
D3 第一版在真实仓库上报「无问题」，而 modelbooks（40 MB、上次变更 2026-03-31）
就在那儿——它住在 `frontend/public/data` 下一层，父目录里有天天变的小文件把
子树年龄洗新了。**被测的东西在那个粒度下物理上不可见。** 已改成逐层下钻并写了
回归测试锁住这个形状。

## 未做（下一轮）

- `frontend/public/data/modelbooks/ohlcv` 40 MB / 1535 文件，上次变更 2026-03-31，
  占每次产物 40%。搬出产物（Vercel Blob 或外部拉取）可再砍四成。需要动前端取数
  路径，属前端线，留给决策。

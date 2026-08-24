# Fluxus_Brand — 品牌与内容资料

> ## 🎛 **先看 [`CONTROL.md`](CONTROL.md)** —— 现状 / 决策台账 / 「我要做 X 该开哪个」查表。
> 本 README 是目录地图,CONTROL 是前门。

*2026-08-03 从仓库根目录整理进来。根目录原本散着 41 个 .md，现在剩 4 个。*
*旧路径 → 新路径的完整对照在 [`_MOVED.json`](_MOVED.json)。*

---

## 目录

| 文件夹 | 装什么 | 什么时候来这儿找 |
|---|---|---|
| **[voice/](voice/)** | 声音、语料、金句、借来的台词 | 写任何对外文字之前 |
| **[ops/](ops/)** | 行动计划、内容运营、周计划、X playbook | 决定「发什么、发哪里、多久发一次」 |
| **[templates/](templates/)** | 周信模板、日更 recap 标准件 | 开写一期新东西 |
| **[record/](record/)** | H1 思考时间轴、复盘模板 | 写业绩/复盘类内容 |
| **[research/](research/)** | 竞品拆解、Substack/Fintwit 调研、蹭号名单 | 做定位判断、找对标 |
| **[visual/](visual/)** | 视觉库、图像方法、海报系统 | 配图、做视觉 |
| **[site/](site/)** | 官网首页文案、课程页文案 | 改 fluxus-capital.com |
| **[copybook/](copybook/)** | 每日临帖的规格、名单、台账 | 日常临帖 |

---

## 最常用的六个

| 文件 | 是什么 |
|---|---|
| [voice/Fluxus_Voice_Bible.md](voice/Fluxus_Voice_Bible.md) | ⭐ **声音的唯一真相** —— 人设、演员表、寄存器、承诺规则 |
| [voice/Fluxus_Own_Lines.md](voice/Fluxus_Own_Lines.md) | ⭐ 192 条自有金句（145 条你的 + 47 条借来的影视台词，带黑名单和使用规矩） |
| [ops/Fluxus_Action_Plan.md](ops/Fluxus_Action_Plan.md) | 三层结构（X / Substack / Discord）、读者定义、刊名与承诺 |
| [ops/Fluxus_Content_Ops.md](ops/Fluxus_Content_Ops.md) | 路由表、日/周流程、自动化分级、**七道闸** |
| [record/Fluxus_H1_2026_Timeline.md](record/Fluxus_H1_2026_Timeline.md) | H1 思考主线，全部带日期，含 3/20 合流专块 |
| [templates/Fluxus_Daily_Recap_Format.md](templates/Fluxus_Daily_Recap_Format.md) | 日更 recap 九块骨架（已在跑的成品） |

---

## 没有移动的（故意留在根目录）

这几个是仓库基建，不是品牌资料，动了会有连带成本：

| 文件 | 为什么留在根 |
|---|---|
| `plan.md` | 管线代码里有 22 处 docstring 引用它的章节号（`plan.md §2.4`） |
| `PERFORMANCE_TRUTH.md` | 对外业绩的唯一真相，`pipeline/portfolio/truth_snapshot.py` 按根路径生成 |
| `performance_truth.json` | 同上，机器可读副本 |
| `TODOS.md` · `DESIGN.md` | 约定俗成的根目录文件；design 类工具默认在根找 `DESIGN.md` |

**也没动**：根目录的 `esplan_*.csv` / `optionplan_*.csv` / `agent-tasks*.txt`。那些是脚本产出物，路径可能被读，动之前要先查脚本。

---

## 相邻的几个文件夹（本来就在，没动）

| | |
|---|---|
| `Fluxus_Substack/` | 周信的实际稿件：`drafts/`（含 `H1_flagship/`）+ `assets/`（配图）+ 定位/定价文档 |
| `Fluxus_References/` | 交易类 PDF 书库 |
| `Fluxus_Receipts/` | 发文台账 |
| `visuals/` | 视觉素材筛选台（544 张候选图 + 挑图流程） |
| `docs/` | 项目文档；新收了 `research.md`、`Position_Sizing_Knowledge_Index.md`、`Notion_Workspace_Audit_Report.md` |

---

## 引用有没有断

搬完做了一次全仓链接校验：**169 处引用全部解析成功，0 断链。**

包括仓库外的 memory（`~/.claude/projects/.../memory/`）—— 那 13 个文件里提到的路径也一起改了，用的是仓库相对路径（不是一长串 `../`）。

搬家脚本留在 [`scripts/organize_root_docs.py`](../scripts/organize_root_docs.py)，带 `--dry-run`。
⚠️ 它有一个已知坑：文件名互为子串时会误伤（`research.md` 曾被从 `project_fintwit_100_research.md` 里切出来）。已修，但下次再用要先跑 dry-run 并肉眼扫一遍结果。

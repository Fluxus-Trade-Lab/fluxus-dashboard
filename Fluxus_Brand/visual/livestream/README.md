# 会员直播画面卡（T-1002-78）

会员直播系列（策划页 https://claude.ai/artifact/UCsft7bmqfxm1WsZAoXPaQ ，Andy 10-02 定：Discord 舞台播出 +
本机 OBS 同录原片，首场 10/3）的 OBS 画面素材。版式照抄课程发布视觉母版（`../course_launch/`），
不新造风格：暖石底 `#F2F1ED`、墨色 `#1c1917`、IBM Plex 三族、无渐变无阴影无辉光。

## 这个目录有什么

| 文件 | 是什么 |
|---|---|
| `make_livestream_cards.py` | 生成器，场次号+标题是参数，每场直播改两个 flag 重出全套 |
| `out/ep<NN>/` | 某一场的全部 PNG，首场是 `out/ep01/` |
| `preview_ep01.html` | 首场预览画廊，9 张图 base64 内嵌，离线可直接用浏览器打开（claude.ai Artifact 工具在本会话运行时不可用，按 `daily-page` skill 的降级规矩落仓库 HTML，诚实降级） |

每场固定 9 张图，1920×1080（OBS 画布标准）：

| 文件名 | 用途 |
|---|---|
| `00_title.png` | 片头卡 |
| `01_segment_1.png` … `06_segment_6.png` | 6 张段落卡（① 今天的盘 ② 本章一张图 ③ 三个案例 ④ Dashboard 实操 ⑤ 会员问答 ⑥ 作业与下一场），文件名前缀的序号同时是剪辑切点编号 |
| `99_closing.png` | 片尾卡 |

## 怎么生成

```bash
python3 Fluxus_Brand/visual/livestream/make_livestream_cards.py \
  --episode 1 \
  --title "先看环境" --title-en "Read the Environment First" \
  --date "2026-10-03" \
  --name "Andy" --name-sub "FLUXUS CAPITAL"
```

下一场只需要换场次号和标题：

```bash
python3 Fluxus_Brand/visual/livestream/make_livestream_cards.py \
  --episode 2 --title "<第二场标题>" --date "2026-10-10"
```

只想重出一类（比如改完名牌条文字只要那一张）：`--only lowerthird`（可选 `title` / `segments` / `closing` / `lowerthird`）。

中英参数独立：`--title`/`--title-en` 各一份；6 个段落名目前写死在脚本里（`SEGMENTS` 常量，中英各一份），
因为这 6 段是 Andy 定的固定结构，不随场次变化——要改段落名本身（不是标题），改脚本里的 `SEGMENTS` 列表，
改一次全场次生效（继承 `make_data_card.py` 的「改母版不改单张」规矩）。

**只出中文优先**：模板里中文永远显示；`--title-en` 留空时标题卡/片尾卡的英文副标题行不渲染，不会出现空行。

## 怎么导进 OBS

1. **场景**：建 8 个场景（或 1 个场景 + 8 个“图片源”互相切换）——片头、段落 1–6、片尾，每个场景放一个「图像源」指到对应 PNG，铺满画布（1920×1080，和 PNG 原始尺寸一致，不用缩放）。
2. **切场次序**：片头 → 段落 1–6（段落卡本身就是剪辑切点，正式回放剪辑时按这 6 个文件名切分）→ 片尾。建议给每个场景配一个 Stream Deck / 热键，直播中按顺序切。
4. **换场次**：下一场直播前重新跑一遍生成命令（换 `--episode`、`--title`、`--date`），OBS 场景里的图像源路径不变（`out/ep01/...` → 改场次后变 `out/ep02/...`，需要在 OBS 里把每个图像源的文件路径指向新一场的目录，或者固定用一个 `out/current/` 软链接/复制覆盖，减少每场改源）。

## 字体依赖

同 `make_data_card.py`：字体来自 `Fluxus_Brand/visual/explorations/2026-08-08/fonts/`（IBM Plex 系列 woff2），
缺字体脚本直接报错，不回退系统字体（海报系统规矩）。渲染用本机 Chrome headless（`/Applications/Google Chrome.app`）。

## 透明背景怎么做到的

Chrome headless 默认截图背景是白色；传 `--default-background-color=00000000` 让页面默认背景变透明，
配合 HTML/CSS 里不设置 `body{background}`（或显式设 `transparent`），截图出来的 PNG 就带真实 alpha 通道
（已用 Pillow 验证：条外像素 `(0,0,0,0)`，条内像素 `(28,25,23,235)` ≈ 92% 不透明）。这个技巧目前只在
`lowerthird.png` 用到；片头/段落/片尾卡是实色背景（1080p 全屏画面），不需要透明。

> 2026-10-03 Andy：「下三分之一名牌条（透明底，叠加用） · lowerthird.png 这个去掉。」——名牌条不再默认生成、不进 OBS；代码保留，`--only lowerthird` 仍可单出。

# 课程发布视觉母版（T-0919-70，Vera）

*课程发售 09-25（Andy 09-19 定）预热期的视觉框架。字段/数字全部来自已核实出处或明确留白，不代笔文案。*

## 这个目录有什么

| 文件 | 是什么 | 状态 |
|---|---|---|
| `../../../scripts/make_data_card.py` | 数据卡生成器（数字大字体+一句话结论），Steve/Mia 每天套用的母版 | 可用，已测试渲染 |
| `2026-09-21_trust_86pct.png` | 用母版渲染的示例：86%/8-14 信任背书卡（排期表 09-21 那条） | 数字有出处，可直接用 |
| `landing_hero_framework.html` | 落地页视觉框架（hero / 课程结构 L1–L5+MU / 价格卡），字段占位 | 结构定稿，等 Mia 文案+ Andy 校完课程正文才能填字 |

## 视觉系统（继承 `Fluxus_Poster_System.md`，不新造）

暖石底 `#F2F1ED` · 墨色 `#1c1917` · 次级字 `#57534E` · 测量灰 `#948F86` ·
IBM Plex Sans / Condensed Bold / Mono，无渐变无阴影，字体自托管（缺字体直接报错，不回退系统字体）。
理由：课程是 Fluxus 品牌的一个交付物，不该另起一套视觉语言——读者认的是框，不是这次配的图（海报系统 §〇）。

## 数据卡怎么用（Steve/Mia 每天套模板）

```bash
python3 scripts/make_data_card.py \
  --number "66.5%" \
  --en "Unconfirmed breakouts. 66.5% fall back below the breakout level within 10 days." \
  --zh "无量突破，66.5% 十天内跌回突破位下方。" \
  --meta "SOURCE: material_inbox 09-13 · 无量 vs 带量突破" \
  --out "Fluxus_Brand/visual/course_launch/2026-09-22_rvol.png"
```

`--meta` 必须写实出处，脚本会拒绝空值——数字只有一个家，卡片上的数字也一样要能查到源头。

## ⛔ 明确不做的三件事（附出处，别按任务书字面执行）

任务原文（T-0919-70）写「进度截图美化、倒计时卡片、课程内页截图裁切」，三件都与已批规矩冲突，**认领时已按下方裁定不做**：

1. **不做倒计时卡片。** `Fluxus_Build_In_Public.md`（08-03，Andy 已批）硬门槛第一条「不预告，只报过去式」；`Fluxus_Course_Launch_2026-09-25.md` §〇 与 build-in-public brief 均已现场确认这条未被 Andy 豁免。Marketing Steve 09-19 已挂门铃提醒同一冲突（INBOX `🔔 [09-19] → Visual Vera`），核对后未找到 Andy 现场豁免的原话，按旧规矩执行。
2. **不做课程内页截图裁切。** brief 末节明写「不做课程截图（课程还没公开，且违反『不发代码/教材截图』的边界）」；课程正文本身 Andy 09-19 仍在校对中，没有可截的定稿页面。
3. **不预先做发布日官宣卡（含真实价格 $1,499 / 日期 09-25）。** brief 末节：「09-25 之前不得预先做出这张图并流出」——这张图本身就含禁止提前公开的信息，且仓库是 public（`project_repo_is_public.md`），进仓库等于对外发布。`landing_hero_framework.html` 的价格卡区域因此只留 `{{ PRICE }}` 占位符。

如果 Andy 现场明确要例外（比如真要倒计时），需要一句原话留痕（登记进 `Fluxus_Course_Launch_2026-09-25.md` 或 §七），不能默认字面执行任务标题。

## 待办 / 交给下一棒

- 09-20/09-22/09-24 三条数据卡（RVOL、波动率表、MU 口径）：等 Mia 把 Studio Q 素材改写成遮蔽课程细节的成稿后，套 `make_data_card.py` 当天出图，本卡不预先生产（避免抢在文案确认前定型措辞）。
- `landing_hero_framework.html`：等 Claire 定了售卖入口（Vercel/Squarespace，T-0919-65）+ Mia 交文案，把占位符替换成真值；L1–L5+MU 的具体主题等 Andy 校完课程正文再填。
- 价格卡官宣图：09-25 前一天再做（不流出），由 Vera 或当值线临场出。

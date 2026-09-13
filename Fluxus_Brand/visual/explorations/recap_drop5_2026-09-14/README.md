# 复盘掉落线 · 源头在哪（2026-09-14）

| 层 | 权威源 | 谁改 |
|---|---|---|
| 颜色、尺寸、位置（CSS） | `recap_ab_2026-09-04/build_recap.py` 的 `CSS = """…"""` 块，产线 `pipeline/content/recap/visual_assets/recap_visual.css` 逐字抄它 | Visual Vera |
| 线的几何、灰尾、落点、标签、标题拼接（JS） | `pipeline/content/recap/visual_assets/recap_page.js` | OPS Fable 按 §七 契约行落地 |
| 用哪几个收盘 | `pipeline/content/recap/visual.py` | OPS Fable |

`recap_ab_2026-09-04/` 与 `recap_ab_2026-09-11/` 两个生成器是 09-12/13 的 A/B 探索快照，线仍是 21 日版；它们不再是几何的源头，不跟着改。

## 定稿沿革（全部 Andy 原话见 daily-recap skill 裁决记录）

1. 09-13 线宽 2.5px、居中占版心 84%、高度随曲线、收盘空心圆 r=4.5px、删副标题 —— `build_final_form.py`
2. 09-13 主标题在自己的破折号处折行，放不下退回 `pretty` —— `../recap_title_wrap_2026-09-13/build_title_wrap.py`
3. 09-14 Andy：最近 5 个交易日；日报最后一天橙、前面渐变灰；周报全橙；标签日报 `#09-11`、周报 `Week37 · 当周区间`（OPS 落地 `93803e32`）
4. 09-14 Visual Vera 判（OPS 交来的两处）—— `build_drop5.py` / `drop5_preview.html`
   - **一天 = 一段**：日报 6 个收盘（5 段，橙色是最后一天那段）；周报 = 上周最后一个收盘 + 本周每个交易日（普通周 6 点，W37 劳动节周 5 点），线和 `09-08 → 09-11` 标签一致
   - **加高**：`dropLine()` 横向跨度 20 → 10；CSS `.drop.thin` 加 `max-height:160px`（剧烈的周形状照画、整体缩小）。样本 100 个交易日：线高中位 99px（21 日版 128px，5 点跨度 20 仅 46px），16% 触顶

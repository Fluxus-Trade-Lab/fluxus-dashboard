# 角色 · 出图简报（可直接投喂图像模型）

*用法:第 4 节起是英文,整段复制给图像模型。前三节是给人看的判断依据。*
*母文件:`Fluxus_Character.md`(他是谁、出现在哪、三条不许)*

---

## 一、一句话

**一个在等的人。** 坐在一整面亮着的读数墙前面,手是停着的。
喜剧在比例里:三千个名字扫完、十二条规则跑完 —— 结论是一个词,等。

**他不是大师。** 这个品类里全是大师,反大师才是位置。

---

## 二、参考谁(校准用,不是让模型抄)

| 参考 | 取它什么 | 不取什么 |
|---|---|---|
| **Sempé** | **最关键的一条:极小的人 + 极大的环境。** 整个构图逻辑来自这里 | 他的巴黎温情;我们要更冷 |
| **Saul Steinberg** | 线条即思考;官僚荒诞;画面里出现手写字和图表 | 他的超现实变形 |
| **Ronald Searle** | 墨线的力道和抖动,排线阴影 | 他的尖刻和怪诞程度 |
| **teenage engineering《Mr. Update》** | 把「品牌真正在做的事」拟人化;冷规格表紧挨着暖画面 | 别画成他们那个人 |
| **早期 A24 海报 / Popeye 杂志插画** | 干净但有态度;日系的松弛;不用力 | —— |

> 给图像模型的提示词里**不写艺术家名字**,只写这些参考带来的**性质**(见第 4 节)。
> 一是效果更稳,二是不去仿在世创作者的个人风格。艺术家名字留给你和插画师沟通时用。

## 三、明确否定谁(这一栏比上一栏重要)

- ❌ **Corporate Memphis** —— 那种大头小身、扁平撞色的 SaaS 插画。第一要杀的
- ❌ 企业吉祥物(Duolingo 猫头鹰那一路);他不是 logo
- ❌ 华尔街符号:公牛、熊、上升箭头、飘落的钞票、K 线背景
- ❌ 交易员刻板印象:吊带裤、双手各一部电话、对着屏幕吼
- ❌ 大师/禅意:僧袍、蒲团、盘腿、山顶、香、莲花
- ❌ 炫富:游艇、跑车、雪茄、名表
- ❌ 赛博朋克 / 霓虹 / 「金融科技未来感」/ HUD 界面
- ❌ 3D 渲染、渐变、高光、玻璃拟态
- ❌ 动漫 / 漫画式大眼睛 / 表情夸张
- ❌ AI 插画的通用长相:平滑矢量、粉彩、对称构图、过度可爱

---

## 四、Master prompt（英文，直接复制）

```
A wide horizontal pen-and-ink cartoon scene, drawn by hand.

SUBJECT — MR. FLUXUS: a middle-aged East Asian man with a round face and
full cheeks, slightly heavyset. He wears a black knitted bucket hat with a
visible crochet texture, pulled low; thin round gold wire-rimmed glasses;
and a rumpled checked button-up shirt, sleeves pushed up. Expression:
deadpan with a faint hint of grumpiness — the face of a man who has been
asked for stock tips one time too many. Not sad, not smug, never smiling.
He must NOT look cool, heroic, or successful — he looks like an ordinary
tired man doing paperwork. He is small in the frame. His hands are still,
one holding a transparent ballpoint pen.

ENVIRONMENT — A small home trading den, not an office: a desk with several
monitors on arms, the charts on them drawn as loose hand-inked squiggles
(never realistic UI), lace curtains behind, a half-finished mug of tea,
and geological strata of paper on the desk — stopped-out order slips, each
stamped NO. A plump indifferent cat sleeps next to the keyboard. One desk
drawer sits slightly open, with a small hand-lettered label reading
"OLD THESIS". Domestic, cluttered, unglamorous.
(The analogue 1970s instrument-wall of v1 is NOT dead — it has moved: it now
lives only in the brain-world scenes, see the spec's inner-world rules.)

THE JOKE — Everything about him says small, ordinary, losing-most-days.
The stack of NO-stamped slips keeps growing. He is completely fine.

PROPS — A hand-lettered cardboard sign propped on the desk reading
"NOT FINANCIAL ADVICE". A rubber stamp. One small open notebook with a
single line written in it. The stamped word NO may be the picture's single
burnt-orange (#D1600F) element.

STYLE — Hand-drawn ink line with visible variation in line weight, slightly
imperfect, confident. Shading built from cross-hatching only — no grey fills,
no airbrush, no gradients. Loose, economical linework. The signs and any
lettering in the drawing are hand-lettered.

COLOUR — Black ink on a flat warm off-white background (#F4F3F0). Exactly one
accent colour, a burnt orange (#D1600F), used on no more than one small
element in the whole picture. Everything else is black and paper.

COMPOSITION — Wide horizontal format, roughly 16:9. Generous empty space.
The figure occupies less than a quarter of the frame. Flat background — no
vignette, no frame, no border, no drop shadow, no texture overlay.

DO NOT INCLUDE — no charts or candlestick graphs, no arrows, no upward or
downward trend lines, no bulls or bears, no currency symbols, no falling
money, no computer screens or glowing monitors, no neon, no 3D rendering, no
gradients, no glossy highlights, no flat vector "corporate" illustration
style, no oversized head or exaggerated cartoon proportions, no anime styling,
no logos or brand marks, no smiling, no suit and tie, no yacht, no city
skyline, no robot, no hooded figure, no glowing eyes, no transformation
effects, no heroic low-angle shot, no lens flare, no clenched fist of
determination, no "focused genius" trope, no monk, no meditation pose.
```

---

## 四点五、Model-sheet prompt（定妆表 —— 第一批产出）

*定妆表先于一切场景图。五个场景必须是同一个人,这页就是「同一个人」的定义。*

```
A character model sheet, hand-drawn in pen and ink on a flat warm off-white
page (#F4F3F0), laid out like an animator's reference sheet with small
hand-lettered labels. Cross-hatched shading only, no grey fills, no
gradients. Roughly 4:3 landscape.

ROW 1 — THE SAME MAN, THREE VIEWS: front view, three-quarter view, profile.
A middle-aged East Asian man, round face, full cheeks, slightly heavyset,
wearing a black knitted bucket hat with visible crochet texture pulled low,
thin round gold wire-rimmed glasses, and a rumpled checked button-up shirt.
Identical hat, glasses, shirt and body in all three views.

ROW 2 — EXPRESSION STUDIES, three heads: (a) baseline deadpan; (b) faintly
annoyed, eyes half-lidded, being asked for a stock tip; (c) asleep upright
in a chair, glasses slipping, a small hand-drawn "zzz". No smiling, no
glowing eyes, no heroic expressions.

ROW 3 — PROP STUDIES, drawn separately and labelled by hand: the black
knitted bucket hat; the round gold wire glasses; a rubber stamp and the
stamped word "NO" (this stamped NO, in burnt orange #D1600F, is the only
colour on the page); a transparent ballpoint pen; a mug of tea; a
hand-lettered cardboard sign reading "NOT FINANCIAL ADVICE"; a desk drawer,
slightly open, with a hand-written label "OLD THESIS".

ROW 4 — THE CAT: a plump indifferent cat, two poses: curled asleep beside
a keyboard; standing on the keyboard mid-mischief, one paw on a key.

DO NOT INCLUDE — no charts, no candlesticks, no arrows, no bulls or bears,
no currency symbols, no computer screens, no neon, no 3D rendering, no
gradients, no flat corporate vector style, no anime, no oversized head
proportions, no smiling, no suit, no glowing eyes, no heroic poses.
```

*猫是真实存在的那只 —— Andy 若提供猫的照片,把品种特征(毛色/花纹)补进 ROW 4;
没有照片就先按 "plump indifferent cat" 出,后补。*
*抽屉标签公开版用 "OLD THESIS";内部版可用 "BABA"(H1 审计的实价出处)。*

---

## 五、场景变体（同一个人，换情境 —— 静态吉祥物三个月就死了）

每条接在 Master prompt 后面，替换 SUBJECT / PROPS 两段：

```
[WAIT]      He is pouring tea, back to the wall. Sign reads "NOT A CALL".

[ADD]       He has finally stood up — but has taken exactly one step away
            from the desk. Sign reads "ONE STEP".

[REDUCE]    He is switching the wall off, one small lamp at a time, standing
            on a short stepladder. Most of the wall is already dark.

[STOPPED]   A single sheet of paper on the desk. He is pressing a rubber
            stamp onto it. The stamp reads "NO". He is not upset — he is
            filing it.

[NULL]      He is feeding a thick stack of research papers into a paper
            shredder, expression completely unchanged.
```

---

## 六、交付规格（给模型或插画师）

```
比例      16:9 主用 · 另出一版 4:5 给 X 和信的封面
分辨率    长边 ≥ 3000px
背景      纯平 #F4F3F0,或透明 PNG。不要任何纹理、噪点、做旧
文件      PNG,线条边缘干净可抠
一致性    五个场景必须是同一个人 —— 同发型、同衬衫、同体型、同桌子
```

---

## 七、验收（三条，任何一条不过就重来）

1. **把画面缩到 400px 宽**,还能看出"人很小、墙很大"这个比例吗?
   —— 看不出就是构图败了,不是细节问题。
2. **遮住牌子上的字**,还能感觉到他在"不动"吗?
   —— 要靠姿态,不能靠文字解释。
3. **它像不像一张理财 App 的插画?**
   —— 像就是失败。这张画必须让人第一眼**不觉得跟市场有关**。
4. **剪影测试:** 涂黑整个人形,只留轮廓 —— 渔夫帽 + 圆镜 + 格衬衫的组合还认得出是他吗?
   认不出就是三件套画弱了。
5. **反英雄测试:** 他看起来像一个会赢的人吗? —— **像就重来。**
   这张脸必须属于一个胜率四成、靠纪律活着的人。

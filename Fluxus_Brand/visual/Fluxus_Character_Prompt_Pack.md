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

SUBJECT — An ordinary office worker in his forties, seated at a plain desk,
doing absolutely nothing. Deadpan expression: not sad, not smug, not amused.
Slightly rumpled shirt, sleeves pushed up, unremarkable haircut. He is small
in the frame. His hands are still — resting on the desk, or holding a mug of
tea. He is NOT looking at the wall behind him.

ENVIRONMENT — Behind and above him, an enormous wall of instruments and
readouts fills most of the picture: rows of small dials, gauges, printed
tickers, pinned sheets of paper, tiny numeric displays, a paper tape spilling
onto the floor. Everything on the wall is switched on and busy. The wall
dwarfs him. Analogue and mechanical, like a 1970s control room — not screens,
not futuristic.

THE JOKE — The whole apparatus is running at full tilt and the man is doing
nothing. That contrast is the entire content of the drawing.

PROPS — A small hand-lettered cardboard sign propped on the desk reading
"NOT A CALL". A rubber stamp on the desk. One small open notebook with a
single line written in it.

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
skyline, no robot, no hooded figure, no monk, no meditation pose.
```

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

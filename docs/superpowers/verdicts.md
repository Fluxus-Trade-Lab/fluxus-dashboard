# Skill 裁决记录

*所有 skill 的裁决集中记这里（第三方的不改原文件；自建的在各自 SKILL.md 末尾也有一份）。格式：`### [日期] <批/划/改/退> · skill · 一句话`。三次律接口：同一 skill 被划三次 → 必须改或退。*

### [2026-09-04] 批 · superpowers:brainstorming · 第一次真用，两问定 skill-os 架构
### [2026-09-04] 批 · superpowers:writing-plans · 产出 v1 计划；v1 被官方对账推翻是设计的错不是它的错；v2 重写沿用
### [2026-09-04] 退 · gstack 全套（56 件） · Andy 原话「同意先retire/删除 gstack」；零调用、与周检/HANDOFF/code-review 重复；目录整套在 `~/.claude/skills/_retired/`，搬回即恢复。存活的用户级 skill 只剩 6 个：lieflat-charts · openmaic · podcast-to-md · shuorenhua · video-subtitles · youtube-clipper
### [2026-09-04] 退 · lieflat-charts · dataviz 覆盖且更好；锁色系与 DESIGN.v2 冲突、非商用许可；已 mv 到 `~/.claude/skills/_retired/`
### [2026-09-04] 退 · openmaic · 课堂生成器安装向导，与十四情境无一对应，零调用；已 mv 到 `~/.claude/skills/_retired/`
### [2026-09-04] 退 · youtube-clipper · 零调用、无「剪 YouTube 短视频」情境，两步分别被 podcast-to-md / video-subtitles 做掉；已 mv 到 `~/.claude/skills/_retired/`
### [2026-09-04] 退 · ui-ux-pro-max@ui-ux-pro-max-skill（插件） · 零痕迹或用两天即停；UI 线视觉决策走 DESIGN.v2 + artifact-design；enabledPlugins 设 false
### [2026-09-04] 退 · frontend-design@claude-plugins-official（插件） · 零痕迹或用两天即停；前端设计口径在 DESIGN.v2，不需要第二个审美源；enabledPlugins 设 false
### [2026-09-04] 退 · vercel@claude-plugins-official（插件） · 零痕迹；部署走 main→Vercel 自动，deploy --prod 需 Andy 先批，不该 skill 一键化；enabledPlugins 设 false
### [2026-09-04] 退 · claude-code-setup@claude-plugins-official（插件） · 零痕迹；对不上任何情境（自动化推荐器）；enabledPlugins 设 false
### [2026-09-04] 退 · claude-security@claude-plugins-official（插件） · 零痕迹；本仓库是静态 JSON + 前端，安全扫描不在情境清单；enabledPlugins 设 false
### [2026-09-04] 退 · code-review@claude-plugins-official（插件） · 零痕迹；只接 PR，本仓库不走 PR 审阅流；发布前情境由内置 code-review skill（非插件）接；enabledPlugins 设 false
### [2026-09-04] 退 · impeccable@impeccable（插件） · 零痕迹或用两天即停；与 frontend-design/ui-ux-pro-max 同形状，三件一起退；enabledPlugins 设 false
### [2026-09-04] 改 · tearsheet · 退→修（R10：计划要迁 skills/ 并优化描述）
### [2026-09-04] 改 · superpowers 五件 · 单件不退（R11）
### [2026-09-04] 改 · ralph-loop · 退→用（R12：Andy 09-02 用它跑过 5 小时冲刺）
### [2026-09-05] 改 · tearsheet · 描述优化器 · 测试集 4/8→4/8（description-only harness，家目录跑；阳性对照 2/6）· 5 轮候选无一超过原描述，description 不动、只加 when_to_use；点名「跑 tearsheet skill」的问句 0/3、「用 /tearsheet…」2/3，harness 本身量不出这个 skill，4/8 不能当描述的属性读
### [2026-09-06] 建 · daily-recap · 判据版复盘 skill（b4346b67）；评估集=Andy 六份真 PDF，首个真金标；A/B/C 三条法与四问全部可溯源到他原话

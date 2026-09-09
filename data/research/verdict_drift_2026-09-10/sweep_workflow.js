export const meta = {
  name: 'verdict-drift-audit',
  description: '扫全部研究目录：有没有脚本在跑一个它自己的研究档已判为错的方法，且没标死',
  phases: [
    { title: 'Scan', detail: '每批 3 个研究目录，读全部 md + py，找裁决与脚本的矛盾' },
    { title: 'Verify', detail: '每条发现两个不同视角的独立复核，默认倾向推翻' },
  ],
}

const WT = '/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/f5790c82-ac56-445d-b332-3df0922610a3/scratchpad/wt-night'

const GROUPS = [
  ['data/research/adr_floor_2026-08', 'data/research/amplitude_2026-08', 'data/research/comedy_rap_2026-08'],
  ['data/research/delayed_ep_review_2026-08', 'data/research/delayed_ep_review_2026-09', 'data/research/delayed_ep_window_2026-08'],
  ['data/research/dirty_window_reach_2026-09-02', 'data/research/gate_role_2026-08', 'data/research/gold_autumn_2026-09'],
  ['data/research/gold_seasonality_2026-08', 'data/research/i4_calibration_2026-09', 'data/research/leaders_tml_2026-09'],
  ['data/research/retro_after_the_fix', 'data/research/screener_overlap_2026-09', 'data/research/session_replay_2026-09'],
  ['data/research/tightness_2026-08', 'data/research/what_changed_2026-08', 'data/research/ui_previews/2026-08-22'],
  ['data/research/ui_previews/2026-08-25', 'data/research/ui_previews/2026-08-26', 'data/research/ui_previews/2026-08-29'],
]

const SCAN_SCHEMA = {
  type: 'object',
  properties: {
    dirs_checked: { type: 'array', items: { type: 'string' } },
    scripts_read: { type: 'integer' },
    docs_read: { type: 'integer' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          dir: { type: 'string' },
          script: { type: 'string' },
          verdict_quote: { type: 'string' },
          verdict_location: { type: 'string' },
          script_evidence: { type: 'string' },
          why_contradiction: { type: 'string' },
          banner_present: { type: 'boolean' },
          severity: { type: 'string' },
          confidence: { type: 'string' },
        },
        required: ['dir', 'script', 'verdict_quote', 'verdict_location', 'script_evidence', 'why_contradiction', 'banner_present', 'severity', 'confidence'],
      },
    },
    marked_cases: {
      type: 'array',
      items: {
        type: 'object',
        properties: { script: { type: 'string' }, how_marked: { type: 'string' } },
        required: ['script', 'how_marked'],
      },
    },
    notes: { type: 'string' },
  },
  required: ['dirs_checked', 'scripts_read', 'docs_read', 'findings', 'marked_cases', 'notes'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    reason: { type: 'string' },
    quote_is_accurate: { type: 'boolean' },
    script_still_does_it: { type: 'boolean' },
  },
  required: ['refuted', 'reason', 'quote_is_accurate', 'script_still_does_it'],
}

function scanPrompt(dirs) {
  return `你在 git worktree \`${WT}\`（**只读，绝对不要修改任何文件、不要 commit**）。全部路径相对该目录。

# 要找的东西（一句话）
**一个脚本还在实现某个方法，而它自己所在的那份研究档已经白纸黑字判定这个方法是错的 / 已被更好的替代 —— 而脚本既没改，也没在文件头标死。**

真实样本（本次审计的起因，2026-09-09）：\`data/research/delayed_ep_review_2026-09/results.md\`（09-01 写的）§三 明写
「SPY 是错的尺子；对 stage 分类器，正确基准是它自己的同日 cohort」，
而同目录的 \`review_benchmarked.py\` **在同一个 commit 里**、一直用 SPY 当分母、从没跟着改。
下一个人（就是写裁决的那个人本人）跑了这个脚本、信了它，把被推翻的方法又跑了一遍，一整夜结论要推倒重来。
⚠️ 注意：**裁决和脚本可以是同一天、同一个 commit 进仓的**，所以别用时间戳判断，要读内容。

# 你负责的目录
${dirs.map(d => '- `' + d + '`').join('\n')}

# 动作（必须全做，不许抽样）
1. \`ls -la\` 每个目录，把里面**每一个 .md 全文读完**、**每一个 .py 全文读完**（脚本很短，别只读开头）。若某个文件超大（>2000 行）就读它的 docstring/注释/关键函数，并在 notes 里说明。
2. 在 md 里找**裁决类语句**——任何形式的「X 是错的 / X 不该用 / 正确的做法是 Y / 已被 Y 取代 / 这个口径不成立 / 我这一版算错了 / 换成 Z 之后结论变了」。**别只搜关键词，要读懂**；裁决常常写成一句自我更正，而不是命令句。
3. 对每条裁决，去看**同目录（以及裁决点名的）脚本**：它现在实现的还是被否掉的那个方法吗？文件头/docstring 里有没有横幅或注释把这件事标死？
4. 逐个脚本反向再问一遍：这个脚本算的量、用的分母/基准/窗口/阈值，在它自己的 md 里有没有被否定过。

# 判定规则
- 记成 finding **只有**：脚本仍在实现被否的方法 **且** 没有任何标记提醒读者。
- 脚本已经有横幅/注释标死 → 放进 \`marked_cases\`（这是好的，不是缺陷），不要记 finding。
- 脚本是**原始跑批的存档**、md 里明说保留它作为历史记录 → 不是 finding，写进 notes。
- md 的自我更正只涉及**文字表述**、不涉及脚本算的量 → 不是 finding。
- 拿不准 → 记下来但 confidence 写 'low'，并在 why_contradiction 里说清你不确定什么。

# 举证要求（硬性）
- \`verdict_quote\`：**逐字照抄** md 里那句裁决（不许转述）。
- \`verdict_location\`：\`文件路径:行号\`。
- \`script_evidence\`：**逐字照抄**脚本里仍在做那件事的那一行/那几行，带行号。
- 举不出这两段原文的，就不要记成 finding。

severity 用 'high'（会让人跑出错结论）/'medium'/'low'；confidence 用 'high'/'medium'/'low'。
\`scripts_read\`/\`docs_read\` 填你**真正打开读过**的文件数，别虚报。
如果这几个目录一条都没有，findings 返回空数组 —— **空结果是完全可接受的答案，不要为了交差编一条**。`
}

function verifyPrompt(f, lens) {
  const lenses = {
    evidence: `**证据链视角**：去 \`${WT}\` 把这两个文件重新打开读一遍（不要相信下面抄给你的引文）。
逐项核：① \`verdict_quote\` 这句话在 \`${f.verdict_location}\` 真的一字不差存在吗？② 它真的是在否定这个方法吗，还是被断章取义了（比如它否定的是另一个量、或者它其实是在描述别人的做法）？
③ \`script\` 现在这一刻真的还在做那件事吗（读完整脚本，别只看被引的那行）？④ 文件里任何位置（文件头 docstring、行内注释、README）有没有已经标死？
只要有一项对不上，就 refuted=true。`,
    steelman: `**反面视角（替被告辩护）**：你的任务是找出这条发现**不成立**的理由。去 \`${WT}\` 读文件。
候选辩护理由：这个脚本是那一轮的原始存档、md 里明说保留；裁决说的是另一个脚本/另一个量；同目录已有替代脚本且 md 已指向它，读者不会误跑；
这个"方法"只在某个可选参数下才是错的，默认路径是对的；这份 md 本身已经是被后来的 md 推翻的旧版。
找到任何一条站得住的辩护 → refuted=true。找不到 → refuted=false 并说清你排除了哪几条辩护。`,
  }
  return `复核一条审计发现。**默认倾向推翻**：拿不准就 refuted=true。**只读，不要改任何文件。**

- 目录：\`${f.dir}\`
- 被指的脚本：\`${f.script}\`
- 声称的裁决（出处 ${f.verdict_location}）：「${f.verdict_quote}」
- 声称的脚本证据：\`${f.script_evidence}\`
- 声称的矛盾：${f.why_contradiction}

${lenses[lens]}

\`quote_is_accurate\`=引文是否逐字属实；\`script_still_does_it\`=脚本此刻是否仍在实现被否的方法。`
}

phase('Scan')
log(`扫 ${GROUPS.flat().length} 个研究目录（${GROUPS.length} 批）`)

const results = await pipeline(
  GROUPS,
  (dirs, _item, i) => agent(scanPrompt(dirs), {
    label: `scan:${dirs[0].split('/').pop()}+${dirs.length - 1}`,
    phase: 'Scan',
    schema: SCAN_SCHEMA,
  }),
  (scan, dirs) => {
    if (!scan || !scan.findings || scan.findings.length === 0) return { scan, verified: [] }
    return parallel(scan.findings.map(f => () =>
      parallel(['evidence', 'steelman'].map(lens => () =>
        agent(verifyPrompt(f, lens), { label: `verify:${lens}:${f.script.split('/').pop()}`, phase: 'Verify', schema: VERDICT_SCHEMA })
      )).then(votes => {
        const good = votes.filter(Boolean)
        const refuted = good.filter(v => v.refuted).length
        return { finding: f, votes: good, refuted_count: refuted, verdict: refuted === 0 ? 'CONFIRMED' : (refuted >= good.length ? 'KILLED' : 'PLAUSIBLE') }
      })
    )).then(verified => ({ scan, verified }))
  }
)

const ok = results.filter(Boolean)
const coverage = {
  dirs_reported: ok.flatMap(r => r.scan ? r.scan.dirs_checked : []),
  scripts_read: ok.reduce((a, r) => a + (r.scan ? r.scan.scripts_read : 0), 0),
  docs_read: ok.reduce((a, r) => a + (r.scan ? r.scan.docs_read : 0), 0),
  batches_returned: ok.length,
  batches_total: GROUPS.length,
}
const all_findings = ok.flatMap(r => r.verified)
const marked = ok.flatMap(r => r.scan ? r.scan.marked_cases : [])
const notes = ok.map(r => r.scan ? r.scan.notes : '').filter(Boolean)

log(`扫完：${coverage.scripts_read} 个脚本 / ${coverage.docs_read} 份文档；候选 ${all_findings.length} 条；已标死 ${marked.length} 条`)

return {
  coverage,
  confirmed: all_findings.filter(v => v.verdict === 'CONFIRMED'),
  plausible: all_findings.filter(v => v.verdict === 'PLAUSIBLE'),
  killed: all_findings.filter(v => v.verdict === 'KILLED'),
  marked_cases: marked,
  notes,
}
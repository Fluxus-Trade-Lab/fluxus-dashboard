// misc i18n part — merged into translations.js. Same rules as that file's
// header: flat dotted keys, identical key sets in en and zh, tickers / numbers /
// trade proper nouns stay Latin. Written as [en, zh] pairs so the two key sets
// cannot drift apart.
//
// Covers the shared pieces no single page owns: the pre-market checklist
// (#/journal), the dated writing slots and their entry stepper, the save
// button, the "data did not load" page, and the Summary insight sentences
// that portfolio/lib/diagnostics.js builds.

const P = {
  // ── PreMarketChecklist ────────────────────────────────────────────────────
  'misc.pm.title': ['Pre-Market Checklist', '盘前清单'],
  'misc.pm.q.rules': ['Am I following my rules?', '我在守自己的规矩吗？'],
  'misc.pm.q.environment': ['Market environment favorable?', '市场环境有利吗？'],
  'misc.pm.q.sizing': ['Am I sized correctly?', '仓位大小合适吗？'],
  'misc.pm.q.setup': ['Do I have a clear setup today?', '今天有清楚的形态吗？'],
  'misc.pm.q.emotional': ['Emotional state?', '情绪怎么样？'],
  'misc.pm.q.breakouts': ['Breakouts working this week?', '这周突破管用吗？'],
  // Answers are stored as the English word; only the label is translated.
  'misc.pm.a.Yes': ['Yes', '是'],
  'misc.pm.a.No': ['No', '否'],
  'misc.pm.a.Somewhat': ['Somewhat', '一般'],
  'misc.pm.a.Clear setup': ['Clear setup', '形态清楚'],
  'misc.pm.a.Forcing': ['Forcing', '硬凑'],
  'misc.pm.a.No setup': ['No setup', '没有形态'],
  'misc.pm.a.Focused': ['Focused', '专注'],
  'misc.pm.a.Tilted': ['Tilted', '上头'],
  'misc.pm.a.FOMO': ['FOMO', '怕踏空'],
  'misc.pm.a.Fearful': ['Fearful', '害怕'],
  'misc.pm.a.Mixed': ['Mixed', '有好有坏'],
  'misc.pm.notePh': ["Situational notes — what's on your mind today?", '今天的情况，心里在想什么？'],
  'misc.pm.noteLabel': ['Situational notes', '当日情况'],

  // ── WritingSlot / EntryNav / SaveState ────────────────────────────────────
  'misc.ws.written': ['{n} written', '已写 {n} 篇'],
  'misc.en.backTo': ['Back to {d}', '往前到 {d}'],
  'misc.en.nothingOlder': ['Nothing older', '没有更早的'],
  'misc.en.older': ['Older entry', '更早一篇'],
  'misc.en.forwardTo': ['Forward to {d}', '往后到 {d}'],
  'misc.en.nothingNewer': ['Nothing newer', '没有更新的'],
  'misc.en.newer': ['Newer entry', '更新一篇'],
  'misc.en.weekBeginning': ['week beginning', '这周起始日'],
  'misc.en.entryDate': ['entry date', '记录日期'],
  'misc.en.backThisWeek': ['Back to this week', '回到本周'],
  'misc.en.backToday': ['Back to today', '回到今天'],
  'misc.save.now': ['Save now', '现在保存'],
  'misc.save.nothing': ['Nothing unsaved', '没有未保存的内容'],

  // ── DataUnavailable ──────────────────────────────────────────────────────
  'misc.du.noData': ['no data', '没有数据'],
  'misc.du.pageHere': ['the page is here, the reading is not', '页面在，读数没到'],
  'misc.du.notLoaded': ['Not loaded', '没有载入'],
  'misc.du.rebuild': ['Rebuild it with', '重建命令'],

  // ── Summary insights (portfolio/lib/diagnostics.js computeInsights) ──────
  // The English templates must reproduce the sentence diagnostics.js writes,
  // byte for byte (misc.i18n.test.jsx checks it).
  'misc.ins.lowWinHighPf': [
    'Low win rate ({wr}%) but strong profit factor ({pf}) — your winners more than compensate for frequent small losses.',
    '胜率低（{wr}%），利润因子却高（{pf}）：常有小亏，但赚的那几笔补得回来还有余。',
  ],
  'misc.ins.highWinLowPf': [
    'High win rate ({wr}%) but profit factor below 1.0 — your losses are too large relative to gains. Consider tighter risk management.',
    '胜率高（{wr}%），利润因子却低于 1.0：亏的比赚的大太多。风险要管得更紧。',
  ],
  'misc.ins.losersHeldLonger': [
    'Losers held {lose} days avg vs {win} for winners — consider cutting losers faster.',
    '亏损单平均拿 {lose} 天，盈利单只拿 {win} 天。亏损单该砍得更快。',
  ],
  'misc.ins.winnersHeldLonger': [
    'Winners held {win} days avg vs {lose} for losers — good discipline letting winners run.',
    '盈利单平均拿 {win} 天，亏损单 {lose} 天。让利润奔跑，这份纪律守住了。',
  ],
  'misc.ins.lossStreak': [
    'Max consecutive loss streak: {n} trades. Consider reducing size after 3+ losses in a row.',
    '最长连亏 {n} 笔。连亏 3 笔以上，就该把仓位降下来。',
  ],
  'misc.ins.trimTooEarly': [
    '{pct}% of trims were too early (stock ran 5%+ higher within 10 days). Avg left on table: {left}%.',
    '{pct}% 的减仓太早（10 天内又涨了 5% 以上）。平均没吃到 {left}%。',
  ],
  'misc.ins.stopTooTight': [
    '{pct}% of stopped-out trades recovered 5%+. Avg stop distance was {dist}% — consider widening stops.',
    '{pct}% 被止损出局的单子后来反弹了 5% 以上。平均止损距离 {dist}%，止损可以放宽。',
  ],
  'misc.ins.consistentMonths': [
    '{pct}% of months are profitable — strong consistency.',
    '{pct}% 的月份赚钱，很稳。',
  ],
  'misc.ins.inconsistentMonths': [
    'Only {pct}% of months are profitable — review position sizing and trade selection.',
    '只有 {pct}% 的月份赚钱。回头查仓位大小和选股。',
  ],
}

export default {
  en: Object.fromEntries(Object.entries(P).map(([k, [en]]) => [k, en])),
  zh: Object.fromEntries(Object.entries(P).map(([k, [, zh]]) => [k, zh])),
}

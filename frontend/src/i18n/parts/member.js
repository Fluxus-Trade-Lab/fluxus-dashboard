// member i18n part — merged into translations.js. Same rules as that file's
// header: flat dotted keys, identical key sets in en and zh, tickers / numbers /
// trade proper nouns (R, ATR, EMA, RS, SQN) stay Latin.
//
// Holds the reserved-page frame (Placeholder.jsx) and the two pages that wear
// it, RS Live Tracker and the Masterclass (props passed from Layout.jsx). The
// lock card itself (LockedPane.jsx) reads the older locked.* / beta.* keys in
// translations.js. English is byte-identical to the literals it replaced.
export default {
  en: {
    // Placeholder frame
    'mem.ph.notBuilt': 'not built yet',
    'mem.ph.reservedNotMissing': 'the slot is reserved, not missing',
    'mem.ph.reserved': 'Reserved',
    'mem.ph.source': 'Data it will read:',

    // RS Live Tracker
    'mem.rsLive.blurb': 'Every theme against SPY, one bar each, sorted, refreshed through the session. One object on the page and nothing else.',
    'mem.rsLive.hold.bars': 'One horizontal bar per theme, ranked by relative strength',
    'mem.rsLive.hold.refresh': 'Intraday refresh, with the time of the last one printed',
    'mem.rsLive.hold.count': 'Member count beside each name — a theme of one stock is one stock',

    // Swing Trading Masterclass
    'mem.mc.blurb': 'Sixteen lessons, beginner first, English with Chinese subtitles. Already written; not yet wired into this app.',
    'mem.mc.hold.lessons': '16 lessons plus a four-part epilogue',
    'mem.mc.hold.gears': 'Two gears throughout — foundational and advanced',
    'mem.mc.hold.drafted': 'Drafted in full 2026-07-12; lives in ~/Documents/SwingMasterclass',
  },
  zh: {
    // Placeholder frame
    'mem.ph.notBuilt': '还没做',
    'mem.ph.reservedNotMissing': '位置先留着，不是漏了',
    'mem.ph.reserved': '预留',
    'mem.ph.source': '将读取的数据：',

    // RS Live Tracker
    'mem.rsLive.blurb': '每个主题对 SPY，一个主题一根条，排好序，盘中持续刷新。整页只有这一样东西。',
    'mem.rsLive.hold.bars': '每个主题一根横条，按相对强弱排名',
    'mem.rsLive.hold.refresh': '盘中刷新，并标出最近一次的时间',
    'mem.rsLive.hold.count': '每个主题旁标成员数——只有一支票的主题就是一支票',

    // Swing Trading Masterclass
    'mem.mc.blurb': '十六课，从入门讲起，英文授课配中文字幕。课已写完，还没接进这个网站。',
    'mem.mc.hold.lessons': '16 课，外加四段尾声',
    'mem.mc.hold.gears': '全程两档——基础和进阶',
    'mem.mc.hold.drafted': '2026-07-12 全部写完初稿；存放在 ~/Documents/SwingMasterclass',
  },
}

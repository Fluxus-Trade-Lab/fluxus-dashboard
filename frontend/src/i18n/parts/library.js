// library page i18n part — merged into translations.js. Same rules as that file's
// header: flat dotted keys, identical key sets in en and zh, tickers / numbers /
// trade proper nouns (T2108, McClellan, RS, ATR, EMA, VCP, EP) stay Latin.
//
// Page titles reuse nav.<page>. Article bodies are NOT here: a piece written in
// one language opens in that language, and its cover says so (lib.cover.inLang.*).
// Cover text for a one-language piece lives in components/library/coverText.js.
export default {
  en: {
    // page blurbs (Layout passes these to LibraryPage)
    'lib.blurb.defense': 'What to do when you are wrong, and what cash is for.',
    'lib.blurb.offense': 'How much, when to add, and how to tell a good setup from one that merely looks familiar.',
    'lib.blurb.psychology': 'Patience, and what to do on the day after a loss.',
    'lib.blurb.portfolio-management': 'The book as one object rather than a list of trades.',
    'lib.blurb.news': "Reading the tape's reaction rather than the headline.",

    // reserved topics
    'lib.hold.defense.stops': 'Stops, and why the one you set at entry is the only honest one',
    'lib.hold.defense.cash': 'Cash as a position, not as the absence of one',
    'lib.hold.defense.drawdown': 'Drawdown rules: what to cut, in what order, before deciding anything',
    'lib.hold.offense.sizing': 'Sizing: fixed R, and why the number is small',
    'lib.hold.offense.pyramiding': 'Pyramiding — adding to a position that has already paid',
    'lib.hold.offense.leverage': 'Leverage, and the conditions under which it is not a mistake',
    'lib.hold.offense.grading': 'Grading setups: what separates an A from a B before the outcome',
    'lib.hold.psychology.waiting': 'Waiting as a position — the cost of trading a mediocre setup',
    'lib.hold.psychology.tilt': 'Tilt: recognising it in your own log rather than in the moment',
    'lib.hold.psychology.reattack': 'The re-attack, which the H1 audit named as the single largest leak',
    'lib.hold.pm.heat': 'Open heat — total risk across every position at once',
    'lib.hold.pm.correlation': 'Correlation: several positions that are secretly one position',
    'lib.hold.pm.metrics': 'Sharpe, expectancy, SQN — what each measures and what none of them do',
    'lib.hold.news.reaction': 'News trading: the setup is the reaction, not the announcement',
    'lib.hold.news.failure': 'News failure — when a good headline cannot lift a name, that is the signal',
    'lib.hold.news.flow': 'Using news flow to track where momentum is arriving and leaving',

    // header meta
    'lib.meta.reading': 'reading',
    'lib.meta.count.one': '{n} piece',
    'lib.meta.count.other': '{n} pieces',
    'lib.meta.indexed': 'from the index',
    'lib.meta.compiled': 'compiled-in list',
    'lib.meta.notBuilt': 'not built yet',
    'lib.meta.reservedNote': 'the slot is reserved, not missing',

    // reserved block
    'lib.reserved': 'Reserved',
    'lib.alsoReserved': 'Also reserved',
    'lib.reserved.compiledNote': 'This page reads a file list compiled into the build, not the directory — a new piece still needs a frontend release. {file} has been requested from the data side (DATA_CONTRACTS §7).',

    // cover
    'lib.cover.read': 'Read →',
    'lib.cover.missing': '{name} not fetched',
    'lib.cover.inLang.zh': '(in Chinese)',
    'lib.cover.inLang.en': '(in English)',

    // one piece
    'lib.article.inLang.zh': 'This piece is written in Chinese only.',
    'lib.article.inLang.en': 'This piece is written in English only.',
    'lib.noPiece.label': 'No such piece',
    'lib.noPiece.body': 'This page has no piece called {slug}.',
    'lib.noPiece.maybeNew': ' It may also be newly written while the frontend still reads the compiled-in list.',
    'lib.missing.label': 'Not fetched',
    'lib.missing.body': '{name} was not fetched — the list names it, the file did not arrive. This is a failed read, not an empty article.',
    'lib.malformed.label': 'Not an article',
    'lib.malformed.body': '{name} arrived, but there is no article in it — no {title} and no {blocks}. Top-level keys only: {keys}.',
    'lib.malformed.how': "The article travels as this one JSON ({fields}); charts go in the same file's {charts}, placed by a {chartBlock} block. The markdown parser was removed on 2026-08-20 at the data side's request (42ec619d); the frontend no longer reads .md.",
    'lib.chart.notShipped': 'Chart not shipped',
    'lib.chart.notShippedBody': 'This article wants a chart ({key}), but {charts} has no price series for it.',
    'lib.chart.logTitle': 'Log scale: equal distance = equal percentage',
    'lib.chart.logNote': 'Log axis — on a linear one the last day would flatten the months before it into a line',
    'lib.block.unknown': 'Unknown block type {type} — the frontend cannot draw it yet.',
  },
  zh: {
    'lib.blurb.defense': '看错了怎么办，现金拿来干什么。',
    'lib.blurb.offense': '仓位多大、什么时候加仓，真正的好形态和看着眼熟的形态怎么分。',
    'lib.blurb.psychology': '耐心，以及亏钱后的第二天怎么做。',
    'lib.blurb.portfolio-management': '把整个账户当一个整体看，别当成一串交易。',
    'lib.blurb.news': '看盘面怎么反应，别看标题怎么写。',

    'lib.hold.defense.stops': '止损：为什么只有进场时设的那一个最老实',
    'lib.hold.defense.cash': '现金本身就是仓位',
    'lib.hold.defense.drawdown': '回撤规则：先砍什么、按什么顺序砍，砍完再做判断',
    'lib.hold.offense.sizing': '仓位：固定 R，以及这个数为什么要小',
    'lib.hold.offense.pyramiding': '金字塔加仓：只往已经赚钱的仓位上加',
    'lib.hold.offense.leverage': '杠杆：什么条件下用它不算犯错',
    'lib.hold.offense.grading': '给形态打分：结果出来之前，A 级和 B 级差在哪',
    'lib.hold.psychology.waiting': '等待也是仓位：做平庸形态要付的代价',
    'lib.hold.psychology.tilt': '上头：去自己的交易记录里认出它，别指望当下察觉',
    'lib.hold.psychology.reattack': '止损后马上再冲进去——上半年审计查出的最大漏洞',
    'lib.hold.pm.heat': '总风险：所有持仓加在一起，同时担着多少风险',
    'lib.hold.pm.correlation': '相关性：看着是几笔持仓，其实是同一笔',
    'lib.hold.pm.metrics': '夏普比率、期望值、SQN：各自量什么，哪样都量不了什么',
    'lib.hold.news.reaction': '新闻交易：形态在市场的反应里，不在公告里',
    'lib.hold.news.failure': '利好不涨：好消息拉不动一只票，这本身就是信号',
    'lib.hold.news.flow': '用新闻流追踪动量往哪里来、从哪里走',

    'lib.meta.reading': '读取中',
    'lib.meta.count.one': '{n} 篇',
    'lib.meta.count.other': '{n} 篇',
    'lib.meta.indexed': '来自索引',
    'lib.meta.compiled': '内置名单',
    'lib.meta.notBuilt': '还没写',
    'lib.meta.reservedNote': '位子留着，不是丢了',

    'lib.reserved': '预留',
    'lib.alsoReserved': '还预留了',
    'lib.reserved.compiledNote': '这一页读的是编译进来的文件名单，不是目录——新增一篇还得前端发一版。已向数据端要 {file}（DATA_CONTRACTS §七）。',

    'lib.cover.read': '读全文 →',
    'lib.cover.missing': '{name} 没取到',
    'lib.cover.inLang.zh': '（中文）',
    'lib.cover.inLang.en': '（英文）',

    'lib.article.inLang.zh': '本篇只有中文版。',
    'lib.article.inLang.en': '本篇只有英文版。',
    'lib.noPiece.label': '没有这一篇',
    'lib.noPiece.body': '这一页没有叫 {slug} 的篇目。',
    'lib.noPiece.maybeNew': '也可能它刚写好，而前端读的还是编译进来的名单。',
    'lib.missing.label': '没取到',
    'lib.missing.body': '{name} 没取到——名单里有它，文件没到。这是一次读取失败，不是空文章。',
    'lib.malformed.label': '不是文章',
    'lib.malformed.body': '{name} 取到了，但里面没有文章——没有 {title}，也没有 {blocks}。顶层只有：{keys}。',
    'lib.malformed.how': '文章正文走这一个 JSON（{fields}），图放同文件的 {charts} 里，由 {chartBlock} 块定位。markdown 解析器 2026-08-20 已按数据端要求删除（42ec619d），前端不再读 .md。',
    'lib.chart.notShipped': '图没到',
    'lib.chart.notShippedBody': '这篇文章要一张图（{key}），但 {charts} 里没有它的 K 线。',
    'lib.chart.logTitle': '纵轴按对数：等距离 = 等百分比',
    'lib.chart.logNote': '纵轴对数——线性轴下，最后一天会把之前几个月压成一条线',
    'lib.block.unknown': '未知的块类型 {type}——前端还不会画它。',
  },
}

// Professional finance zh-CN translations for UI chrome (labels, headers, buttons, badges).
// Flat dotted keys. Data values (tickers, numbers, prices, dates) are never translated.
// Missing keys fall back to English, then to the key string itself (see LanguageContext).

export const translations = {
  en: {
    // Brand / header
    'brand.name': 'Fluxus Capital',
    'header.offline': 'Offline',
    'header.lightMode': 'Switch to light mode',
    'header.darkMode': 'Switch to dark mode',
    'header.language': 'Language',

    // Nav
    'nav.dashboard': 'Dashboard',
    'nav.screener': 'Screener',
    'nav.portfolio': 'Portfolio',
    'nav.trades': 'Trade Journal',
    'nav.journal': 'AI Coach',
    'nav.briefing': 'Briefing',
    'nav.breadth': 'Market State',
    'nav.correction': 'Correction Risk',
    'nav.groups': 'Themes',
    'nav.modelbooks': 'Model Books',
    // The rail's two groups. MARKET is the state of the market and needs no
    // account; MY BOOK is a framework and a record and cannot exist without one.
    'rail.market': 'Market',
    'rail.market.note': 'Open. No account needed.',
    'rail.library': 'Library',
    'rail.library.note': 'How to read a market. Not what it did today.',
    'rail.book': 'My Book',
    'rail.book.note': 'Needs an account and your own fills.',

    // Page titles
    'page.trades.title': 'Trade Journal',
    'page.watchlist.title': "Today's Watchlist",

    // Portfolio — header
    'pf.title': 'Portfolio Tracker',
    'pf.starting': 'Starting',
    'pf.stat.portfolio': 'Portfolio',
    'pf.stat.pl': 'P/L',
    'pf.stat.return': 'Return',
    'pf.stat.cash': 'Cash',
    'pf.stat.open': 'Open',

    // Portfolio — buttons
    'pf.btn.trade': '+ Trade',
    'pf.btn.cancel': 'Cancel',
    'pf.btn.refresh': 'Refresh',
    'pf.btn.fetching': 'Fetching...',
    'pf.btn.export': 'Export',
    'pf.btn.import': 'Import',
    'pf.btn.settings': 'Settings',
    'pf.btn.private': 'Private',
    'pf.btn.reset': 'Reset',
    'pf.sync.showValues': 'Show values',
    'pf.sync.hideValues': 'Hide values',

    // Portfolio — tabs
    'pf.tab.overview': 'Overview',
    'pf.tab.exposure': 'Exposure',
    'pf.tab.risk': 'Risk',
    'pf.tab.options': 'Options Port',

    // Portfolio — table columns (keyed by column key)
    'pf.col.ticker': 'Ticker',
    'pf.col.direction': 'Dir',
    'pf.col.status': 'Status',
    'pf.col.entryDate': 'Open',
    'pf.col.currentQty': 'Qty',
    'pf.col.entryPrice': 'Entry',
    'pf.col.weight': 'Wt%',
    'pf.col.change1D': '1D%',
    'pf.col.pl1D': 'P/L 1D',
    'pf.col.lastPrice': 'Last',
    'pf.col.t1Price': 'T1 $',
    'pf.col.t1Date': 'T1 Date',
    'pf.col.t2Price': 'T2 $',
    'pf.col.t2Date': 'T2 Date',
    'pf.col.t3Price': 'T3 $',
    'pf.col.t3Date': 'T3 Date',
    'pf.col.stopPrice': 'Stop',
    'pf.col.unrealizedPLPct': 'Unrl%',
    'pf.col.realizedPLPct': 'Rlzd%',
    'pf.col.marketVal': 'Mkt Val',
    'pf.col.totalPL': 'P/L',
    'pf.col.totalReturnPct': 'Tot%',
    'pf.col.holdingDays': 'Days',
    'pf.col.rr': 'RR',

    // Portfolio — direction values
    'pf.dir.long': 'LONG',
    'pf.dir.short': 'SHORT',

    // Portfolio — leg-state badges
    'pf.leg.PRE_TRIM': 'PRE-T1',
    'pf.leg.POST_T1': 'POST-T1',
    'pf.leg.POST_T2': 'POST-T2',
    'pf.leg.POST_T3': 'POST-T3',

    // Portfolio — table controls / status
    'pf.showOpenOnly': 'Show Open Only',
    'pf.showAll': 'Show All',
    'pf.closedCount': 'closed',
    'pf.closed': 'Closed',
    'pf.hint.editPrice': 'Click Last Price or Stop to edit. Hit Refresh to auto-fetch.',

    // Portfolio — intro / empty state
    'pf.intro.subtitle': 'Enter starting capital, or upload an existing trade log',
    'pf.intro.capitalLabel': 'Starting Capital ($)',
    'pf.intro.startTracking': 'Start Tracking',
    'pf.intro.uploadCsv': 'Upload CSV',
    'pf.intro.trySample': 'Try Sample',

    // Portfolio — equity chart
    'pf.chart.vsSpy': 'Portfolio vs SPY',
    'pf.chart.loading': 'Loading...',
    'pf.chart.refreshHistory': 'Refresh History',
    'pf.chart.loadHistory': 'Load History',
    'pf.chart.loadHistoryHint': 'Load historical prices for the equity curve and SPY comparison.',
    'pf.chart.portfolio': 'Portfolio',
    'pf.chart.spyYtd': 'SPY YTD',

    // Portfolio — monthly performance table
    'pf.monthly.title': 'Monthly Performance',
    'pf.mh.return': 'Return%',
    'pf.mh.trades': '# Trades',
    'pf.mh.avgRet': 'Avg Ret%',
    'pf.mh.win': 'Win%',
    'pf.mh.avgGain': 'Avg Gain%',
    'pf.mh.avgLoss': 'Avg Loss%',
    'pf.mh.maxGain': 'Max Gain%',
    'pf.mh.maxLoss': 'Max Loss%',
    'pf.mh.daysW': 'Days(W)',
    'pf.mh.daysL': 'Days(L)',
  },

  zh: {
    // Brand / header
    'brand.name': 'Fluxus Capital',
    'header.offline': '离线',
    'header.lightMode': '切换到浅色模式',
    'header.darkMode': '切换到深色模式',
    'header.language': '语言',

    // Nav
    'nav.dashboard': '仪表盘',
    'nav.screener': '选股器',
    'nav.portfolio': '投资组合',
    'nav.trades': '交易日志',
    'nav.journal': 'AI 教练',
    'nav.briefing': '每日简报',
    'nav.breadth': '市场状态',
    'nav.correction': '回撤风险',
    'nav.groups': '主题',
    'nav.modelbooks': '标杆案例',

    // 侧栏两组。Market 是市场的状态,对所有人相同,不需要账户;
    // My Book 是你的框架和你的记录,没有账户就不存在。
    'rail.market': '市场',
    'rail.market.note': '开放。不需要账户。',
    'rail.library': '资料库',
    'rail.library.note': '怎么读市场。不是市场今天怎么样。',
    'rail.book': '我的账本',
    'rail.book.note': '需要账户 + 你自己的成交。',

    // Page titles
    'page.trades.title': '交易日志',
    'page.watchlist.title': '今日观察名单',

    // Portfolio — header
    'pf.title': '投资组合追踪',
    'pf.starting': '起始资金',
    'pf.stat.portfolio': '组合市值',
    'pf.stat.pl': '盈亏',
    'pf.stat.return': '收益率',
    'pf.stat.cash': '现金',
    'pf.stat.open': '未平仓',

    // Portfolio — buttons
    'pf.btn.trade': '+ 建仓',
    'pf.btn.cancel': '取消',
    'pf.btn.refresh': '刷新',
    'pf.btn.fetching': '获取中…',
    'pf.btn.export': '导出',
    'pf.btn.import': '导入',
    'pf.btn.settings': '设置',
    'pf.btn.private': '隐私',
    'pf.btn.reset': '重置',
    'pf.sync.showValues': '显示数值',
    'pf.sync.hideValues': '隐藏数值',

    // Portfolio — tabs
    'pf.tab.overview': '总览',
    'pf.tab.exposure': '持仓敞口',
    'pf.tab.risk': '风险',
    'pf.tab.options': '期权组合',

    // Portfolio — table columns
    'pf.col.ticker': '代码',
    'pf.col.direction': '方向',
    'pf.col.status': '状态',
    'pf.col.entryDate': '建仓日',
    'pf.col.currentQty': '数量',
    'pf.col.entryPrice': '建仓价',
    'pf.col.weight': '权重%',
    'pf.col.change1D': '单日%',
    'pf.col.pl1D': '单日盈亏',
    'pf.col.lastPrice': '最新价',
    'pf.col.t1Price': '减仓1价',
    'pf.col.t1Date': '减仓1日',
    'pf.col.t2Price': '减仓2价',
    'pf.col.t2Date': '减仓2日',
    'pf.col.t3Price': '减仓3价',
    'pf.col.t3Date': '减仓3日',
    'pf.col.stopPrice': '止损',
    'pf.col.unrealizedPLPct': '未实现%',
    'pf.col.realizedPLPct': '已实现%',
    'pf.col.marketVal': '市值',
    'pf.col.totalPL': '盈亏',
    'pf.col.totalReturnPct': '总收益%',
    'pf.col.holdingDays': '持仓天数',
    'pf.col.rr': '盈亏比',

    // Portfolio — direction values
    'pf.dir.long': '多头',
    'pf.dir.short': '空头',

    // Portfolio — leg-state badges
    'pf.leg.PRE_TRIM': '待减仓',
    'pf.leg.POST_T1': '已减1',
    'pf.leg.POST_T2': '已减2',
    'pf.leg.POST_T3': '已减3',

    // Portfolio — table controls / status
    'pf.showOpenOnly': '仅看持仓',
    'pf.showAll': '显示全部',
    'pf.closedCount': '已平仓',
    'pf.closed': '已平仓',
    'pf.hint.editPrice': '点击最新价或止损可编辑，点击刷新自动获取。',

    // Portfolio — intro / empty state
    'pf.intro.subtitle': '输入起始资金，或上传已有的交易记录',
    'pf.intro.capitalLabel': '起始资金（$）',
    'pf.intro.startTracking': '开始追踪',
    'pf.intro.uploadCsv': '上传 CSV',
    'pf.intro.trySample': '示例数据',

    // Portfolio — equity chart
    'pf.chart.vsSpy': '组合 vs SPY',
    'pf.chart.loading': '加载中…',
    'pf.chart.refreshHistory': '刷新历史',
    'pf.chart.loadHistory': '加载历史',
    'pf.chart.loadHistoryHint': '加载历史价格以生成净值曲线并与 SPY 对比。',
    'pf.chart.portfolio': '投资组合',
    'pf.chart.spyYtd': 'SPY 年初至今',

    // Portfolio — monthly performance table
    'pf.monthly.title': '月度业绩',
    'pf.mh.return': '收益%',
    'pf.mh.trades': '交易数',
    'pf.mh.avgRet': '平均收益%',
    'pf.mh.win': '胜率%',
    'pf.mh.avgGain': '平均盈利%',
    'pf.mh.avgLoss': '平均亏损%',
    'pf.mh.maxGain': '最大盈利%',
    'pf.mh.maxLoss': '最大亏损%',
    'pf.mh.daysW': '持仓天(盈)',
    'pf.mh.daysL': '持仓天(亏)',
  },
}

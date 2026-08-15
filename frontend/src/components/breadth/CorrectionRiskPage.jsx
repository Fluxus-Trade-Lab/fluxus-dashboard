import { useLanguage } from '../../i18n/LanguageContext'

/**
 * Correction Risk — an empty slot, held open on purpose.
 *
 * The rail's Market group is a ladder of what we can show, and this rung is
 * not earned yet. It is published empty rather than filled with the nearest
 * thing we happen to have, because a page that borrows an adjacent number to
 * look finished teaches the reader to trust a claim nobody made.
 *
 * What goes here is written down now so that the slot is a commitment with a
 * standard attached, not a placeholder that quietly becomes whatever ships.
 * The gating condition below is the whole reason the page is empty: the
 * measurement exists, the sample does not.
 */

const GOALS = [
  {
    k: 'question',
    en: 'The question',
    zh: '要回答的问题',
    en_body: 'The probability that the index draws down 5% or more within the ' +
      'next month — a number, with the base rate it is measured against. Not a ' +
      'direction call. It answers how much can be lost here, never which way to lean.',
    zh_body: '未来一个月内指数跌破 −5% 的概率 —— 一个数字,连同它所对照的基准率。' +
      '不是方向判断:它回答「这里能亏多少」,不回答「该往哪边押」。',
  },
  {
    k: 'why',
    en: 'Why it is a separate reading',
    zh: '为什么它是独立的一读',
    en_body: 'Market State is flat against next month\'s average return and ' +
      'monotone against the left tail — 5% drawdown frequency ran 27% in Damaged ' +
      'against 6% in Extended across 2024–2026. Mean and tail are different ' +
      'objects. This page is the tail one.',
    zh_body: '市场状态对下个月的平均收益是平的,对左尾却是单调的 —— 2024–2026 年间,' +
      'Damaged 档的 −5% 回撤频率 27%,Extended 档 6%。均值和尾部是两个统计量,这一页是尾部那个。',
  },
  {
    k: 'blocker',
    en: 'What is blocking it',
    zh: '卡在哪里',
    en_body: 'Episodes, not sessions. Corrections arrive about 5.5 times a year, ' +
      'so our 2.2-year breadth archive holds ten independent ones — four bands ' +
      'can line up in the right order on ten events by luck. A defensible model ' +
      'wants roughly twenty years, and breadth and dealer gamma, the two inputs ' +
      'we compute rather than rent, are the two without that history.',
    zh_body: '卡在事件数,不是交易日数。回撤平均每年 5.5 段,我们 2.2 年的广度归档里只有 10 段独立事件 —— ' +
      '四个档在 10 段事件上排出正确顺序,靠运气就能做到。要站得住大约需要 20 年;' +
      '而广度和做市商 gamma —— 恰恰是我们自建而非租用的两项 —— 正是没有长历史的两项。',
  },
  {
    k: 'plan',
    en: 'How it will be built',
    zh: '打算怎么建',
    en_body: 'Two layers, validated apart and never averaged into one number. A ' +
      'base on inputs that reach back twenty years — index volatility structure, ' +
      'the VIX term curve, credit spreads, survey sentiment — calibrated on 115 ' +
      'or more episodes. Then breadth and gamma as an overlay, scored only on the ' +
      'window where they exist, and labelled as such.',
    zh_body: '两层,分开验证,绝不平均成一个数。底座只用能回溯 20 年的输入 —— ' +
      '指数波动结构、VIX 期限曲线、信用价差、调查情绪 —— 在 115 段以上事件上标定。' +
      '广度和 gamma 作为叠加层,只在有数据的窗口上打分,并且明确标注。',
  },
  {
    k: 'gate',
    en: 'What has to be true before it ships',
    zh: '上线前必须成立的条件',
    en_body: 'The band ordering holds on non-overlapping samples and in both ' +
      'halves, on a sample with at least a hundred episodes, and the full backtest ' +
      'is published alongside it. If it fails, this page says so and stays empty — ' +
      'the same way RS acceleration was built, measured, found null, and demoted ' +
      'to description.',
    zh_body: '档位顺序在不重叠采样和前后半样本中都成立,样本至少 100 段事件,' +
      '并且回测全量随页公开。不成立就把结论写在这页上、继续空着 —— ' +
      '和 RS 加速度一样:建了、测了、是 NULL、降级为描述层。',
  },
]

export default function CorrectionRiskPage() {
  const { lang } = useLanguage()
  const zh = lang === 'zh'

  return (
    <div className="max-w-[760px]">
      <header className="pb-5 mb-6 border-b border-[var(--color-border)]">
        <div className="flex items-baseline gap-3 flex-wrap">
          <h1 className="text-[17px] font-semibold m-0">
            {zh ? '回撤风险' : 'Correction Risk'}
          </h1>
          <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase tracking-[.18em]
                           rounded-3xl text-[var(--color-text-muted)]">
            {zh ? '未上线' : 'Not shipped'}
          </span>
        </div>
        <p className="mt-2 mb-0 text-[14px] text-[var(--color-text-secondary)]">
          {zh
            ? '这一格是空的,而且是故意空着的。下面写的是它要回答什么、卡在哪里、以及凭什么才算做完 —— 先立标准,再动手。'
            : 'This slot is empty, deliberately. Below is what it has to answer, what is ' +
              'blocking it, and the standard it has to clear — the standard first, the page after.'}
        </p>
      </header>

      <ol className="list-none p-0 m-0 space-y-6">
        {GOALS.map((g, i) => (
          <li key={g.k} className="grid grid-cols-[1.6rem_1fr] gap-3">
            <span className="font-mono text-[11px] pt-[3px] text-[var(--color-text-muted)]
                             tabular-nums">
              {String(i + 1).padStart(2, '0')}
            </span>
            <div>
              <h2 className="text-[12.5px] font-semibold m-0 mb-1">
                {zh ? g.zh : g.en}
              </h2>
              <p className="m-0 text-[12.5px] leading-relaxed text-[var(--color-text-secondary)]">
                {zh ? g.zh_body : g.en_body}
              </p>
            </div>
          </li>
        ))}
      </ol>

      <p className="mt-8 pt-4 border-t border-[var(--color-border)] m-0
                    text-[11px] leading-relaxed text-[var(--color-text-muted)]">
        {zh
          ? '在此之前,风险预算读「市场状态」那一页的档位 —— 它的尾部读数只在 10 段事件上验证过,别当成概率用。'
          : 'Until then the risk budget reads off the Market State band. Its tail reading ' +
            'rests on ten episodes — read it as an ordering, not as a probability.'}
      </p>
    </div>
  )
}

/**
 * 会员问卷 · Google 表单生成器（v2 · 2026-09-26）
 *
 * v2（Andy 09-26 原话「我选A，GOOGLE的表单。另外问题还应该加入过去他们的交易时间，经历，
 * 『你到底要什么』也应该更加复杂一些吧」）：加第二节「交易经历」6 题；「你到底要什么」扩成 8 题，
 * 含阶梯题 Q9 与重要度矩阵 Q11。共 30 题、7 节，必答 14 题。
 *
 * 用法：script.google.com → 新建项目 → 粘贴本文件 → 运行 createFluxusMemberSurvey()
 * 首次运行会要求授权（用 Andy 自己的 Google 账号）。跑完在执行日志里打印两个链接：
 * 填写链接（发给会员）与编辑链接（改题）。回收结果：表单编辑页 →「回复」→「关联到试算表」。
 *
 * 题库与每题的决策口径见 data/growth/member_survey_2026-09-26.md —— 那份是权威，改题先改它。
 */

function createFluxusMemberSurvey() {
  var form = FormApp.create('Fluxus 会员问卷 · Member Survey (5 min)');

  form.setDescription(
    '我想把接下来三个月做对，所以先问你们，而不是自己猜。\n' +
    '30 个问题，大部分是选项，5 分钟。最后三题是开放的——那三题我会一条条读。\n' +
    '有一题问你能承受多大回撤：我自己 YTD 是 130%，SPY 是 11%，但那条曲线中间的坑不是每个人都该去踩。我需要知道你站在哪。\n\n' +
    'I want to get the next three months right, so I am asking instead of guessing. ' +
    '30 questions, mostly multiple choice, about 5 minutes. The open ones at the end I read myself.'
  );
  form.setProgressBar(true);
  form.setCollectEmail(false);            // 不强制留邮箱；Q30 自愿留联系方式
  form.setLimitOneResponsePerUser(false); // 不要求登录 Google 账号

  // ——————————————— 一、你是谁 ———————————————
  form.addSectionHeaderItem().setTitle('一、你是谁 / About you');

  form.addMultipleChoiceItem()
    .setTitle('Q1. 你加入 Fluxus 多久了？ / How long have you been with Fluxus?')
    .setChoiceValues(['不到 1 个月', '1–3 个月', '3–6 个月', '6 个月以上'])
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('Q2. 你现在有什么？（可多选） / What do you have now?')
    .setChoiceValues(['月付 / 季付 / 年付会员', '终身会员', '波段大师课', '只用免费区'])
    .setRequired(true);

  // ——————————————— 二、你的交易经历 ———————————————
  form.addSectionHeaderItem()
    .setTitle('二、你的交易经历 / Your trading background')
    .setHelpText('这一节不是考试。我需要知道站在对面的是什么人，才知道东西该做成什么样。');

  form.addGridItem()
    .setTitle('Q3. 下面两件事各有多久？ / How long for each?')
    .setRows(['接触交易（含看书、模拟、纸上练）', '真金实盘 / Real money'])
    .setColumns(['不到 1 年', '1–3 年', '3–5 年', '5–10 年', '10 年以上'])
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('Q4. 下面哪些行情，你是带着仓位经历过的？（可多选） / Which of these did you trade through, with positions on?')
    .setChoiceValues(['2020 疫情崩盘', '2022 全年熊市', '2023–24 AI 主升', '2026 年内那次回撤', '以上都没有'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q5. 你主要做多长周期？ / Your typical holding period?')
    .setChoiceValues(['日内', '几天到两周', '两周到两个月', '几个月以上', '说不清'])
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('Q6.（可跳过）你主要交易什么？ / What do you trade?')
    .setChoiceValues(['美股个股', 'ETF', '美股期权', '加密', '期货', 'A 股 / 港股'])
    .setRequired(false);

  form.addMultipleChoiceItem()
    .setTitle('Q7. 你自己经历过的最大一次账户回撤是多少？ / The worst drawdown you have personally lived through?')
    .setChoiceValues(['10% 以内', '10–20%', '20–35%', '35–50%', '50% 以上', '没算过'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q8.（可跳过）在我们之前，你买过几个付费社群或交易课程？ / How many paid trading communities or courses before us?')
    .setChoiceValues(['没有，我们是第一个', '1–2 个', '3–5 个', '5 个以上'])
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('Q8b.（可跳过）其中最有用的是哪一个？它做对了什么？ / Which one was most useful, and what did it get right?')
    .setRequired(false);

  // ——————————————— 三、你到底要什么 ———————————————
  form.addSectionHeaderItem()
    .setTitle('三、你到底要什么 / What you actually want')
    .setHelpText('这一节的答案决定我接下来三个月做什么。请按你真实会做的选，不用按你觉得应该的选。');

  form.addMultipleChoiceItem()
    .setTitle('Q9. 你希望我们替你做到哪一步？ / How far should we go for you?')
    .setChoiceValues([
      '1 只给我市场观点和方向，票我自己找',
      '2 给我候选清单，买不买、什么时候买我自己判断',
      '3 给我明确的入场点和止损点，仓位我自己定',
      '4 连仓位、加仓、减仓都给我，我照着做',
      '5 我希望有人直接替我管账户'
    ])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q10. 下面哪句最像你？ / Which one sounds most like you?')
    .setChoiceValues([
      'A 我想学会自己选股、自己进出，最终不依赖任何人',
      'B 我想有人给我明确的买卖点，我照做就行',
      'C 我只要账户能跑赢指数，过程谁做的不重要',
      'D 我自己有一套系统，来这里是交叉验证'
    ])
    .setRequired(true);

  form.addGridItem()
    .setTitle('Q11. 下面几件事，对你各有多重要？ / How important is each to you?')
    .setRows([
      '更高的收益',
      '更少的时间投入',
      '更少的亏损',
      '学会自己做',
      '有人可以问',
      '有人在旁边，不至于一个人扛'
    ])
    .setColumns(['非常重要', '重要', '一般', '不重要'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q12. 你眼下最想解决的一个问题是什么？ / The one problem you most want solved?')
    .setChoiceValues([
      '不知道买什么',
      '知道买什么但不敢下手',
      '拿不住，涨一点就卖',
      '止损不执行',
      '亏了之后报复性交易',
      '没时间盯盘',
      '仓位不会管'
    ])
    .showOtherOption(true)
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q13. 你希望和我的互动到什么程度？ / How much interaction do you want?')
    .setChoiceValues(['只看内容就好，不需要互动', '偶尔能问一句', '希望有人点评我自己的交易', '想要一对一'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q14. 一年后，你希望自己是什么样？ / A year from now, you want to be…')
    .setChoiceValues(['能独立跑完整个流程', '能跟上并执行、不犯大错', '账户比指数好就行', '说不准'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q15. 如果只能保留一样，你希望是哪一样？ / If you could keep only one thing?')
    .setChoiceValues(['每日简报', '盘中实时评论', '选股清单', '课程与回放', 'dashboard 数据', '社群问答'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q16. 你希望多久收到一次可执行的东西？ / How often do you want something actionable?')
    .setChoiceValues(['每天', '每周一次', '每月几次就够', '有机会才发，不用定期'])
    .setRequired(true);

  // ——————————————— 四、时间与执行 ———————————————
  form.addSectionHeaderItem().setTitle('四、时间与执行 / Time and execution');

  form.addMultipleChoiceItem()
    .setTitle('Q17. 你每天能花多少时间在盯盘或复盘？ / Time per day on the market?')
    .setChoiceValues(['15 分钟以内', '15–60 分钟', '1–3 小时', '基本全天'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q18. 美股盘中你能看到吗？ / Can you watch the US session live?')
    .setChoiceValues(['全程可以', '只能开盘后一小时', '只能盘后看', '完全不能'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q19. 过去 3 个月我们发出的机会，你实际做了多少？ / Of the setups we posted, how many did you take?')
    .setChoiceValues(['几乎都做', '大约一半', '很少', '一次也没做'])
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('Q19b.（可跳过）没做的主要原因？ / Why not?')
    .setChoiceValues(['看不懂', '没时间', '资金不够', '不敢下手', '不同意这个判断'])
    .setRequired(false);

  form.addMultipleChoiceItem()
    .setTitle('Q20. 止损你怎么执行？ / How do you handle stops?')
    .setChoiceValues(['写了就一定执行', '大部分执行', '常常拖', '没有固定止损'])
    .setRequired(true);

  // ——————————————— 五、风险承受 ———————————————
  form.addSectionHeaderItem()
    .setTitle('五、风险承受 / Risk tolerance')
    .setHelpText('这一节只用来决定产品怎么做，不会公开，也不会和你的名字放在一起。');

  form.addMultipleChoiceItem()
    .setTitle('Q21. 账户整体，你能接受的最大回撤？ / Max drawdown you can live with?')
    .setChoiceValues(['10% 以内', '10–20%', '20–35%', '35% 以上'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q22. 单笔交易，你最多愿意亏账户的百分之几？ / Max loss per trade?')
    .setChoiceValues(['1% 以内', '1–2%', '2–5%', '没想过'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q23.（可跳过）用于这套打法的资金规模区间？ / Capital deployed on this approach?')
    .setChoiceValues(['$25k 以内', '$25–100k', '$100–500k', '$500k 以上', '不想说'])
    .setRequired(false);

  form.addMultipleChoiceItem()
    .setTitle('Q24. 过去 12 个月，你的实际收益和 SPY 比？ / Your last 12 months vs SPY?')
    .setChoiceValues(['跑输', '差不多', '跑赢', '没算过'])
    .setRequired(true);

  // ——————————————— 六、老会员开放题 ———————————————
  form.addSectionHeaderItem()
    .setTitle('六、给待了一阵子的你 / If you have been here a while')
    .setHelpText('加入不满 1 个月可以跳过这三题。');

  form.addParagraphTextItem()
    .setTitle('Q25. 这段时间你学到的最有用的一件事是什么？ / The most useful thing you have learned here?')
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('Q26. 有没有哪一笔交易，是因为这里才做对、或才躲开的？（有代码更好） / A trade you got right — or avoided — because of this?')
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('Q27. 我最该改进的一件事是什么？ / The one thing I should improve?')
    .setRequired(false);

  // ——————————————— 七、料理包 ———————————————
  form.addSectionHeaderItem().setTitle('七、一个还没做的东西 / Something we have not built yet');

  form.addMultipleChoiceItem()
    .setTitle('Q28. 每周给你实盘持仓、入场点、止损点、减仓点，你不需要自己选股——你会？ / A weekly follow-along pack. You would…')
    .setChoiceValues(['现在就要', '看价格再说', '不需要，我要自己学', '不确定'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q29. 你觉得它每月值多少？ / What is it worth per month?')
    .setChoiceValues(['$50 以内', '$50–99', '$100–199', '$200 以上', '不会买'])
    .setRequired(true);

  form.addTextItem()
    .setTitle('Q30. 愿意和我做一次 15 分钟的一对一通话吗？愿意的话留个 Discord 名或邮箱。 / Up for a 15-minute call? Leave a handle or email.')
    .setRequired(false);

  Logger.log('填写链接（发给会员）: ' + form.getPublishedUrl());
  Logger.log('编辑链接（改题用）: ' + form.getEditUrl());
  return form.getPublishedUrl();
}

/**
 * 会员问卷 · Google 表单生成器（2026-09-26）
 *
 * 用法：script.google.com → 新建项目 → 粘贴本文件 → 运行 createFluxusMemberSurvey()
 * 第一次运行会要求授权（用 Andy 自己的 Google 账号）。
 * 跑完在执行日志里打印两个链接：填写链接（发给会员）与编辑链接（改题）。
 * 回收结果：表单编辑页 → 「回复」→ 「关联到试算表」。
 *
 * 题库与每题的决策口径见 data/growth/member_survey_2026-09-26.md。
 * 改题请先改那份 md，再改本文件 —— md 是权威。
 */

function createFluxusMemberSurvey() {
  var form = FormApp.create('Fluxus 会员问卷 · Member Survey (3 min)');

  form.setDescription(
    '我想把接下来三个月做对，所以先问你们，而不是自己猜。\n' +
    '20 个问题，3 分钟，最后几题是开放的——那几题我会一条条读。\n\n' +
    'I want to get the next three months right, so I am asking instead of guessing. ' +
    '20 questions, 3 minutes. The open ones at the end I read myself.'
  );
  form.setProgressBar(true);
  form.setCollectEmail(false);          // 不强制留邮箱；Q20 自愿留联系方式
  form.setLimitOneResponsePerUser(false); // 不要求登录 Google 账号

  // —— 一、你是谁 ——
  form.addSectionHeaderItem().setTitle('一、你是谁 / About you');

  form.addMultipleChoiceItem()
    .setTitle('Q1. 你加入 Fluxus 多久了？ / How long have you been with Fluxus?')
    .setChoiceValues(['不到 1 个月', '1–3 个月', '3–6 个月', '6 个月以上'])
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('Q2. 你现在有什么？（可多选） / What do you have now?')
    .setChoiceValues(['月付 / 季付 / 年付会员', '终身会员', '波段大师课', '只用免费区'])
    .setRequired(true);

  // —— 二、你到底要什么 ——
  form.addSectionHeaderItem().setTitle('二、你到底要什么 / What you actually want');

  form.addMultipleChoiceItem()
    .setTitle('Q3. 下面哪句最像你？ / Which one sounds most like you?')
    .setChoiceValues([
      'A 我想学会自己选股、自己进出，最终不依赖任何人',
      'B 我想有人给我明确的买卖点，我照做就行',
      'C 我只要账户能跑赢指数，过程谁做的不重要',
      'D 我自己有一套系统，来这里是交叉验证'
    ])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q4. 如果只能保留一样，你希望是哪一样？ / If you could keep only one thing?')
    .setChoiceValues(['每日简报', '盘中实时评论', '选股清单', '课程与回放', 'dashboard 数据', '社群问答'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q5. 一年后，你希望自己是什么样？ / A year from now, you want to be…')
    .setChoiceValues(['能独立跑完整个流程', '能跟上并执行、不犯大错', '账户比指数好就行', '说不准'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q6. 你希望多久收到一次可执行的东西？ / How often do you want something actionable?')
    .setChoiceValues(['每天', '每周一次', '每月几次就够', '有机会才发，不用定期'])
    .setRequired(true);

  // —— 三、配合度与能力 ——
  form.addSectionHeaderItem().setTitle('三、时间与执行 / Time and execution');

  form.addMultipleChoiceItem()
    .setTitle('Q7. 你每天能花多少时间在盯盘或复盘？ / Time per day on the market?')
    .setChoiceValues(['15 分钟以内', '15–60 分钟', '1–3 小时', '基本全天'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q8. 美股盘中你能看到吗？ / Can you watch the US session live?')
    .setChoiceValues(['全程可以', '只能开盘后一小时', '只能盘后看', '完全不能'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q9. 过去 3 个月我们发出的机会，你实际做了多少？ / Of the setups we posted, how many did you take?')
    .setChoiceValues(['几乎都做', '大约一半', '很少', '一次也没做'])
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('Q9b.（可跳过）没做的主要原因？ / Why not?')
    .setChoiceValues(['看不懂', '没时间', '资金不够', '不敢下手', '不同意这个判断'])
    .setRequired(false);

  form.addMultipleChoiceItem()
    .setTitle('Q10. 止损你怎么执行？ / How do you handle stops?')
    .setChoiceValues(['写了就一定执行', '大部分执行', '常常拖', '没有固定止损'])
    .setRequired(true);

  // —— 四、风险承受 ——
  form.addSectionHeaderItem()
    .setTitle('四、风险承受 / Risk tolerance')
    .setHelpText('这一节的答案只用来决定产品怎么做，不会公开，也不会和你的名字放在一起。');

  form.addMultipleChoiceItem()
    .setTitle('Q11. 账户整体，你能接受的最大回撤？ / Max drawdown you can live with?')
    .setChoiceValues(['10% 以内', '10–20%', '20–35%', '35% 以上'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q12. 单笔交易，你最多愿意亏账户的百分之几？ / Max loss per trade?')
    .setChoiceValues(['1% 以内', '1–2%', '2–5%', '没想过'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q13.（可跳过）用于这套打法的资金规模区间？ / Capital deployed on this approach?')
    .setChoiceValues(['$25k 以内', '$25–100k', '$100–500k', '$500k 以上', '不想说'])
    .setRequired(false);

  form.addMultipleChoiceItem()
    .setTitle('Q14. 过去 12 个月，你的实际收益和 SPY 比？ / Your last 12 months vs SPY?')
    .setChoiceValues(['跑输', '差不多', '跑赢', '没算过'])
    .setRequired(true);

  // —— 五、老会员 ——
  form.addSectionHeaderItem()
    .setTitle('五、给待了一阵子的你 / If you have been here a while')
    .setHelpText('加入不满 1 个月可以跳过这三题。');

  form.addParagraphTextItem()
    .setTitle('Q15. 这段时间你学到的最有用的一件事是什么？ / The most useful thing you have learned here?')
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('Q16. 有没有哪一笔交易，是因为这里才做对、或才躲开的？（有代码更好） / A trade you got right — or avoided — because of this?')
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('Q17. 我最该改进的一件事是什么？ / The one thing I should improve?')
    .setRequired(false);

  // —— 六、料理包 ——
  form.addSectionHeaderItem()
    .setTitle('六、一个还没做的东西 / Something we have not built yet');

  form.addMultipleChoiceItem()
    .setTitle('Q18. 每周给你实盘持仓、入场点、止损点、减仓点，你不需要自己选股——你会？ / A weekly follow-along pack. You would…')
    .setChoiceValues(['现在就要', '看价格再说', '不需要，我要自己学', '不确定'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Q19. 你觉得它每月值多少？ / What is it worth per month?')
    .setChoiceValues(['$50 以内', '$50–99', '$100–199', '$200 以上', '不会买'])
    .setRequired(true);

  form.addTextItem()
    .setTitle('Q20. 愿意和我做一次 15 分钟的一对一通话吗？愿意的话留个 Discord 名或邮箱。 / Up for a 15-minute call? Leave a handle or email.')
    .setRequired(false);

  Logger.log('填写链接（发给会员）: ' + form.getPublishedUrl());
  Logger.log('编辑链接（改题用）: ' + form.getEditUrl());
  return form.getPublishedUrl();
}

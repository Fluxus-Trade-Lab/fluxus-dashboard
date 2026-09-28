<!-- 新主线第一篇复盘长文,T-0927-82(created_by T-0927-56,Andy 09-27 W39 结算台定「一周一篇复盘长文」)。
     选题由 Steve 定(见任务单;09-27 亲自否掉原 $BE 时效性角度,换成本周广度分歧这条)。
     字由 mia 写,尚未发布 —— Steve 审稿/Andy 拍板前不要当成定稿。
     判据:两周三条 LONGFORM(此文 + 08-24 MRNA + 09-22 ARM)中位曝光 ≥158.5 才算「复盘长文」这条路走得通。
     每个数字的出处见文末 Sourcing 段,全部可用 `git show origin/main:data/output/breadth.json` 复核。 -->

# When Bulls and Bears Both Have the Right Numbers

**Sept 25, 2026.** Two traders, same tape, same day, opposite conclusions — and both of them were reading real numbers.

**10:52am ET, @PrimeTrading_:** "$QQQE is trying to confirm a daily reversal here, with breadth turning green to hook MCO back up... The rest of the market remains very weak, and Credit Spreads just keep making new highs, so definitely not a broad based rally so far, but let's see which side it swings."

**12:32pm ET, @NickSchmidt:** "Theres only a small group of stocks working and going higher while breadth is poor. The good news is they are growth stocks... the only group of stocks that the market can turn up and follow higher."

**3:51pm ET, @RealSimpleAriel, live into the close:** "The bears have failed with every opportunity they've been given to take this market lower. The bottom has fallen out of bonds. Yields are flying. Equal weight has gotten smoked. And yet, $QQQ is sitting at a new weekly all-time closing high."

Read only the first tweet and you'd think breadth just turned. Read only the third and you'd think breadth just confirmed it never will. Our regime engine logs both readings against the same date, in the same file, and its own label for the day was **"Inconclusive — signals split."** Not a hedge. A description.

## The number PrimeTrading_ was looking at

The NDX McClellan Oscillator sat at exactly 0.0 on Sept 23, slipped to −6.93 on Sept 24, and printed **+19.85 on Sept 25** — the first positive reading in the three sessions the engine has on file for this stretch. That's "breadth turning green to hook MCO back up," in a number.

## The number RealSimpleAriel was looking at

The share of the index above its 200-day average opened the week at 41.84% on Sept 22. It hasn't been back there since — 39.87%, then 39.22%, then **39.39% on Friday**. One green afternoon in the oscillator didn't buy back the 2.45 points this measure lost over the week. That's "equal weight has gotten smoked," in a number.

## Why the engine refuses to pick a side

Break the board down the way it actually tracks things, and the argument stops being an argument:

- **Index repair — confirmed.** SPY and QQQ are both back above their 50-day, 2 of 2. That's the leg RealSimpleAriel is standing on, and it's real.
- **Confirmation — not yet.** The five-day up/down ratio needs to clear 1.0 before the engine calls a reversal real. Friday it closed at 0.81.

Both of those are true on the same afternoon. One is a fact about the two names everyone already trades. The other is a fact about the other several thousand. PrimeTrading_ said as much himself, nine hours before RealSimpleAriel's tweet: *"not a broad based rally so far."* He wasn't disagreeing with her in advance. He was describing the same split the engine logged that night.

## What this actually says

Nobody here was wrong. $QQQE hooking up and the 200-day count sliding are not two competing stories about the same day — they're two layers of the same system moving at two different speeds. The oscillator can turn in an afternoon. The 200-day count took months to build and takes months to unwind; one green session doesn't reverse it.

The trade isn't guessing which trader gets proven right next week. It's knowing which layer you're actually trading before the position goes on — a reclaim in the two names everyone owns, or sponsorship actually handing back to everything else. Mix the two up and you end up long the wrong layer right before the one that's been lagging decides whether to catch up or roll over.

*When my opinion and my system disagree, I go with the system.* On Sept 25 the system's opinion was that it didn't have one yet — and refusing to have one was the correct read.

---

*Sourcing — every number above can be reproduced from this repo:*
*NDX McClellan Oscillator and % above 200-day: `data/output/breadth.json` → `history.mcclellan_osc_ndx` / `history.pct_above_200sma`, dates 2026-09-22 through 2026-09-25 (`history.dates`). Day verdict: `verdict.confirmation = "Inconclusive — signals split"`, `verdict.env = "MIXED"`. SPY/QQQ above-50-day and the 5-day ratio: `state_board.rows` (`index repair`, `confirmation`) and `verdict.vote_detail` (`ratio_5d` = 0.8115). Tweets: PrimeTrading_ status/2103497754102178134 (14:52 UTC), NickSchmidt status/2103522994442150041 (16:32 UTC), RealSimpleAriel status/2103573039141282130 (19:51 UTC) — full text captured in `data/content/x_watch/posts/2026-09-25.jsonl`; ET times are UTC−4 (EDT).*

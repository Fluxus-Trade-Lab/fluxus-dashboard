---
title: "Swing Trade Risk Management System"
source: "notion"
notion_id: "1555bc79-10f7-80bb-a6ce-f7c4a372243c"
notion_url: "https://www.notion.so/1555bc7910f780bba6cef7c4a372243c"
fetched: 2026-04-03
---

# Swing Trade Risk Management System

## Day 0 — Initial Stops

3 stops at the 33% level to LoD (Low of Day)

## Day 0-2

- If profit >2R, shave off 33%, adjust stop sizes accordingly
- If profit >4R, shave off 33% of net size, single stop at the average price (Breakeven)

## Day 3

- Reduce size by 33% if there is no profit taking and stop loss yet
- Single stop at breakeven
- Move stop to LoD of Day 3 if partially stopped out before

## Day 4+

- If profit > 3R, reduce 30% of net size, adjust stop sizes accordingly
- If 8-10x ATR% extension, reduce 30% of net size, adjust stop sizes accordingly
- 10MA as mental stop on day X
- SL: 5min ORL on day X+1
- Big gap down after closing below 10MA — SL: 15min ORL

## Inverse Pyramid

**Stop hit before Day 4:**
- Set alert at the High of stop day
- Add 50% back

**Sideway consolidation:**
- Add 50% of net size if below 4x ATR% extension

## Resources

- 3-Stop TWS Auto Order Panel & Tutorial
- [YouTube Tutorial](https://www.youtube.com/watch?v=gyi4Kl6VL3Q)
- [Will Hu's TWS Tool](https://x.com/traderwillhu/status/1945674251064775026)

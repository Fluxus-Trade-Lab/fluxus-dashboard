// Fallback figures for the public pages, used only when performance.json cannot
// be fetched. Source of truth is data/output/performance.json, generated from
// data/portfolio/reviews/h1_2026.json (H1 2026, 2025-12-31 → 2026-07-22).
//
// This module exists so LandingPage and ResultsPage cannot drift apart again:
// until 2026-08-31 the landing page advertised 72% / 2.1R / 340+ — invented
// placeholders that the 2026-08-16 ResultsPage cleanup did not reach.
export const PUBLIC_STATS = {
  winRate: 39.9,
  avgReturn: 0.88,
  totalTrades: 331,
  profitFactor: 2.48,
  avgHoldDays: 7.5,
  // H1 2026 account return and payoff ratio (avg win / avg loss). Same review
  // artifact as the rest: data/portfolio/reviews/h1_2026.json.
  h1Return: 90.5,
  payoff: 3.40,
  // Deepest MTM decline BY PERCENT. See ResultsPage for why percent, not dollar.
  maxDrawdown: -17.9,
}

# Dark Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a global dark/light theme toggle using CSS custom properties, migrating all 53 files from hardcoded stone colors to CSS variables.

**Architecture:** Define color tokens as CSS custom properties in `@theme`. A `.dark` class on `<html>` swaps all tokens. A `useTheme` hook manages state via localStorage. An inline script in `index.html` prevents FOUC.

**Tech Stack:** CSS custom properties, Tailwind CSS 4 `@theme`, React hook, localStorage

---

### Task 1: CSS Foundation — Theme Variables & Dark Overrides

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/index.html`

**Step 1: Rewrite index.css with complete token system**

Replace the entire `@theme` block and body styles. Add `html.dark` overrides. Remove the `!important` hacks (they'll conflict with variable-based approach).

```css
@import "tailwindcss";

@theme {
  --font-sans: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  --color-bg: #fafaf9;
  --color-surface: #ffffff;
  --color-surface-alt: #fafaf9;
  --color-surface-raised: #f5f5f4;
  --color-border: #e7e5e4;
  --color-border-light: #f5f5f4;
  --color-text: #1c1917;
  --color-text-secondary: #78716c;
  --color-text-muted: #a8a29e;
  --color-text-bold: #292524;

  --color-signal-power3: #22c55e;
  --color-signal-caution: #eab308;
  --color-signal-warning: #f97316;
  --color-signal-riskoff: #ef4444;

  --color-profit: #16a34a;
  --color-loss: #dc2626;
  --color-neutral: #78716c;
  --color-accent: #2d5f8a;
  --color-accent-light: #dbeafe;

  --color-active-tab-bg: #292524;
  --color-active-tab-text: #f5f5f4;
  --color-hover-bg: #f5f5f4;
  --color-input-bg: #ffffff;
  --color-input-border: #d6d3d1;
  --color-closed-row: #f5f5f4;
}

html.dark {
  --color-bg: #1c1917;
  --color-surface: #292524;
  --color-surface-alt: #1c1917;
  --color-surface-raised: #44403c;
  --color-border: #44403c;
  --color-border-light: #3a3733;
  --color-text: #e7e5e4;
  --color-text-secondary: #a8a29e;
  --color-text-muted: #78716c;
  --color-text-bold: #fafaf9;

  --color-active-tab-bg: #fafaf9;
  --color-active-tab-text: #1c1917;
  --color-hover-bg: #44403c;
  --color-input-bg: #1c1917;
  --color-input-border: #57534e;
  --color-closed-row: #44403c;

  --color-accent-light: #1e3a5f;
}

html {
  color-scheme: light;
}
html.dark {
  color-scheme: dark;
}

body {
  margin: 0;
  font-family: var(--font-sans);
  background-color: var(--color-bg);
  color: var(--color-text);
  min-height: 100vh;
}
```

**Step 2: Add FOUC-prevention script to index.html**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#1c1917" />
    <link rel="manifest" href="/manifest.json" />
    <script>
      // Prevent flash of wrong theme
      (function(){
        var t = localStorage.getItem('theme');
        if (t === 'dark') document.documentElement.classList.add('dark');
      })();
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
    <title>Fluxus Capital Dashboard</title>
  </head>
  <body class="antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

**Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds (no component changes yet, just CSS)

**Step 4: Commit**

```bash
git add frontend/src/index.css frontend/index.html
git commit -m "feat: add CSS dark mode token system and FOUC prevention"
```

---

### Task 2: useTheme Hook + Header Toggle

**Files:**
- Create: `frontend/src/hooks/useTheme.js`
- Modify: `frontend/src/components/Header.jsx`

**Step 1: Create useTheme hook**

```js
import { useState, useEffect } from 'react'

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'light'
    return localStorage.getItem('theme') || 'light'
  })

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggle = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

  return { theme, toggle }
}
```

**Step 2: Add toggle to Header.jsx**

Add a sun/moon icon button to the right side of the header, next to the timestamp. Use simple unicode characters (no icon library needed): `☀` for light mode (click to go dark), `☾` for dark mode (click to go light).

The header itself also needs migration:
- `bg-white` → `bg-[var(--color-surface)]`
- `border-stone-200` → `border-[var(--color-border)]`
- `text-stone-900` → `text-[var(--color-text)]`
- `text-stone-500` → `text-[var(--color-text-secondary)]`
- `hover:text-stone-800` → `hover:text-[var(--color-text)]`
- Active tab `bg-stone-800 text-stone-100` → `bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]`

**Step 3: Verify build + test toggle**

Run dev server, confirm toggle switches between light/dark, verify localStorage persistence.

**Step 4: Commit**

```bash
git add frontend/src/hooks/useTheme.js frontend/src/components/Header.jsx
git commit -m "feat: add useTheme hook and header dark mode toggle"
```

---

### Task 3: Core Layout Migration (Layout, App, Footer, TabNav)

**Files:**
- Modify: `frontend/src/App.jsx` — `bg-[#fafaf9]` → `bg-[var(--color-bg)]`
- Modify: `frontend/src/components/Layout.jsx` — `bg-[#fafaf9]` → `bg-[var(--color-bg)]`
- Modify: `frontend/src/components/Footer.jsx` — text colors
- Modify: `frontend/src/components/TabNav.jsx` — `bg-white`, `border-stone-200`, `text-stone-900`, `border-stone-900`

**Replacement rules for this batch:**
- `bg-[#fafaf9]` → `bg-[var(--color-bg)]`
- `bg-white` → `bg-[var(--color-surface)]`
- `border-stone-200` → `border-[var(--color-border)]`
- `text-stone-900` → `text-[var(--color-text)]`
- `border-stone-900` → `border-[var(--color-text)]`
- `text-stone-500` → `text-[var(--color-text-secondary)]`
- `text-stone-400` → `text-[var(--color-text-muted)]`

**Commit after verifying build.**

---

### Task 4: Dashboard Page Migration (Macro, Equities, Screeners sections)

**Files (9):**
- `frontend/src/components/macro/MacroSection.jsx`
- `frontend/src/components/macro/MarketConditions.jsx`
- `frontend/src/components/macro/SignalLights.jsx`
- `frontend/src/components/macro/TrendStatus.jsx`
- `frontend/src/components/macro/PowerTrend.jsx`
- `frontend/src/components/equities/EtfSection.jsx`
- `frontend/src/components/shared/EtfRow.jsx`
- `frontend/src/components/shared/LeveragedInfo.jsx`
- `frontend/src/components/screeners/ScreenerSection.jsx`

**Replacement rules (same as Task 3 plus):**
- `bg-stone-50/50` → `bg-[var(--color-surface-alt)]/50`
- `text-stone-800` → `text-[var(--color-text-bold)]`
- `border-stone-100` → `border-[var(--color-border-light)]`
- `bg-stone-50` (standalone, not alt-row) → `bg-[var(--color-bg)]`
- `hover:bg-stone-50` → `hover:bg-[var(--color-hover-bg)]`

**Commit after verifying build.**

---

### Task 5: Screener Page Migration

**Files (5):**
- `frontend/src/components/screener/ScreenerPage.jsx`
- `frontend/src/components/screener/FilterPanel.jsx`
- `frontend/src/components/screener/PresetBar.jsx`
- `frontend/src/components/screener/ResultsTable.jsx`
- `frontend/src/components/screener/RangeFilter.jsx`

**Same replacement rules as Task 4. Plus for inputs:**
- `bg-white` on inputs → `bg-[var(--color-input-bg)]`
- `border-stone-300` on inputs → `border-[var(--color-input-border)]`

**Commit after verifying build.**

---

### Task 6: Screener Cards Migration (VCP, EP, Stockbee, etc.)

**Files (5):**
- `frontend/src/components/screeners/VcpResults.jsx`
- `frontend/src/components/screeners/EpisodicPivot.jsx`
- `frontend/src/components/screeners/StockbeeRatio.jsx`
- `frontend/src/components/screeners/HealthyCharts.jsx`
- `frontend/src/components/screeners/Ema21Watch.jsx`
- `frontend/src/components/screeners/Momentum97.jsx`

**Same replacement rules. Commit after verifying build.**

---

### Task 7: Breadth Page Migration

**Files (5):**
- `frontend/src/components/breadth/BreadthPage.jsx`
- `frontend/src/components/breadth/BreadthTable.jsx`
- `frontend/src/components/breadth/BreadthCharts.jsx`
- `frontend/src/components/breadth/MarketMonitor.jsx`
- `frontend/src/components/breadth/ClassicBreadth.jsx`

**Same replacement rules. Commit after verifying build.**

---

### Task 8: Portfolio Page Migration

**Files (13):**
- `frontend/src/components/portfolio/PortfolioLayout.jsx`
- `frontend/src/components/portfolio/PortfolioHeader.jsx`
- `frontend/src/components/portfolio/TradeForm.jsx`
- `frontend/src/components/portfolio/OptionsTradeForm.jsx`
- `frontend/src/components/portfolio/TrimModal.jsx`
- `frontend/src/components/portfolio/SettingsPanel.jsx`
- `frontend/src/components/portfolio/ui/StatCard.jsx`
- `frontend/src/components/portfolio/ui/InputField.jsx`
- `frontend/src/components/portfolio/tabs/PLTab.jsx`
- `frontend/src/components/portfolio/tabs/ExposureTab.jsx`
- `frontend/src/components/portfolio/tabs/PerformanceTab.jsx`
- `frontend/src/components/portfolio/tabs/MonthlyTab.jsx`
- `frontend/src/components/portfolio/tabs/RiskTab.jsx`
- `frontend/src/components/portfolio/tabs/ThreeStopTab.jsx`
- `frontend/src/components/portfolio/tabs/OptionsTab.jsx`

**Additional rules for portfolio:**
- `bg-stone-100 opacity-55` (closed rows in PLTab) → `bg-[var(--color-closed-row)] opacity-55`
- `bg-stone-50` on StatCard/forms → `bg-[var(--color-bg)]`
- `border-stone-300` on inputs → `border-[var(--color-input-border)]`
- `focus:border-stone-500` → `focus:border-[var(--color-text-secondary)]`
- `text-stone-600` → `text-[var(--color-text-secondary)]`

**Commit after verifying build.**

---

### Task 9: Briefing, Journal, Model Books Migration

**Files (10):**
- `frontend/src/components/briefing/BriefingPage.jsx`
- `frontend/src/components/briefing/DateNav.jsx`
- `frontend/src/components/briefing/RecapViewer.jsx`
- `frontend/src/components/briefing/DailyNotes.jsx`
- `frontend/src/components/journal/JournalPage.jsx`
- `frontend/src/components/journal/AnalyticsTab.jsx`
- `frontend/src/components/journal/CoachTab.jsx`
- `frontend/src/components/modelbooks/ModelBooksPage.jsx`
- `frontend/src/components/modelbooks/BrowseView.jsx`
- `frontend/src/components/modelbooks/StudyMode.jsx`

**Same replacement rules. Additional for prose (RecapViewer):**
- `prose-headings:text-stone-800` → `prose-headings:text-[var(--color-text-bold)]`
- `prose-strong:text-stone-800` → `prose-strong:text-[var(--color-text-bold)]`

**Commit after verifying build.**

---

### Task 10: Utility Files Migration

**Files (2):**
- `frontend/src/lib/format.js` — signal dot color references (these use Tailwind class strings returned by functions)
- `frontend/src/components/portfolio/lib/portfolioFormat.js` — color utility functions

These files return Tailwind class strings like `'text-green-600'`, `'text-red-500'`, `'bg-stone-100'`. The signal colors (green/red/amber) should stay as-is. Only migrate stone-colored background/text references.

**Commit after verifying build.**

---

### Task 11: Visual QA — Full Page Screenshots

**No code changes.** Run the dev server, navigate to every page in both light and dark mode, take screenshots to verify:

1. Dashboard (Macro/Equities/Screeners)
2. Screener page
3. Portfolio (P/L, Options tabs)
4. AI Coach
5. Briefing
6. Breadth
7. Model Books

Fix any issues found during QA.

**Final commit with any fixes.**

---

## Parallelization Notes

Tasks 4-9 are **independent** — they touch different file sets with identical replacement rules. They can be dispatched as parallel agents. Tasks 1-3 must run first (foundation). Task 10 can run after Task 3. Task 11 runs last.

**Execution order:**
1. Task 1 (CSS foundation)
2. Task 2 (hook + header)
3. Task 3 (core layout)
4. Tasks 4-9 in parallel (all page migrations)
5. Task 10 (utility files)
6. Task 11 (visual QA)

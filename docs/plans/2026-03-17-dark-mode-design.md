# Dark Mode — Design Document

**Date**: 2026-03-17
**Status**: Approved

## Problem

The current light-only UI (stone-50 backgrounds, white cards) is too bright for nighttime use.

## Solution

Add a global dark/light theme toggle using CSS custom properties. A single `.dark` class on `<html>` swaps all color tokens.

## Color Token System

All hardcoded Tailwind colors are replaced with CSS variables defined in `@theme`.

| Token | Used for | Light | Dark |
|-------|----------|-------|------|
| `--color-bg` | Page background | `#fafaf9` (stone-50) | `#1c1917` (stone-900) |
| `--color-surface` | Cards, modals | `#ffffff` (white) | `#292524` (stone-800) |
| `--color-surface-alt` | Alternating rows, hover | `#fafaf9` (stone-50) | `#1c1917` (stone-900) |
| `--color-border` | All borders | `#e7e5e4` (stone-200) | `#44403c` (stone-700) |
| `--color-border-light` | Table row dividers | `#f5f5f4` (stone-100) | `#57534e` (stone-600) |
| `--color-text` | Primary text | `#1c1917` (stone-900) | `#e7e5e4` (stone-200) |
| `--color-text-secondary` | Labels, secondary | `#78716c` (stone-500) | `#a8a29e` (stone-400) |
| `--color-text-muted` | Timestamps, hints | `#a8a29e` (stone-400) | `#78716c` (stone-500) |

Signal colors (green/red/amber for P&L, badges, status indicators) remain unchanged — they have sufficient contrast on both light and dark backgrounds.

## Toggle & State

- **Location**: Sun/moon icon in Header, top-right next to timestamp
- **Storage**: `localStorage` key `theme` — values `'light'` or `'dark'`
- **Mechanism**: Toggles `.dark` class on `<html>`, which swaps CSS variables
- **Default**: Light mode (no change for existing users)
- **FOUC prevention**: Inline script in `index.html` reads localStorage and applies `.dark` before first paint

## Approach: CSS Custom Properties

Chosen over Tailwind `dark:` variants (doubles class lists) and CSS filter inversion (breaks images/charts).

### Migration Patterns (117 occurrences across 45 files)

| Pattern | ~Count | Replace with |
|---------|--------|-------------|
| `bg-white` | 30 | `bg-[var(--color-surface)]` |
| `bg-stone-50` / `bg-[#fafaf9]` | 25 | `bg-[var(--color-bg)]` |
| `bg-stone-50/50` (alt rows) | 10 | `bg-[var(--color-surface-alt)]/50` |
| `border-stone-200` / `border-stone-100` | 25 | `border-[var(--color-border)]` / `border-[var(--color-border-light)]` |
| `text-stone-900` / `text-stone-800` | 10 | `text-[var(--color-text)]` |
| `text-stone-500` / `text-stone-400` | 17 | `text-[var(--color-text-secondary)]` / `text-[var(--color-text-muted)]` |

## Files

### New
- `frontend/src/hooks/useTheme.js` — hook: `{theme, toggle}`, reads/writes localStorage + `<html>` class

### Modify
- `frontend/index.html` — inline FOUC-prevention script
- `frontend/src/index.css` — expand `@theme`, add `html.dark` overrides, remove `!important` hacks
- `frontend/src/components/Header.jsx` — add sun/moon toggle button
- ~45 component files — swap hardcoded colors to CSS variable references

## Design Principles

- **Warm stone palette** — dark mode uses stone-800/900, not cold blue-black
- **Same signal colors** — green/red/amber P&L colors stay consistent across modes
- **Anti-dopamine** — no flashy transitions or neon accents in dark mode
- **Persist preference** — once you pick dark, it stays dark across sessions

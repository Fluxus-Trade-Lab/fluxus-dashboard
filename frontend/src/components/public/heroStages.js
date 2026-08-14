/**
 * The five panels of the Swing Trading Masterclass poster, as coordinates.
 *
 * Each stage is the same cast of circles — fourteen blue, fourteen red — in a
 * different arrangement. A circle keeps its colour for its whole life: lerping
 * between poster blue and poster red would pass through a muddy purple that
 * belongs to neither, so the layouts are authored around a fixed cast instead.
 * A circle a stage has no use for is parked at PARK with radius zero, which is
 * how a stage of eight circles and a stage of twenty-eight are the same object.
 *
 * Coordinates are fractions of the field's square: x rightward, y DOWNWARD (the
 * reading order of the poster panels), radius in units of the square's side.
 *
 *   0  reversal   descend, floor, climb — red down the left, blue up the right,
 *                 the two heaviest circles at the turn. The green triangle that
 *                 marks the low is drawn by HeroField, not listed here.
 *   1  funnel     eight names across the top, narrowing through the screens to
 *                 one leader. The rows are 8 → 4 → 3 → 1.
 *   2  scatter    setups strewn across the whole square at every size. The one
 *                 stage that uses the full cast — the market as it actually
 *                 arrives, before anything has been selected.
 *   3  grid       nine nodes, and the sizes are the lesson: same setups, and
 *                 the position is what differs. The biggest circles run off the
 *                 edge of the square exactly as they do on the poster.
 *   4  taiji      every circle collapses into the centre and the contest is
 *                 drawn by HeroField from halves and lobes.
 */

export const BLUE_N = 14
export const RED_N = 14

/** Where an unused circle waits — dead centre, radius zero. */
export const PARK = [0.47, 0.47, 0]

const park = (n) => Array.from({ length: n }, () => PARK)

// ── 0 · reversal ────────────────────────────────────────────────────────────
const S_REVERSAL = {
  red: [
    [0.14, 0.13, 0.030], [0.21, 0.21, 0.017], [0.18, 0.31, 0.052],
    [0.26, 0.42, 0.025], [0.29, 0.57, 0.086], [0.35, 0.68, 0.019],
    ...park(8),
  ],
  blue: [
    [0.45, 0.61, 0.066], [0.39, 0.72, 0.020], [0.53, 0.46, 0.027],
    [0.58, 0.35, 0.042], [0.65, 0.24, 0.050], [0.71, 0.15, 0.022],
    ...park(8),
  ],
}

// ── 1 · funnel ──────────────────────────────────────────────────────────────
const S_FUNNEL = {
  red: [
    [0.12, 0.11, 0.015], [0.32, 0.11, 0.015], [0.52, 0.11, 0.015], [0.72, 0.11, 0.015],
    [0.20, 0.33, 0.027], [0.56, 0.33, 0.027],
    [0.30, 0.52, 0.033], [0.66, 0.52, 0.033],
    ...park(6),
  ],
  blue: [
    [0.22, 0.11, 0.015], [0.42, 0.11, 0.015], [0.62, 0.11, 0.015], [0.82, 0.11, 0.015],
    [0.38, 0.33, 0.027], [0.74, 0.33, 0.027],
    [0.50, 0.52, 0.033],
    [0.46, 0.78, 0.100],          // the one leader the funnel was for
    ...park(6),
  ],
}

// ── 2 · scatter ─────────────────────────────────────────────────────────────
const S_SCATTER = {
  red: [
    [0.09, 0.22, 0.014], [0.23, 0.09, 0.030], [0.38, 0.19, 0.020], [0.16, 0.44, 0.041],
    [0.31, 0.36, 0.012], [0.47, 0.31, 0.026], [0.60, 0.12, 0.017], [0.72, 0.27, 0.034],
    [0.55, 0.49, 0.011], [0.83, 0.44, 0.022], [0.26, 0.62, 0.029], [0.44, 0.72, 0.016],
    [0.68, 0.66, 0.038], [0.87, 0.79, 0.013],
  ],
  blue: [
    [0.15, 0.13, 0.019], [0.33, 0.25, 0.036], [0.06, 0.34, 0.011], [0.49, 0.14, 0.023],
    [0.62, 0.35, 0.015], [0.78, 0.13, 0.032], [0.21, 0.53, 0.017], [0.40, 0.47, 0.044],
    [0.58, 0.60, 0.021], [0.76, 0.52, 0.013], [0.12, 0.72, 0.025], [0.35, 0.83, 0.033],
    [0.55, 0.80, 0.014], [0.80, 0.71, 0.018],
  ],
}

// ── 3 · grid ────────────────────────────────────────────────────────────────
// Every circle sits exactly on the lattice, so GRID_LINES below can be drawn
// through the nodes rather than near them.
const GX = [0.17, 0.45, 0.70]
const GY = [0.15, 0.45, 0.74]
const S_GRID = {
  blue: [
    [GX[0], GY[0], 0.088], [GX[2], GY[0], 0.019], [GX[1], GY[1], 0.023], [GX[2], GY[2], 0.046],
    ...park(10),
  ],
  red: [
    [GX[1], GY[0], 0.011], [GX[2], GY[1], 0.072], [GX[0], GY[1], 0.017],
    [GX[0], GY[2], 0.082], [GX[1], GY[2], 0.013],
    ...park(9),
  ],
}

// ── 4 · taiji ───────────────────────────────────────────────────────────────
// Pointillist, because the field's circles are now material spheres and a flat
// vector taiji would be a sticker in a photograph. The spheres THEMSELVES form
// the figure: two interlocking commas, each a head sweeping into a tail that
// wraps the other's head, each head carrying the other colour's seed. Same
// cast, no extra geometry — the finale is made of the same bodies that were
// the market, the funnel and the grid, which is the claim anyway.
//
// Authored on a circle at C = (0.47, 0.47). Each fish is a MASS, not an
// outline — a big head and a body of shrinking spheres that curls around the
// other's head — because the first draft traced the rim and read as a ring
// with a hole where the S should be. The blue fish is the red one rotated
// half a turn about C, coordinate for coordinate, so the balance is exact.
const S_TAIJI = {
  red: [
    [0.47, 0.335, 0.095],                                    // head, upper centre
    [0.575, 0.305, 0.042], [0.545, 0.24, 0.030],             // shoulder over the top
    [0.585, 0.40, 0.050], [0.63, 0.50, 0.055],               // body down the right
    [0.60, 0.60, 0.045], [0.52, 0.655, 0.035],               // tail curling under the blue head
    [0.47, 0.605, 0.038],                                    // seed in the blue head
    ...park(6),
  ],
  blue: [
    [0.47, 0.605, 0.095],
    [0.365, 0.635, 0.042], [0.395, 0.70, 0.030],
    [0.355, 0.54, 0.050], [0.31, 0.44, 0.055],
    [0.34, 0.34, 0.045], [0.42, 0.285, 0.035],
    [0.47, 0.335, 0.038],                                    // seed in the red head
    ...park(6),
  ],
}

export const STAGES = [S_REVERSAL, S_FUNNEL, S_SCATTER, S_GRID, S_TAIJI]

/** Names, in stage order — for the contact sheet, and for anything that later
 *  wants to caption the field. */
export const STAGE_NAMES = ['reversal', 'funnel', 'scatter', 'grid', 'taiji']

/** The one shape a single stage owns, kept here so the renderer and the
 *  contact sheet cannot drift apart on where it sits. (The taiji used to be a
 *  second one, drawn from vector halves and lobes; it is now a sphere layout
 *  like every other stage, in STAGES[4].) */
export const TRIANGLE = { x: 0.40, y: 0.775, r: 0.030 }   // stage 0, the turn

/**
 * The connective tissue — and it is not decoration.
 *
 * Without the links, stage 1 is three rows of dots and a big circle; the links
 * are what make it a funnel. Without the rules, stage 3 is five circles at
 * arbitrary spots; the rules are what make it a grid, which is the whole claim
 * that the SAME nodes get different sizes. The poster draws both, faintly, in
 * grey, and it draws them for exactly this reason.
 *
 * Each link is [x0, y0, x1, y1]. The curve's control point sits at (x0, y1) —
 * it leaves the parent straight down and swings into the child, the way the
 * poster's connectors hang.
 */
export const FUNNEL_LINKS = [
  // eight names → four
  [0.12, 0.11, 0.20, 0.33], [0.22, 0.11, 0.20, 0.33],
  [0.32, 0.11, 0.38, 0.33], [0.42, 0.11, 0.38, 0.33],
  [0.52, 0.11, 0.56, 0.33], [0.62, 0.11, 0.56, 0.33],
  [0.72, 0.11, 0.74, 0.33], [0.82, 0.11, 0.74, 0.33],
  // four → three
  [0.20, 0.33, 0.30, 0.52], [0.38, 0.33, 0.30, 0.52],
  [0.56, 0.33, 0.50, 0.52], [0.74, 0.33, 0.66, 0.52],
  // three → the one it was all for
  [0.30, 0.52, 0.46, 0.78], [0.50, 0.52, 0.46, 0.78], [0.66, 0.52, 0.46, 0.78],
]

/** Straight rules through the lattice, run past the outer nodes so the grid
 *  reads as a field the nodes sit in rather than a closed box. */
export const GRID_LINES = [
  ...GY.map((y) => [0.05, y, 0.88, y]),
  ...GX.map((x) => [x, 0.04, x, 0.88]),
]

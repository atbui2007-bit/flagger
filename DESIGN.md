---
name: Flagger
description: A dark ledger of AI-authored engineering activity, living inside quiet frosted glass.
colors:
  aurora-blue: "#8da2ff"
  aurora-violet: "#b892ff"
  aurora-cyan: "#7fd8ea"
  canvas: "#0f1017"
  canvas-deep: "#0a0b10"
  surface: "#16181f"
  surface-strong: "#1d2029"
  glass-fill: "#ffffff14"
  glass-border: "#ffffff24"
  row-fill: "#16181fd6"
  row-fill-hover: "#1d2029eb"
  ink: "#edeff5"
  soft-ink: "#b8bfcc"
  muted-ink: "#8b93a3"
  divider: "#262a35"
  code-surface: "#1c1f28"
  review: "#f5a08c"
  review-surface: "#3a231e"
  reviewed: "#7fc4dc"
  reviewed-surface: "#17323c"
  approved: "#83d6a5"
  approved-surface: "#1a3527"
  light-canvas: "#f3f4f8"
  light-surface: "#ffffff"
  light-glass-fill: "#ffffffb8"
  light-glass-border: "#1e222b24"
  light-row-fill: "#ffffffe0"
  light-ink: "#1e222b"
  light-muted-ink: "#5b6373"
  light-divider: "#dfe2ea"
  light-accent: "#4f66d8"
  light-review: "#a33d2a"
  light-reviewed: "#2a6086"
  light-approved: "#1f6b45"
typography:
  display:
    fontFamily: "system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "56px"
    fontWeight: 500
    lineHeight: "1.18"
    letterSpacing: "-1.68px"
  title:
    fontFamily: "system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "24px"
    fontWeight: 500
    lineHeight: "1.18"
    letterSpacing: "-0.24px"
  body:
    fontFamily: "system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: "1.5"
  label:
    fontFamily: "ui-monospace, Consolas, monospace"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: "1.35"
rounded:
  xs: "5px"
  sm: "10px"
  md: "14px"
  lg: "20px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "32px"
components:
  sidebar:
    backgroundColor: "{colors.glass-fill}"
    textColor: "{colors.ink}"
    padding: "24px 16px"
    width: "220px"
  summary-strip:
    textColor: "{colors.muted-ink}"
    typography: "{typography.body}"
  activity-row:
    backgroundColor: "{colors.row-fill}"
    textColor: "{colors.ink}"
    padding: "12px 16px"
  ledger-shell:
    backgroundColor: "{colors.glass-fill}"
    rounded: "{rounded.lg}"
  inspector-panel:
    backgroundColor: "{colors.glass-fill}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "24px"
  button-primary:
    backgroundColor: "{colors.aurora-blue}"
    textColor: "{colors.canvas-deep}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
  commit-sha:
    backgroundColor: "{colors.code-surface}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "2px 6px"
---

# Design System: Flagger

## 1. Overview

**Creative North Star: "The Ledger Under Glass" — glass-forward evolution**

Flagger is a dark, legible record of AI-authored engineering activity that **lives
inside frosted glass**. Every container — the ledger shell, agent and repository
tables, filters, state cards, the Evidence Inspector, the login panel — is a rounded
glass panel floating over a composed wallpaper-grade gradient canvas: translucent,
softly blurred, edged with a hairline light border. The evidence itself never
degrades: rows of dense data
sit on a high-opacity tint *inside* the glass so text stays crisp while the panel
around it refracts the glow.

Premium is carried by material and motion — glass, glow, generous radius and spacing,
softened labels, and a minimal purposeful motion system — never by removing
information. All columns and signals stay; the 30-second risk-detection purpose is
untouched. The atmosphere is one composed canvas of three cool fields: a dominant
blue core off-canvas at the upper left, a cyan counterweight at the lower right, and
a violet bridge at top center, finished with mandatory debanding grain. The quietest
region sits behind the content column while exposed shell chrome crosses at least one
field's falloff, giving the glass a luminance boundary to refract. The canvas drifts
almost imperceptibly on a ≥100-second cycle and freezes under reduced motion. The
system still explicitly rejects maximalist observability walls,
gamification, alarmist presentation, and color-only risk signals.

**Key Characteristics:**

- Rounded frosted-glass panels for every container; blur owned by panel shells only
- Contiguous, high-opacity tinted rows inside the glass — evidence stays crisp
- Real glass material: inner light edges, layered shadows, faint grain on large shells
- Dark-first; light theme reads as glass through borders and cool shadow, not blur
- Cool aurora accent family (blue-violet-cyan); warm color reserved for review states
- Wallpaper-grade three-field canvas with off-edge cores, a quiet center, and
  debanding grain in barely perceptible drift; frozen under reduced motion
- Minimal purposeful motion: feedback, one-time entrances, quiet view fades
- Familiar Git typography: monospace for SHAs, branches, and code only

## 2. Colors

A near-black cool foundation, one aurora accent family for action and selection, and
warm/cool state colors reserved exclusively for review status.

### Primary
- **Aurora Blue** (`#8da2ff`): The action color. Primary buttons, current selection,
  focus rings, active filters, links. Used on ≤10% of any screen; its scarcity keeps
  the ledger quiet.

### Secondary
- **Aurora Violet** (`#b892ff`): The top-center bridge field and occasional
  large-surface tint (never body text). Exists mostly *behind* the glass.
- **Aurora Cyan** (`#7fd8ea`): The lower-right counterweight field; also small data
  highlights (sparklines, agent attribution marks) where Aurora Blue is already in use.

### Tertiary (review states — the only non-aurora chroma)
- **Review** (`#f5a08c` on `#3a231e`): Needs-review. Deliberately warm so it can never
  be mistaken for the cool aurora family. Always paired with the word "Review" and/or
  an icon.
- **Reviewed** (`#7fc4dc` on `#17323c`): Reviewed-not-approved.
- **Approved** (`#83d6a5` on `#1a3527`): Approved.

### Neutral
- **Canvas** (`#0f1017`) and **Canvas Deep** (`#0a0b10`): The workspace. Canvas Deep
  sits behind the wallpaper fields at the page root.
- **Glass Fill** (`#ffffff14`, white at 8%) + **Glass Border** (`#ffffff24`, white at
  14%): the two ingredients of a glass panel, paired with a shell-level
  `backdrop-filter` (see the Single Blur Rule).
- **Row Fill** (`rgba(22,24,31,0.84)`) / **Row Fill Hover** (`rgba(29,32,41,0.92)`):
  the tint under dense text inside glass panels. Derived from Surface's own hue —
  never white mixed into glass — so rows keep the ledger's color while a hint of the
  aurora passes through.
- **Surface** (`#16181f`) / **Surface Strong** (`#1d2029`): opaque planes for the
  fallback modes and small solid elements (selects' option lists, code capsules).
- **Ink** (`#edeff5`), **Soft Ink** (`#b8bfcc`), **Muted Ink** (`#8b93a3`): text
  hierarchy. Muted Ink is the floor — nothing dimmer may carry information.
- **Divider** (`#262a35`), **Code Surface** (`#1c1f28`).
- **Light theme** (`light-*` tokens): cool near-white canvas; glass is translucent
  cool white (72%) with a dark hairline border (14%) and rows at 88% white. In light
  mode the glass reads through its border, inset highlight, and cool shadow — blur
  strength carries less of the signal. Darkened accent (`#4f66d8`) and state colors
  keep every text role ≥4.5:1.

**The Glass Panels, Legible Rows Rule.** Any container may be glass: ledger shells,
tables, filters, cards, panels, overlays. But any surface carrying more than two
lines of dense text sits on Row Fill (≥80% opacity) *inside* the glass. Rows are
never independently glass, and text never sits directly on blur.

**The Wallpaper Canvas Rule.** Exactly three cool fields — a blue dominant upper-left
core off-canvas, a cyan counterweight at the lower right, and a violet bridge at top
center — compose one stacked-radial background on **one oversized backdrop layer**.
Every field fades to its own hue at alpha 0 through four eased stops; never use a
linear ramp to transparent. A 128px debanding grain layer is mandatory and topmost.
The content column's center is the quietest region, not a uniformly quiet region: at
least one field's falloff must cross exposed shell chrome so the glass straddles a
luminance boundary. Evidence rows stay on a ≥84% tint. Warm and salmon hues are
banned from the canvas and remain reserved for review states. The layer drifts
transform-only (translate/scale, GPU-composited) on a ≥100-second alternating cycle.
The drift must be below the threshold of casual notice: if a user can see the
background moving, it is too fast. Under `prefers-reduced-motion` the layer is frozen
at a static transform; if profiling shows frame instability beneath the blurred
shells, ship it static — never compensate with a slower repaint-driven technique
(`background-position` animation is banned).

**The Redundancy Rule.** Risk and review status always pair color with explicit text
and, where useful, a distinct icon. Color is never the only signal.

## 3. Typography

**Display Font:** system-ui (with Segoe UI and Roboto fallbacks)
**Body Font:** system-ui (with Segoe UI and Roboto fallbacks)
**Label/Mono Font:** ui-monospace (with Consolas fallback)

**Character:** One system sans keeps the product native and unobtrusive against the
atmospheric backdrop; the type does the ledger's work while the glass does the mood.
Monospace is reserved for Git identifiers and machine-readable evidence. Labels are
calm: sentence case at readable sizes — no uppercase tracked micro-labels anywhere.

### Hierarchy
- **Display** (500, 56px, 1.18): Rare page-level headings only; 36px on compact screens.
- **Title** (500, 24px, 1.18): Section headings; 20px on compact screens.
- **Body** (400, 16px, 1.5): Commit messages and explanatory content. Prose capped at
  65–75ch; dense table/feed content may run wider.
- **Label** (600, 13px mono, 1.35): SHAs, branches, filenames, compact technical
  identifiers, with `font-variant-numeric: tabular-nums`.
- **Column headers** (600, 12px sans, sentence case, no added letter-spacing): table
  and ledger headers. Never uppercase, never tracked.

**The Evidence Type Rule.** Monospace for SHAs, branches, filenames, and code only.
Never as general atmosphere.

**The Legible Glass Rule.** Text on glass must be Ink or Soft Ink and must pass 4.5:1
against the *darkest plausible* content scrolling beneath the panel. Dense text gets
Row Fill under it; if a text role still fails, the panel gains an opaque scrim — the
text never gets lighter.

## 4. Elevation

Depth comes from three layers, back to front: the wallpaper-grade gradient canvas,
glass panel shells, and tinted rows riding inside them. Glass panels carry a soft ambient shadow
(`0 12px 32px rgba(0,0,0,0.35)`) plus their hairline light border — that combination
is what reads as "glass", not the blur alone. Rows are flat: separated by Divider
rules and tone, no shadows at rest.

### Shadow Vocabulary
- **glass-ambient** (dark): a layered stack that carries the inner light edge —
  `inset 0 1px 0 rgba(255,255,255,.10), inset 1px 0 0 rgba(255,255,255,.035),
  0 18px 48px rgba(0,0,0,.32), 0 4px 14px rgba(0,0,0,.22)` — on large floating
  shells. Light theme: `inset 0 1px 0 rgba(255,255,255,.88), inset 1px 0 0
  rgba(255,255,255,.38), 0 16px 42px rgba(48,58,90,.12), 0 3px 10px
  rgba(48,58,90,.08)`. The inset top edge is the light catching the glass lip; it
  supplements the 1px Glass Border, never replaces it. The sidebar keeps its
  no-drop-shadow treatment.
- **overlay** (`box-shadow: 0 20px 48px rgba(0,0,0,0.5)`): dropdowns, dialogs, toasts.

### Material Grain
One cached 128×128 inline-SVG `feTurbulence` tile (`baseFrequency=.72`,
`numOctaves=3`, `stitchTiles="stitch"`, grayscale) is the mandatory topmost canvas
layer and is also layered as a background beneath content on **large shells** —
ledger/agents/repositories shells, Evidence Inspector, PR sections, login panel — at
~3% alpha dark / ~1.5% light. Never on
chips, pills, rows, buttons, or the sidebar: at small scale grain reads as
decoration. Grain is a background layer, not an overlay above text, and adds no
extra blur.

**The Single Blur Rule.** `backdrop-filter` belongs to panel shells only, exactly one
level deep. Large panels (ledger shells, inspector, login) use `blur(12px)
saturate(1.35)`; small chrome (filter pills, dropdowns, transient overlays) may use up
to `blur(16px) saturate(1.35)` — 16px is the hard cap. Never nest a blur inside a
blurred ancestor (inner sections use Row Fill, no second `backdrop-filter`), and never
put blur on individual rows — one shell-level capture instead of dozens. Keep the blur
and its rounded clip (`overflow: hidden`) on the same element; avoid transforms on
children of blurred shells.

**The Opaque Fallback Rule.** Under `prefers-reduced-transparency`, `forced-colors`,
or missing `backdrop-filter` support, every glass token resolves to opaque Surface
Strong with a Divider border and Row Fill resolves to solid Surface — the layout must
not change.

**The Flat Evidence Rule.** Rows remain flat at rest. Row hover is a tonal shift
(Row Fill → Row Fill Hover), never elevation, never a card.

## 5. Motion

Minimal and purposeful: motion conveys state, gives feedback, and lets the interface
greet its owner — it never decorates for its own sake. Only the user's current action
should be readily noticeable; ambient motion (canvas, shimmer) stays below casual
notice.

### Tokens
- Durations: `--motion-press: 90ms`, `--motion-fast: 140ms`, `--motion-ui: 200ms`,
  `--motion-enter: 320ms`, `--motion-route: 180ms`, `--motion-exit: 160ms`.
- Easings: `--ease-out: cubic-bezier(.16,1,.3,1)` (entrances),
  `--ease-standard: cubic-bezier(.2,0,0,1)` (state changes),
  `--ease-in: cubic-bezier(.4,0,1,1)` (exits),
  `--ease-ambient: cubic-bezier(.45,0,.55,1)` (wallpaper canvas only).
  No bounce, no elastic, ever.

### Layers
- **Feedback (constant):** buttons press with `translateY(1px) scale(.99)` at 90ms;
  color/border shifts at 140ms; rows keep tonal hover only — never lift. Blurred
  panel shells change border/shadow only: **no transforms on a blurred shell**.
- **Entrance (once per mount):** ledger rows rise 6px + fade over 320ms, staggered
  50ms by a global row index capped at 9 (≤450ms total). Rows are fully visible in
  base CSS — the animation is an enhancement layered on top, and it must never
  re-fire on refetch, filter change, sort change, or pagination (first successful
  page only; the entrance is consumed after it plays).
- **View transitions:** route content fades in over 180ms (keyed container; a fade,
  not a fake crossfade). Evidence Inspector enters at 240ms and exits at 160ms
  `--ease-in`, retained in the tree until the exit completes. Never animate
  workspace width/padding — that reflows the ledger.
- **Exits are faster than entrances** (~75% of enter duration).

### Reduced Motion
`prefers-reduced-motion` collapses every transition/animation to near-instant and
freezes the wallpaper canvas. This is non-negotiable and already token-driven.

## 6. Components

**Page rhythm (all data views).** Content centers on a shared 1126px frame —
Activity, Agents, and Repositories align to the same measure (PR detail matches it
too). Page headings are 24px/600 with 4px to their subtitle and 24px to the content
below. Filters sit tight to the ledger (8px between pills, 12px to the shell, no
trailing border). Ledger to pagination is 12px; pagination is a 44px band. The beat
is tight groups, generous section breaks — never four equal bands.

### Sidebar (glass)
- **Style:** Full-height frosted panel — Glass Fill, shell-level blur, right edge is
  Glass Border (no drop shadow; it sits on the canvas).
- **Brand lockup:** a 22px glass tile beside the "Flagger" wordmark holding three
  small solid aurora dots (blue centered, violet upper-left, cyan lower-right, at
  70–85% opacity). The wordmark stays solid Ink — no gradient text, no glow, no
  animation.
- **Nav:** Soft Ink links; active view in Aurora Blue on a 12% accent tint.
- **Behavior:** Sticky; content scrolling beneath it is what makes it read as glass.

### Summary Strip (glass capsule)
- **Shape:** Pill-shaped glass capsule in the page heading — Glass Fill + Glass
  Border, small-chrome blur.
- **Content:** review-needed count first, then AI-authored %, then total commits —
  plain Ink figures with Soft Ink labels. No gradient tiles, no per-stat cards.
- **Review-needed emphasis:** when > 0, the review-needed *number* renders in the
  Review color at 1rem/600 with the words "need review" in Soft Ink beside it. The
  color goes on the number only — never the phrase, never the capsule border or
  background, never `--review-bg` behind the stat. A scoped finding, not an alarm.
- **All-clear state:** when the summary loads successfully and review-needed is 0,
  the "0 need review" stat becomes a checked **"All clear in this view"** state
  (Approved color + check, text always present), with secondary copy "No current
  changes match Flagger's review-needed signals." The ledger stays visible beneath —
  all-clear describes this view's signals, never the safety of the commits.
- **State:** Fetch error renders `—` in Muted Ink; loading renders the skeleton.

### Activity Heading (lead sentence)
- The `<h1>` stays "Activity". The subtitle is the page's **lead finding**, prefixed
  by the time-aware greeting (computed once per mount, no live clock):
  - review-needed > 0: "{greeting} {n} change(s) need review in this view of {r}
    repository/ies."
  - zero: "{greeting} No current changes match Flagger's review-needed signals."
  - loading: "{greeting} Loading review summary…"
  - error: "{greeting} Review summary unavailable. AI-authored changes across
    connected repositories."
- Numeric prose is gated on a trusted summary response — never derived from `?? 0`
  fallbacks, which would fabricate an all-clear. Type stays .875rem Soft Ink: the
  content carries the weight, not the size.

### Ledger Shell + Activity Rows
- **Shell:** One rounded (20px) glass panel per table — Glass Fill + Glass Border +
  glass-ambient shadow, `overflow: hidden`, a single 12px blur. The shell owns the
  glass; everything inside is tint.
- **Toolbar:** first band inside the shell (48px): a short, accurate explainer of the
  current ordering on the left, the sort controls (Review queue / Latest first) on
  the right. The copy is **state-driven** — it describes the active sort ("Riskiest
  changes first within each day" vs "Newest changes first within each day") and must
  not overclaim: priority sorting happens within each day group.
- **Internal bands:** toolbar 48px → column head 42px → day header 40px → rows.
  Bands separate by fixed height, typography, and 1px Divider rules — never free
  whitespace. All three bands use `--ledger-band-fill`: 40% Canvas Deep in dark mode
  and 32% white in light mode, with Soft Ink labels and copy. Day headers are a real
  40px band (13px, 700) carrying the day's count as quiet evidence — "Today · 3
  changes" with the count in Soft Ink at 400 —
  with an 8px gutter + boundary rule between day groups.
- **Rows:** Contiguous Row Fill planes separated by single Divider rules (omitted on
  the final row) — no per-row radius, no gaps, so column scanning stays continuous.
- **Content:** Commit message first (Ink), abbreviated SHA in the mono code capsule,
  contributor / agent / risk metadata in Muted Ink + state chips.
- **Hover:** Row Fill Hover. **Selected:** an Aurora Blue 10% tint mixed into the row
  fill plus the standard focus outline — no stripe borders, no inset box rings.
- **Behavior:** New activity never reorders or reflows rows while the user is reading.
  Queue updates behind an explicit disclosure.

### Evidence Inspector (glass)
- **Shape:** Right-side panel, 20px radius on the inner edge, Glass Fill + Glass
  Border + glass-ambient shadow, single 12px shell blur.
- **Content:** Inner sections sit on Row Fill with a 14px radius — tint only, never a
  second blur (the Single Blur Rule). The glass is the panel shell, padding, and
  header.
- **Motion:** enters at 240ms (fade + 18px slide); exits at 160ms `--ease-in`
  (fade + 12px slide), retained in the tree until the exit finishes. The workspace
  padding is never animated.

### Buttons
- **Primary:** Aurora Blue fill, Canvas Deep text (≥7:1), 10px radius, 8px 16px
  padding. Hover lightens one ramp step; active darkens one. Focus: 2px Aurora Blue
  outline, 2px offset.
- **Ghost:** Transparent fill, Soft Ink text, Glass Border outline; hover raises fill
  to Glass Fill.

### Inputs / Selects
- **Style:** Opaque Code Surface fill, 10px radius, no border at rest; 1px Divider on
  hover; 2px Aurora Blue outline on focus. Placeholder is Muted Ink (the contrast
  floor), `opacity: 1`.

### Chips (state + filters)
- **State chips:** Review / Reviewed / Approved surface + text token pairs, pill
  radius, sentence case, always label text beside the color. No uppercase, no wide
  tracking.
- **Severity ranking:** Flagged visually outranks every other state — it alone
  carries a 1px border (Review at 40%) and 700 weight; Review needed shares the
  Review color pair at 600 without the border; Pending and Approved stay quiet.
  Base chips are 600 with a transparent border so the Flagged border never shifts
  layout.
- **Filter pills:** Compact glass — Glass Fill + Glass Border, small-chrome blur;
  selected = Aurora Blue text on its 12% accent tint.

### State Cards (loading / error / empty)
- **Style:** Rounded (14px) glass tint — Glass Fill + Glass Border; icon + text carry
  the state, color never alone.

### Login Panel (glass)
- **Style:** Centered 20px-radius glass panel with 24–32px padding — the first
  premium moment a user sees; same recipe as every other panel, nothing bespoke.

### Inline Code / SHAs
- **Style:** Code Surface capsule, 5px radius, 13px mono, 2px 6px padding,
  tabular numerals.

## 7. Do's and Don'ts

### Do:
- **Do** keep motion purposeful and quiet: feedback at 90–140ms, entrances once per
  mount, exits faster than entrances, everything token-driven and collapsed under
  `prefers-reduced-motion`.
- **Do** make every container a glass panel — and put Row Fill under anything with
  more than two lines of dense text (the Glass Panels, Legible Rows Rule).
- **Do** give blur to panel shells only: 12px large, 16px small-chrome cap, one level
  deep, clip and blur on the same element (the Single Blur Rule).
- **Do** make consequential activity identifiable within 30 seconds; the canvas and
  glass must never slow that down.
- **Do** pair every risk/review color with explicit text and, where useful, an icon.
- **Do** provide the opaque fallback: `prefers-reduced-transparency`, `forced-colors`,
  and missing `backdrop-filter` support collapse glass to Surface Strong + Divider and
  rows to solid Surface with identical layout.
- **Do** compose all three cool wallpaper fields with off-edge cores and eased
  hue-to-alpha-zero falloffs beneath a topmost 128px grain layer; keep the center
  quiet while a falloff crosses exposed shell chrome, and drift only imperceptibly
  (one transform-only layer, ≥100s cycle, frozen under reduced motion).
- **Do** keep feed position stable; queue new activity behind an explicit disclosure.
- **Do** target WCAG 2.2 AA: 4.5:1 body text everywhere, visible focus states, full
  keyboard operation, reduced-motion alternatives for every transition.

### Don't:
- **Don't** put `backdrop-filter` on individual rows, or nest blur inside a blurred
  shell — one shell-level capture per panel, tint for everything inside.
- **Don't** let text sit directly on blur: dense text always gets Row Fill beneath it.
- **Don't** break rows into separate rounded cards — the feed is one continuous
  ledger inside one glass shell; per-row gaps destroy column scanning.
- **Don't** build a Datadog- or Splunk-style maximalist observability wall. This is a
  ledger in glass, not a light show.
- **Don't** add gamification: streaks, leaderboards, adoption scores.
- **Don't** make background motion perceptible: no parallax, no repaint-driven
  animation (`background-position`), no cycles under 100s, nothing that survives
  `prefers-reduced-motion`.
- **Don't** use bounce/elastic easing, hover-lift blurred shells, re-fire entrance
  choreography on refetch/filter/pagination, or stagger more than 10 rows.
- **Don't** put grain on chips, pills, rows, buttons, or the sidebar — the canvas and
  large shells only.
- **Don't** rely on red/green alone for risk, and don't use alarmist presentation or
  claim unvalidated risk reduction.
- **Don't** auto-refresh in a way that jumps or reflows the feed mid-scan.
- **Don't** use gradient text, colored side-stripe borders, uppercase tracked
  micro-labels, or saturated fills on inactive states.
- **Don't** remove data to look premium — polish comes from material and spacing,
  never from hiding the evidence.

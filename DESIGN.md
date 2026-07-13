---
name: Flagger
description: A dark forensic ledger of AI-authored engineering activity, framed in quiet glass.
colors:
  aurora-blue: "#8da2ff"
  aurora-violet: "#b892ff"
  aurora-cyan: "#7fd8ea"
  canvas: "#0f1017"
  canvas-deep: "#0a0b10"
  surface: "#16181f"
  surface-strong: "#1d2029"
  glass-fill: "#ffffff0d"
  glass-border: "#ffffff1a"
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
  light-glass-fill: "#ffffff99"
  light-glass-border: "#1e222b14"
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
  xs: "4px"
  sm: "6px"
  md: "10px"
  lg: "16px"
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
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    padding: "12px 16px"
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

**Creative North Star: "The Ledger Under Glass"**

Flagger is a dark, dense, forensic record of AI-authored engineering activity — read
through instrument glass. The data itself (commit rows, SHAs, diffs, review states)
sits on opaque, flat surfaces and is treated like evidence: dense, aligned, never
decorated. The **chrome** around the data — the left navigation sidebar, Evidence
Inspector, dropdowns, and modals — is frosted glass: translucent, blurred, edged with a hairline
light border, catching faint aurora color from two fixed glows behind the canvas.
Glass frames the ledger; it never sits underneath it.

The atmosphere is a quiet glow, not a light show. A near-black cool canvas carries
two large, very dim, **stationary** color fields (violet upper-left, cyan lower-right).
They exist so the glass has something to refract; they are never animated and never
compete with the data. The system still explicitly rejects maximalist observability
walls, gamification, alarmist presentation, and color-only risk signals.

**Key Characteristics:**

- Opaque, flat, dense activity rows — evidence first
- Frosted-glass chrome: navigation sidebar, inspector, overlays only
- Dark-first; light theme is a functional, less atmospheric fallback
- Cool aurora accent family (blue-violet-cyan); warm color reserved for review states
- Two fixed ambient glows, never animated
- Familiar Git typography: monospace for SHAs, branches, and code only

## 2. Colors

A near-black cool foundation, one aurora accent family for action and selection, and
warm/cool state colors reserved exclusively for review status.

### Primary
- **Aurora Blue** (`#8da2ff`): The action color. Primary buttons, current selection,
  focus rings, active filters, links. Used on ≤10% of any screen; its scarcity keeps
  the ledger quiet.

### Secondary
- **Aurora Violet** (`#b892ff`): The upper-left ambient glow hue and occasional
  large-surface tint (never body text). Exists mostly *behind* the glass.
- **Aurora Cyan** (`#7fd8ea`): The lower-right ambient glow hue; also small data
  highlights (sparklines, agent attribution marks) where Aurora Blue is already in use.

### Tertiary (review states — the only non-aurora chroma)
- **Review** (`#f5a08c` on `#3a231e`): Needs-review. Deliberately warm so it can never
  be mistaken for the cool aurora family. Always paired with the word "Review" and/or
  an icon.
- **Reviewed** (`#7fc4dc` on `#17323c`): Reviewed-not-approved.
- **Approved** (`#83d6a5` on `#1a3527`): Approved.

### Neutral
- **Canvas** (`#0f1017`) and **Canvas Deep** (`#0a0b10`): The workspace. Canvas Deep
  sits behind the ambient glows at the page root.
- **Surface** (`#16181f`) / **Surface Strong** (`#1d2029`): Opaque planes for feed rows
  and any container holding body text.
- **Glass Fill** (`#ffffff0d`, i.e. white at 5%) + **Glass Border** (`#ffffff1a`, white
  at 10%): the only two ingredients of a glass panel, always with `backdrop-filter:
  blur(16px) saturate(1.4)`.
- **Ink** (`#edeff5`), **Soft Ink** (`#b8bfcc`), **Muted Ink** (`#8b93a3`): text
  hierarchy. Muted Ink is the floor — nothing dimmer may carry information.
- **Divider** (`#262a35`), **Code Surface** (`#1c1f28`).
- **Light theme fallback** (`light-*` tokens): cool near-white canvas, white glass at
  60% with a dark hairline border, darkened accent (`#4f66d8`) and state colors so
  every text role keeps ≥4.5:1 on light surfaces.

**The Chrome-Only Glass Rule.** Glass (translucency + blur) is permitted on exactly
three things: the navigation sidebar, the Evidence Inspector panel, and transient
overlays (dropdowns, dialogs, toasts). Feed rows, tables, and any surface carrying
more than two lines of text are opaque. No exceptions.

**The Quiet Glow Rule.** Exactly two ambient glows, fixed position, ≤12% opacity,
never animated, never more saturated than the aurora tokens. If a screenshot of the
canvas alone looks like a gradient poster, the glows are too loud.

**The Redundancy Rule.** Risk and review status always pair color with explicit text
and, where useful, a distinct icon. Color is never the only signal.

## 3. Typography

**Display Font:** system-ui (with Segoe UI and Roboto fallbacks)
**Body Font:** system-ui (with Segoe UI and Roboto fallbacks)
**Label/Mono Font:** ui-monospace (with Consolas fallback)

**Character:** One system sans keeps the product native and unobtrusive against the
atmospheric backdrop; the type does the ledger's work while the glass does the mood.
Monospace is reserved for Git identifiers and machine-readable evidence.

### Hierarchy
- **Display** (500, 56px, 1.18): Rare page-level headings only; 36px on compact screens.
- **Title** (500, 24px, 1.18): Section headings; 20px on compact screens.
- **Body** (400, 16px, 1.5): Commit messages and explanatory content. Prose capped at
  65–75ch; dense table/feed content may run wider.
- **Label** (600, 13px mono, 1.35): SHAs, branches, filenames, compact technical
  identifiers, with `font-variant-numeric: tabular-nums`.

**The Evidence Type Rule.** Monospace for SHAs, branches, filenames, and code only.
Never as general atmosphere.

**The Legible Glass Rule.** Text on glass must be Ink or Soft Ink and must pass 4.5:1
against the *darkest plausible* content scrolling beneath the panel. If a text role
fails, the panel gains an opaque scrim — the text never gets lighter.

## 4. Elevation

Depth comes from three layers, back to front: the glowing canvas, opaque data
surfaces, and glass chrome. Glass panels carry a soft ambient shadow
(`0 12px 32px rgba(0,0,0,0.35)`) plus their hairline light border — that combination
is what reads as "glass", not the blur alone. Opaque surfaces are flat: separated by
Divider rules and tone, no shadows at rest.

### Shadow Vocabulary
- **glass-ambient** (`box-shadow: 0 12px 32px rgba(0,0,0,0.35)`): glass chrome panels.
- **overlay** (`box-shadow: 0 20px 48px rgba(0,0,0,0.5)`): dropdowns, dialogs, toasts.

**The Blur Budget Rule.** `backdrop-filter` blur is capped at 16px and at most three
glass surfaces may be visible at once. Under `prefers-reduced-transparency` or
`forced-colors`, every glass token resolves to opaque Surface Strong with a Divider
border — the layout must not change.

**The Flat Evidence Rule.** Feed rows remain flat at rest. Row hover is a tonal shift
(Surface → Surface Strong), never elevation.

## 5. Components

### Topbar (glass)
- **Style:** Full-width frosted bar — Glass Fill, `blur(16px) saturate(1.4)`,
  bottom edge is Glass Border (no drop shadow; it sits on the canvas).
- **Nav:** Soft Ink links; active view in Ink with a 2px Aurora Blue underline.
- **Behavior:** Sticky; content scrolling beneath it is what makes it read as glass.

### Summary Bar (glass)
- **Shape:** Softly rounded (16px), Glass Fill + Glass Border + glass-ambient shadow.
- **Content:** AI-authored %, review-needed count, total commits — plain Ink figures
  with Soft Ink labels. No gradient tiles, no per-stat cards inside the glass.
- **State:** Fetch error renders `—` in Muted Ink; loading renders the skeleton.

### Activity Rows (opaque)
- **Shape:** Square list geometry, no radius, Surface background.
- **Separation:** Single Divider bottom rule, omitted on the final row.
- **Content:** Commit message first (Ink), abbreviated SHA in the mono code capsule,
  contributor / agent / risk metadata beneath in Muted Ink + state chips.
- **Hover / Selected:** Surface Strong; selected row adds a 2px Aurora Blue left
  inset on the focus ring only (never a colored stripe border).
- **Behavior:** New activity never reorders or reflows rows while the user is reading.
  Queue updates behind an explicit disclosure.

### Evidence Inspector (glass)
- **Shape:** Right-side panel, 16px radius on the inner edge, Glass Fill + Glass
  Border + glass-ambient shadow, `blur(16px)`.
- **Content:** Sits on sections of opaque Surface for diff stats and risk-signal
  lists — evidence inside the inspector is on opaque ground per the Legible Glass
  Rule; the glass is the panel shell, padding, and header.

### Buttons
- **Primary:** Aurora Blue fill, Canvas Deep text (≥7:1), 6px radius, 8px 16px padding.
  Hover lightens one ramp step; active darkens one. Focus: 2px Aurora Blue outline,
  2px offset.
- **Ghost:** Transparent fill, Soft Ink text, Glass Border outline; hover raises fill
  to Glass Fill.

### Inputs / Selects
- **Style:** Opaque Code Surface fill, 6px radius, no border at rest; 1px Divider on
  hover; 2px Aurora Blue outline on focus. Placeholder is Muted Ink (the contrast
  floor), `opacity: 1`.

### Chips (state + filters)
- **State chips:** Review / Reviewed / Approved surface + text token pairs, pill
  radius, always label text beside the color.
- **Filter chips:** Ghost treatment; selected = Aurora Blue text on its `-surface`
  tint at 12% with Glass Border.

### Inline Code / SHAs
- **Style:** Code Surface capsule, 4px radius, 13px mono, 2px 6px padding,
  tabular numerals.

## 6. Do's and Don'ts

### Do:
- **Do** keep glass on the chrome only: topbar, summary bar, Evidence Inspector, and
  transient overlays. Everything carrying dense text sits on opaque Surface.
- **Do** make consequential activity identifiable within 30 seconds; the glow and
  glass must never slow that down.
- **Do** pair every risk/review color with explicit text and, where useful, an icon.
- **Do** provide the opaque fallback: `prefers-reduced-transparency` and
  `forced-colors` collapse glass to Surface Strong + Divider with identical layout.
- **Do** keep both ambient glows fixed, dim (≤12% opacity), and unanimated.
- **Do** keep feed position stable; queue new activity behind an explicit disclosure.
- **Do** target WCAG 2.2 AA: 4.5:1 body text everywhere, visible focus states, full
  keyboard operation, reduced-motion alternatives for every transition.

### Don't:
- **Don't** put `backdrop-filter` under feed rows, tables, or paragraphs — if glass
  ever sits beneath more than two lines of text, it's wrong (the Chrome-Only Glass Rule).
- **Don't** build a Datadog- or Splunk-style maximalist observability wall. This is a
  ledger, not a monitoring wall — the glass is a frame, not a light show.
- **Don't** add gamification: streaks, leaderboards, adoption scores.
- **Don't** animate the ambient glows, add parallax, or drift the background.
- **Don't** rely on red/green alone for risk, and don't use alarmist presentation or
  claim unvalidated risk reduction.
- **Don't** auto-refresh in a way that jumps or reflows the feed mid-scan.
- **Don't** use gradient text, colored side-stripe borders, or saturated fills on
  inactive states.
- **Don't** exceed the Blur Budget: 16px blur max, three visible glass surfaces max.
- **Don't** turn activity rows into rounded, shadowed glass cards; the feed is a
  continuous opaque ledger.

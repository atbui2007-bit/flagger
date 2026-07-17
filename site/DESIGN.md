---
name: Flagger Landing
description: The Ledger at Dusk — an editorial serif landing page set in the dashboard's dark aurora glass.
colors:
  canvas: "#0f1017"
  canvas-deep: "#0a0b10"
  surface: "#16181f"
  surface-strong: "#1d2029"
  surface-muted: "#1c1f28"
  ink: "#edeff5"
  soft-ink: "#b8bfcc"
  muted-ink: "#8b93a3"
  divider: "#262a35"
  divider-soft: "#1f232d"
  aurora-blue: "#8da2ff"
  aurora-blue-bright: "#b0bdff"
  aurora-blue-deep: "#748ade"
  on-accent: "#0a0b10"
  aurora-violet: "#b892ff"
  aurora-cyan: "#7fd8ea"
  hero-indigo: "#1a2040"
  hero-core: "#2c3766"
  hero-glow: "#42528f"
  glass-fill: "#ffffff14"
  chrome-glass: "#0a0b1070"
  glass-border: "#ffffff24"
  review: "#f5a08c"
  review-surface: "#3a231e"
  approved: "#83d6a5"
  approved-surface: "#1a3527"
  reviewed: "#7fc4dc"
  reviewed-surface: "#17323c"
typography:
  display:
    fontFamily: "Playfair Display, Georgia, serif"
    fontSize: "clamp(36px, 6vw, 48px)"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "normal"
  headline:
    fontFamily: "Playfair Display, Georgia, serif"
    fontSize: "36px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "normal"
  title:
    fontFamily: "Inter, SF Pro Text, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "-0.36px"
  body:
    fontFamily: "Inter, SF Pro Text, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "-0.32px"
  label:
    fontFamily: "Inter, SF Pro Text, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.24px"
rounded:
  md: "7px"
  screen: "16px"
  card: "22px"
  frame: "30px"
  pill: "50px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
  2xl: "80px"
  3xl: "100px"
components:
  button-primary:
    backgroundColor: "{colors.aurora-blue}"
    textColor: "{colors.on-accent}"
    rounded: "{rounded.pill}"
    padding: "14px 24px"
  button-primary-hover:
    backgroundColor: "{colors.aurora-blue-bright}"
  button-primary-active:
    backgroundColor: "{colors.aurora-blue-deep}"
  button-ghost:
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "12px 22px"
  nav-capsule:
    backgroundColor: "{colors.chrome-glass}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "8px 16px"
  glass-card:
    backgroundColor: "{colors.chrome-glass}"
    textColor: "{colors.ink}"
    rounded: "{rounded.frame}"
    padding: "24px"
  item-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.soft-ink}"
    rounded: "{rounded.card}"
    padding: "20px"
  ledger-row:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "20px"
  badge:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.soft-ink}"
    rounded: "{rounded.pill}"
    padding: "4px 10px"
  badge-active:
    backgroundColor: "#8da2ff24"
    textColor: "{colors.aurora-blue}"
  badge-approved:
    backgroundColor: "{colors.approved-surface}"
    textColor: "{colors.approved}"
  badge-needs-review:
    backgroundColor: "{colors.review-surface}"
    textColor: "{colors.review}"
  badge-reviewed:
    backgroundColor: "{colors.reviewed-surface}"
    textColor: "{colors.reviewed}"
---

# Design System: Flagger Landing

## 1. Overview

**Creative North Star: "The Ledger at Dusk"**

The landing page is the magazine cover for the dashboard behind it. It keeps the
editorial architecture of a premium indie print spread — a confident retro serif
for every display headline, a floating capsule nav, one atmospheric full-bleed
hero, single-column reading sections — but sets all of it in the Flagger
dashboard's own material: a near-black night canvas washed with three faint
aurora fields (blue, violet, cyan), grain-debanded, with dark frosted-glass
panels for the page chrome. The hero is a PS3-XMB-style dusk: a vast,
nearly empty deep-indigo field with a single blurred silk ribbon drifting
through its center band and a handful of twinkling sparkles, melting seamlessly
into the page canvas — with the product ledger overlapping out of the scene
like the first page of the record.

The system explicitly rejects the Datadog/Splunk observability-wall aesthetic,
gamification of any kind, alarmist presentation, and color-only status signals.
It is one atmospheric moment followed by quiet, legible evidence — never a
monitoring dashboard cosplaying as a website.

**Key Characteristics:**
- Dark-first and light-less: one committed night theme, `color-scheme: dark`.
- Serif display voice (Playfair Display at 36–48px only) over Inter body — magazine, not dashboard.
- Aurora blue (#8da2ff) is the single action accent; violet and cyan exist only as atmosphere and never as UI chrome.
- Glass belongs to shells (nav, hero card, mockup frame, closing CTA); rows and item cards are solid, crisp surfaces.
- Every pill, every generous radius from the editorial system survives — softness carries the premium feel, not decoration.

## 2. Colors

A night palette: layered near-black neutrals, one aurora-blue voice, two
supporting atmosphere hues, and three evidence-state colors that only ever
appear with a text label.

### Primary
- **Aurora Blue** (#8da2ff): the only action color. Primary CTA fill, live/active badges, focus rings, text selection. Hover brightens to **Aurora Bright** (#b0bdff), press deepens to **Aurora Deep** (#748ade); text on any aurora fill is **On-Accent** (#0a0b10), never white.

### Secondary
- **Aurora Violet** (#b892ff) and **Aurora Cyan** (#7fd8ea): atmosphere only — the canvas wash fields, the hero gradient's mid-stops, and the brand-mark gradient (blue→violet). Prohibited as button fills, link colors, or borders.

### Tertiary
- **Approved Green** (#83d6a5 on #1a3527), **Needs-Review Coral** (#f5a08c on #3a231e), **Reviewed Cyan** (#7fc4dc on #17323c): evidence-state badge pairs inside the product mockup. Each is always paired with its text label — these are claims, not decorations.

### Neutral
- **Night Canvas** (#0f1017): page background, washed with the aurora fields and grain. **Canvas Deep** (#0a0b10): silhouette fill and hero-gradient terminus.
- **Ledger Surface** (#16181f): solid item cards and the product screen. **Surface Strong** (#1d2029): glass fallback and row hover. **Surface Muted** (#1c1f28): neutral badge fill.
- **Ink** (#edeff5): headings, hero lede, nav links. **Soft Ink** (#b8bfcc): body prose. **Muted Ink** (#8b93a3): metadata and captions only — never running body text.
- **Divider** (#262a35) / **Divider Soft** (#1f232d): hairlines inside solid surfaces. **Glass Border** (rgba(255,255,255,.14)): the 1px light edge on every glass panel and item card.
- **Chrome Glass** (rgba(10,11,16,.44) + blur(12px) saturate(1.35)): the dark-tinted glass for page chrome. **Panel Glass** (rgba(255,255,255,.08)): the lighter glass reserved for the mockup frame sitting over the dark base of the hero.

**The Dark Glass Rule.** Page chrome that can sit over the hero's bright
gradient stops (nav, hero copy card) uses dark-tinted Chrome Glass, never
white-tinted glass — white glass over the bright aurora top composites into a
bright surface and destroys text contrast. This rule exists because that exact
failure shipped once.

**The Labeled State Rule.** Green, coral, and cyan never appear without their
words ("Approved", "Needs review", "Reviewed"). Color-only risk signals are
prohibited, mirroring the product.

## 3. Typography

**Display Font:** Playfair Display 400 (Perfectly Nineties aspirationally; Georgia fallback)
**Body Font:** Inter 400/500/600 (SF Pro Text, system-ui fallback)

**Character:** A confident retro serif doing all the talking at display sizes,
over a tight, quiet Inter running text — the editorial contrast axis is the
brand's voice. The serif never appears below 36px; Inter never exceeds 600.

### Hierarchy
- **Display** (400, clamp(36px, 6vw, 48px), line-height 1.0): the hero H1 only.
- **Headline** (400, 36px, line-height 1.0): section H2s ("Certain or suspected. Never blurred.").
- **Title** (600, 16–18px, Inter): card headings, ledger row titles, the brand wordmark.
- **Body** (400, 16px, line-height 1.45, letter-spacing -0.32px, Inter): prose, capped at the 720px editorial column (~68ch). Line-height is raised from the light-theme 1.35 because light text on dark reads lighter.
- **Label** (500, 12–14px, Inter): badges, nav links, metadata, captions.

**The Serif Ceiling Rule.** Playfair Display exists at 36px and above, weight
400, sentence case, and nowhere else. In buttons, badges, navs, or body copy it
is forbidden.

## 4. Elevation

Depth is layered material, not drop shadows: the fixed aurora canvas sits at
the very back; solid ledger surfaces float on it with 1px light borders; glass
panels form the topmost chrome layer with an inset light edge and a deep soft
ambient shadow (`inset 0 1px 0 rgba(255,255,255,.10), 0 18px 48px
rgba(0,0,0,.32), 0 4px 14px rgba(0,0,0,.22)`). The old light-theme glow rings
are gone; the light hairline + dark ambience pair is the entire depth language.

### Shadow Vocabulary
- **Glass ambient** (`--shadow-glass`): every backdrop-blurred panel — nav capsule, hero copy card, mockup frame, closing CTA.
- **Button lift** (`inset 0 1px 0 rgba(255,255,255,.34), 0 0 0 1px rgba(255,255,255,.08), 0 8px 22px rgba(0,0,0,.24)`): the primary pill only.

**The Shells-Only Rule.** `backdrop-filter` belongs to panel shells exclusively
— never to ledger rows, item cards, badges, or anything nested inside another
glass panel. Under `prefers-reduced-transparency` or missing backdrop-filter
support, all glass collapses to solid #1d2029 with #262a35 borders, layout
unchanged.

## 5. Components

### Buttons
- **Shape:** full pill (50px radius), min-height 50px — every button, no exceptions.
- **Primary:** Aurora Blue fill, On-Accent (#0a0b10) text, Inter 600 14px, padding 14px 24px, button-lift shadow. Hover → #b0bdff, active → #748ade + 1px translate.
- **Ghost:** transparent, 1.5px rgba(237,239,245,.6) border, Ink text, Inter 500. Hover fills with Chrome Glass. Outlined only — never filled.
- **Focus:** 2px Aurora Blue outline, 3px offset, on all interactive elements.

### Chips / Badges
- **Style:** full pill, Inter 500 12px, padding 4px 10px, min-height 26px.
- **States:** neutral (Surface Muted + Soft Ink), active/live (Aurora Blue on 14% aurora tint), and the three labeled evidence states (see Colors §Tertiary).

### Cards / Containers
- **Glass chrome** (nav, hero copy, closing CTA): Chrome Glass fill, 1px Glass Border, glass-ambient shadow, backdrop blur; 22px radius for the nav capsule, 30px for cards.
- **Item cards** (steps, principles): solid Ledger Surface, 1px Glass Border, 22px radius, 20px padding. No blur, no nesting.
- **Ledger rows** (inside the mockup): solid rgba(22,24,31,.84) rising to rgba(29,32,41,.92) on hover over 140ms; 22px radius; time / title+meta / badge grid.

### Navigation
- **Floating capsule**, max-width 760px, centered with top margin — never a full-width bar. Brand mark (40px circle, blue→violet gradient, ↗ glyph in On-Accent) + wordmark left; Inter 500 14px Ink links right, hover opacity .6. Mobile collapses to brand + "Sign in".

### The XMB Hero (signature)
A PS3-XMB-inspired ethereal field, built as three layers inside an
absolutely-positioned clipped `.hero-bg` so content can overlap out of it:

- **Field:** full-bleed 180° gradient (#0a0b10 → #1a2040 → #2c3766 → #42528f
  glow band → #1a2040 → #0f1017) plus one soft radial aurora glow at ~52%
  height — dark quiet edges, saturated center, no horizon, no scenery.
- **Ribbon:** one 140%-wide SVG silk band at ~42–58% of hero height — three
  stacked blurred (10px) bezier layers in Aurora Blue .14 / Violet .10 /
  Cyan .07, `mix-blend-mode: screen`, drifting transform-only at 70s/90s/110s
  alternating cycles ("gently alive," never eye-pulling).
- **Sparkles:** ~14 screen-blended 2–5px dots, denser in the ribbon band, top
  ~35% kept nearly empty; staggered 3–6s opacity twinkles from a visible base
  state (they never depend on animation to appear). An 18% bottom fade inside
  `.hero-bg` soft-lands everything into the canvas — no clip edge.

The glass device mockup (real ledger rows, real state badges) hangs -88px past
the hero bottom into the canvas. Negative space is the design: ~60% of the
hero reads as pure gradient. Under reduced motion the whole scene freezes at
its visible base state. This is the page's only atmospheric moment; everything
below is typography on the quiet aurora wash.

### The Aurora Canvas (signature)
`background-attachment: fixed` layer on the main canvas: three radial fields —
aurora blue at 24% alpha (top-left), violet 24% (right), cyan 20% (bottom) —
over Night Canvas, plus the 128px SVG grain tile at 3% opacity for debanding.
Cores pushed off-edge, center kept quiet so prose stays legible.

## 6. Do's and Don'ts

### Do:
- **Do** set every display heading in Playfair Display 400 at 36–48px, line-height 1.0 — the serif is the voice; diluting it to smaller sizes kills the register.
- **Do** use Aurora Blue (#8da2ff) for every action and only actions; text on it is always #0a0b10.
- **Do** keep every button and badge a full 50px pill and every card at 22–30px radius.
- **Do** pair every state color with its text label — "Needs review" in coral, never a bare coral dot.
- **Do** keep body prose Soft Ink (#b8bfcc) at 16px/1.45 in the 720px column; verified ≥9.5:1 on all shipped surfaces.
- **Do** collapse glass to solid #1d2029 surfaces (same layout) under `prefers-reduced-transparency`, `forced-colors`, and missing `backdrop-filter`.
- **Do** honor `prefers-reduced-motion`: transitions drop to instant; nothing on the page requires motion to be visible.

### Don't:
- **Don't** put white-tinted glass over the hero's bright gradient stops — the Dark Glass Rule exists because this shipped as an illegibility bug once.
- **Don't** blur rows, item cards, or anything nested inside a glass panel — shells only.
- **Don't** use Aurora Violet or Cyan as UI chrome (buttons, links, borders); they are atmosphere and brand-mark only.
- **Don't** build a Datadog/Splunk-style observability wall, add gamification (streaks, leaderboards, adoption scores), or use alarmist presentation — PRODUCT.md's anti-references apply to the marketing surface too.
- **Don't** rely on color alone for any status signal.
- **Don't** reintroduce a light theme, the old #007aff accent, or the #f7f7f7 glow rings — the Portal light system this page previously used is fully superseded.
- **Don't** use Muted Ink (#8b93a3) for running body text; it is metadata-only.
- **Don't** wrap editorial sections in large panels — prose sits directly on the aurora canvas; burying the wash under section-wide cards flattens the page to black slabs (this also shipped once).

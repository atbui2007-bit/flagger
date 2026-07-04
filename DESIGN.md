---
name: Flagger
description: A quiet, auditable ledger of AI-authored engineering activity.
colors:
  action-ink: "#242329"
  canvas: "#f4f4f2"
  surface: "#fafaf8"
  surface-strong: "#ffffff"
  ink: "#22262d"
  soft-ink: "#515862"
  muted-ink: "#666d76"
  divider: "#dcdeda"
  code-surface: "#eeeeeb"
  review: "#863128"
  review-surface: "#f8e9e6"
  reviewed: "#315579"
  reviewed-surface: "#e9eef5"
  approved: "#215f40"
  approved-surface: "#e7f2eb"
  dark-canvas: "#16171d"
  dark-ink: "#f3f4f6"
  dark-muted-ink: "#9ca3af"
  dark-divider: "#2e303a"
  dark-code-surface: "#1f2028"
  dark-action-ink: "#d7d9de"
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
    fontSize: "18px"
    fontWeight: 400
    lineHeight: "1.45"
    letterSpacing: "0.18px"
  label:
    fontFamily: "ui-monospace, Consolas, monospace"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: "1.35"
rounded:
  xs: "4px"
  sm: "5px"
  md: "6px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "32px"
components:
  activity-row:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    padding: "12px 16px"
  commit-sha:
    textColor: "{colors.ink}"
    typography: "{typography.label}"
---

# Design System: Flagger

## Overview

**Creative North Star: "The Commit Ledger"**

Flagger is quiet, dense, and forensic. Its light-first Activity workspace resembles a dependable engineering record: compact enough to scan quickly, familiar enough to trust immediately, and restrained enough that meaningful status changes retain their force.

Structure comes from typography, alignment, and thin dividers rather than decorative containers. Information remains stable while a user scans it; motion is reserved for state feedback and must never cause the activity feed to jump. The system explicitly rejects maximalist observability dashboards, gamification, and ornamental AI-product styling.

**Key Characteristics:**

- Compact, evidence-first activity rows
- Familiar Git typography and terminology
- Achromatic surfaces with one scarce action tone
- Stable layouts and restrained state feedback
- Flat, structural separation rather than decorative depth

## Colors

The foundation is deliberately achromatic. A warm-gray Canvas and dark-slate ink carry hierarchy; restrained semantic colors are reserved exclusively for review state.

### Primary

- **Action Ink:** Reserved for current selection, focus, agent attribution, and primary actions. It is a semantic placeholder for a future accent, not a permanent brand hue.

### Neutral

- **Canvas:** The default warm-gray workspace surface.
- **Surface and Surface Strong:** Quiet raised planes for the ledger and Evidence inspector without decorative shadow.
- **Ink:** Primary headings, commit messages, and high-priority evidence.
- **Muted Ink:** Supporting metadata that remains readable against Canvas.
- **Divider:** Row boundaries and structural separators.
- **Code Surface:** Inline code and SHA treatments that need tonal separation.
- **Dark Canvas, Dark Ink, Dark Muted Ink, Dark Divider, and Dark Code Surface:** Equivalent roles when the operating system requests dark mode.
- **Dark Action Ink:** The dark-mode equivalent used for selection, focus, attribution, and primary actions.

**The Monochrome Foundation Rule.** Use only achromatic colors until a colorway is explicitly selected. Preserve the Action Ink role so a future accent remains a token change rather than a component rewrite.

**The Redundancy Rule.** Risk and status always use readable text and, when useful, an icon in addition to color.

**The State-Only Color Rule.** Review, Reviewed, and Approved are the only chromatic roles. Every state pairs color with text and a distinct shape.

## Typography

**Display Font:** system-ui (with Segoe UI and Roboto fallbacks)  
**Body Font:** system-ui (with Segoe UI and Roboto fallbacks)  
**Label/Mono Font:** ui-monospace (with Consolas fallback)

**Character:** A single system sans keeps the product native and unobtrusive. Monospace is reserved for Git identifiers and machine-readable evidence, never used as general atmosphere.

### Hierarchy

- **Display** (500, 56px, 1.18): Reserved for rare page-level headings; reduces to 36px on compact screens.
- **Title** (500, 24px, 1.18): Section headings; reduces to 20px on compact screens.
- **Body** (400, 18px, 1.45): Commit messages and explanatory content; reduces to 16px below 1024px. Prose is capped at 65–75 characters.
- **Label** (600, 15px, 1.35): SHAs and compact technical identifiers.

**The Evidence Type Rule.** Use monospace for SHAs, branches, filenames, and code only. Everything else uses the system sans.

## Elevation

The system is flat and structural. Depth is conveyed through surface tone, borders, and hierarchy at rest. Shadows are not part of the current rendered dashboard and must not be introduced as ambient decoration.

**The Flat Ledger Rule.** Rows remain flat at rest. Interactive elevation may appear only as brief state feedback and never combines a wide soft shadow with a decorative border.

## Components

### Activity Rows

Compact and evidentiary: each row presents the commit message first, its abbreviated SHA in semibold monospace, and contributor, agent, and risk metadata beneath it.

- **Shape:** Square list geometry with no card radius.
- **Background:** Canvas, with Dark Canvas under the system dark preference.
- **Separation:** A single Divider-colored bottom rule, omitted on the final row.
- **Internal Padding:** 12px vertically within a 16px feed inset.
- **Behavior:** New activity must not reorder or reflow rows while the user is scanning. Queue updates behind an explicit disclosure.

### Inline Code and Identifiers

- **Shape:** Gently curved corners (4px).
- **Background:** Code Surface.
- **Typography:** Compact monospace (15px, 1.35 line height).
- **Padding:** 4px vertically and 8px horizontally when rendered as a code capsule.

### Containers

- **Corner Style:** Square by default; radii are reserved for small controls and code treatments.
- **Background:** Canvas or Dark Canvas.
- **Shadow Strategy:** None at rest.
- **Border:** Divider-colored structural rules.
- **Width:** The current shell caps at 1126px and remains fluid below that width.

## Do's and Don'ts

### Do:

- **Do** make potentially consequential activity identifiable within 30 seconds of dashboard load.
- **Do** preserve visible repository, contributor, commit, diff, and review context.
- **Do** use familiar Git conventions, including abbreviated SHAs in monospace.
- **Do** keep status labels explicit and pair color with text or icons.
- **Do** keep feed position stable and let users reveal queued updates deliberately.
- **Do** target WCAG 2.2 AA with visible focus states and reduced-motion behavior.

### Don't:

- **Don't** use Datadog- or Splunk-style maximalist observability aesthetics. This is a ledger, not a monitoring wall.
- **Don't** introduce gamification such as streaks, leaderboards, or adoption scores that can be gamed.
- **Don't** make unsupported claims about reduced risk or present unvalidated risk scoring as fact.
- **Don't** rely on red and green as the only risk signal.
- **Don't** auto-refresh in a way that causes the feed to jump or reflow while someone is scanning it.
- **Don't** introduce chromatic accents before a colorway is explicitly selected; also prohibit gradient text, glassmorphism, and saturated inactive states.
- **Don't** turn each activity item into a rounded, shadowed card; the feed is a continuous ledger.

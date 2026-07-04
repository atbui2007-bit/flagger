# Product

## Register

product

## Users

The primary users are tech leads and staff engineers who need a cross-repository, cross-contributor view of AI-authored activity. They are responsible for engineering oversight and may hold budget authority for a paid product.

The secondary users are individual developers reviewing their own agent activity. They need to understand what an agent changed during an extended run and whether any work needs human review. This view uses the same underlying activity feed as the lead experience, scoped with a contributor filter.

## Product Purpose

Flagger is an auditable ledger of AI-authored engineering activity. It helps a technical lead identify a potentially risky change within 30 seconds of loading the dashboard while preserving the repository, contributor, commit, and review context needed to investigate it.

Its secondary purpose is to make AI adoption visible through measures such as the percentage of commits attributed to agents and changes in that percentage over time. The product must not claim that it reduces escaped risk until sufficient baseline and outcome data exist, and it must communicate the limits of any unvalidated risk scoring.

## Brand Personality

Legible, trustworthy, and auditable. The interface should have Linear's information density without decorative clutter, Vercel's quiet confidence and restrained use of alarm states, and GitHub's familiarity with commits, branches, SHAs, diffs, and blame-style audit trails.

## Anti-references

Avoid Datadog- or Splunk-style maximalist observability aesthetics. This is a ledger, not a monitoring wall. Avoid gamification such as streaks, leaderboards, and adoption scores that could turn AI usage into a metric to game. Avoid alarmist presentation, unsupported claims about risk reduction, color-only risk signals, and auto-refresh behavior that causes the feed to jump or reflow while a user is scanning it.

## Design Principles

1. Optimize for detection at a glance: make consequential activity identifiable within 30 seconds without hiding the evidence behind it.
2. Preserve the audit trail: every summary should lead naturally to the contributor, repository, commit, diff, and review context that supports it.
3. Use native engineering conventions: favor familiar Git and code-review language and affordances over invented metaphors.
4. Communicate uncertainty honestly: distinguish observed facts, attribution confidence, and unvalidated risk signals without overclaiming.
5. Build the lead view as the superset: derive focused individual views through filtering rather than creating a separate product model.

## Accessibility & Inclusion

Target WCAG 2.2 AA. Support reduced-motion preferences and full keyboard operation with visible focus states. Never rely on red and green alone: pair every risk or status color with clear text and, where useful, a distinct icon. Keep feed position stable during updates so users do not lose their place, and announce new activity without forcing a reflow.

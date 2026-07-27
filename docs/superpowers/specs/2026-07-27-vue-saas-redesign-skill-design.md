# Vue SaaS Redesign Skill — Design

**Date:** 2026-07-27
**Status:** Approved, pending implementation plan

## Purpose

Build a repo-scoped skill that redesigns this application's UI shell into a modern SaaS-style
interface: a collapsible vertical navigation sidebar replacing the top nav bar, a design-token
layer enforcing consistent spacing, and a crisp, dense visual treatment.

The skill is specific to this codebase. It names real files and encodes concrete values rather
than teaching a general method.

## Why now

The current styling is less consistent than `CLAUDE.md`'s design system implies. An audit found:

| Signal | Current state |
| --- | --- |
| CSS custom properties | none — every value hardcoded |
| Unique color literals | 51, across 18 files (483 total occurrences) |
| Distinct `rem` spacing values | 26, including `0.313`, `0.688`, `0.813`, `0.938`, `0.95`, `1.1` |
| Global styles | ~320 unscoped lines, all inside `App.vue` |

"Consistent spacing" therefore requires introducing a token layer that does not exist yet, and
moving navigation to a sidebar breaks two dropdowns that are positioned for a top bar.

## Decisions

| Question | Decision |
| --- | --- |
| Skill scope | Specific to this app, committed at `.claude/skills/` |
| Blast radius | Shell plus token layer; view-scoped styles inherit and are not swept |
| Sidebar behavior | Collapsible, 240px expanded to 64px icon rail, state persisted |
| Visual direction | Crisp and dense — hairline borders, no card shadows, small radius |
| Skill structure | `SKILL.md` procedure plus `reference/` assets |
| Delivery | Two phases — build the skill, then invoke it to perform the redesign |

Density won over a softer, more elevated treatment because this app's primary screens are wide
data tables — 250 orders, 32 inventory items, 14 restock candidates. Generous padding would cost
roughly a third of the visible rows.

## Delivery in two phases

**Phase 1** builds `.claude/skills/vue-saas-redesign/` and commits it. No application file changes.

**Phase 2** invokes that skill to perform the redesign on this codebase, following its own
procedure and verification steps.

Phase 1 is done when the skill exists and its assets are complete and self-consistent. Phase 2 is
done when every verification item below passes. Keeping them separate means the skill gets
exercised exactly as a future reader would run it, which is the best test that it is actually
followable.

## Artifact layout

```
.claude/skills/vue-saas-redesign/
├── SKILL.md                  ~130 lines: trigger, procedure, verification, non-goals
├── reference/tokens.css      the token layer, copied verbatim into the app
└── reference/nav-icons.md    7 nav icon SVG paths
```

`tokens.css` ships as a real file rather than prose because transcribing ~40 custom properties
by hand silently drifts. Same reasoning for the SVG paths.

`SKILL.md` frontmatter must state the trigger conditions, so the skill is discoverable from
phrasings like "modernize the UI", "replace the top nav", or "add a sidebar" — not only from its
exact name.

## Token layer

Lives at `client/src/styles/tokens.css`, imported in `client/src/main.js` before the app mounts.
CSS custom properties pierce Vue's `scoped` attribute, so existing view styles can consume the
tokens without being rewritten — this is what makes the "views inherit" blast radius viable.

Required token groups and values:

- **Spacing** — 6 steps: `4px, 8px, 12px, 16px, 24px, 32px`. Replaces the current 26 ad-hoc values.
- **Radius** — 2 steps: `4px` (controls, badges) and `6px` (cards, panels). Nothing larger; large
  radii read as soft, which is the direction that was rejected.
- **Border** — hairline `1px` in a single border color. Borders, not shadows, do the separating.
- **Shadow** — exactly one token, reserved for overlays and dropdowns. Cards must not have shadows.
- **Color** — anchored to the palette `CLAUDE.md` already documents rather than invented fresh, so
  the diff stays a consolidation rather than a re-skin: ink `#0f172a`, muted `#64748b`, border
  `#e2e8f0`, canvas `#f8fafc`, surface `#ffffff`. Plus the four existing status colors
  (green/blue/amber/red as already used by `.badge` variants), and a dark ramp for the sidebar
  surface derived from ink. Any of the other 46 literals found in the audit that do not map onto
  this set are consolidated into it, not preserved.
- **Type** — 5 steps covering page title, card title, body, small, and uppercase eyebrow labels.
- **Layout** — `--sidebar-w: 240px`, `--sidebar-w-collapsed: 64px`.

## Sidebar

New `client/src/components/AppSidebar.vue`, containing:

- brand block at top
- 7 `router-link` entries, each pairing a `NavIcon` with its `t('nav.*')` label
- footer holding the existing `LanguageSwitcher` and `ProfileMenu`
- a collapse toggle

**Icons.** New `client/src/components/icons/NavIcon.vue` takes a `name` prop and renders inline
1.5px-stroke SVG using `currentColor`, so icons inherit nav link color automatically. Seven icons
are needed, one per route. No dependency, and no emoji — `CLAUDE.md` forbids them.

**Collapse state.** New `client/src/composables/useSidebar.js` holds a module-level `ref`
persisted to `localStorage`, matching the singleton pattern already used by `useFilters.js` and
`useI18n.js`.

**Responsive.** `matchMedia` watchers collapse to the icon rail below 1024px and switch to an
off-canvas overlay below 640px. A breakpoint override does not erase the user's stored
preference; it takes precedence while active and the preference is restored above the breakpoint.

**Accessibility.** `nav` landmark, `aria-current="page"` on the active link, `aria-expanded` on
the toggle, and `aria-label` on nav links whose text is hidden in the collapsed rail.

## App shell rewiring

In `client/src/App.vue`:

- `.app` becomes a two-column CSS grid: sidebar column, main column.
- Delete the `.top-nav`, `.nav-container`, and `.nav-tabs` rules.
- Rewrite the surviving global styles against tokens: `.card`, `.stat-card`, `.page-header`,
  `table`, `thead`, `th`, `td`, `.badge` and its variants, `.loading`, `.error`.
- `FilterBar` keeps its position above page content, restyled as a content-area toolbar.

`ProfileMenu` and `LanguageSwitcher` move into the sidebar footer. Both currently open with
`top: calc(100% + 0.5rem); right: 0`, which is correct for a top bar and wrong for a sidebar
footer — they must be re-anchored to open upward and rightward or they render off-screen. This is
the single fiddliest change in the migration.

## Procedure encoded in SKILL.md

Every step that creates or modifies a `.vue` file delegates to the `vue-expert` subagent, per
`CLAUDE.md`'s mandatory rule. `SKILL.md` states this once at the top of the procedure.

1. Read the current shell — `App.vue` styles, `main.js`, `FilterBar.vue`
2. Copy `reference/tokens.css` to `client/src/styles/tokens.css`; import it in `main.js`
3. Create `NavIcon.vue` from `reference/nav-icons.md`
4. Create `useSidebar.js`
5. Create `AppSidebar.vue`
6. Rewire `App.vue` — grid layout, remove top-nav CSS, rewrite globals against tokens
7. Re-anchor the `ProfileMenu` and `LanguageSwitcher` dropdowns
8. Restyle `FilterBar` as a toolbar
9. Verify

## Verification encoded in SKILL.md

- `npm run build` in `client/` compiles with no errors
- `cd tests && uv run --project ../server pytest backend/ -q` still reports 71 passed. Nothing
  here touches the backend; the run exists to catch collateral damage.
- Playwright MCP against `http://localhost:3000`:
  - all 7 routes render, with no console errors
  - the collapse toggle expands and collapses, and the state survives a reload
  - both sidebar dropdowns open fully on-screen
  - the 1024px and 640px breakpoints behave as specified
  - the `ja` locale still renders with no untranslated leaks
- Grep guard: no `.top-nav` or `.nav-tabs` references remain anywhere in `client/src/`

## Non-goals

- Does not migrate the ~400 hardcoded literals in view-scoped styles. The token layer makes that
  possible as a follow-up; doing it here would touch 18 files and every one would need to go
  through `vue-expert`.
- No dark mode.
- No changes to backend, data files, routing, nav labels, or i18n keys.
- No changes to Vue logic. This is a presentation-layer change only.

## Risks

**Global styles are load-bearing.** `App.vue`'s unscoped styles define `.card`, `table`, `.badge`
and friends for all seven views. Rewriting them against tokens can regress a view the migration
never opens. Mitigation: verification walks every route rather than spot-checking the dashboard.

**Dropdown re-anchoring.** Two components positioned for a top bar must work from a sidebar
footer, including in the collapsed rail where horizontal space is 64px. Verification checks both
dropdowns render fully on-screen.

**Scope creep into view styles.** The blast radius deliberately stops at the shell. The skill
should state the non-goal explicitly so a future run does not start sweeping view files.

---
name: vue-saas-redesign
description: Redesign this app's Vue shell into a modern SaaS layout with a collapsible left sidebar, a CSS design-token layer, and a crisp dense visual treatment. Use when asked to modernize the UI, replace the top nav bar with a sidebar, introduce design tokens, or make the interface look more professional.
---

# Vue SaaS Shell Redesign

Converts this application's shell from a top nav bar to a collapsible left sidebar, and replaces
scattered hardcoded CSS values with a token layer.

## Mandatory delegation

**Every step that creates or modifies a `.vue` file MUST be delegated to the `vue-expert`
subagent.** `CLAUDE.md` requires it. Steps below are marked where this applies.

## Scope

In scope: the shell only — `App.vue`, a new sidebar and icon component, a new composable,
`FilterBar.vue`, and the two nav-adjacent dropdown components.

Out of scope, deliberately: the ~400 hardcoded color literals and ad-hoc spacing values inside
the scoped styles of the **eight view files and nine shared components** — 17 files, every one of
which currently contains hex literals. They inherit the new look through the global `.card`,
`.stat-card`, `table` and `.badge` rules, so they need no edit here. Sweeping them is a separate
follow-up the token layer makes possible, and all 17 would need `vue-expert`.

Note for whoever does that sweep: `client/src/views/` holds **eight** files but only **seven** are
routed. `Backlog.vue` is unrouted and unimported — reachable from no URL — yet it carries the same
hardcoded styles. Do not skip it just because it is absent from the nav.

Also out of scope: dark mode, backend, data, routes, nav labels, i18n keys, and any Vue logic.
This is presentation only.

## Design rules

- Six spacing values only: `--sp-1` through `--sp-6`. No other spacing value may appear.
- Radius is `--r-sm` (4px) or `--r-md` (6px). Nothing larger.
- Cards get a hairline `1px` `--border` and **no shadow**. `--shadow-overlay` is for dropdowns
  and overlays only.
- No emojis. Icons are inline stroke SVG using `currentColor`.
- Density is a feature: this app's main screens are wide tables, so keep row padding tight.

## Procedure

1. **Read the current shell.** `client/src/App.vue` (its unscoped `<style>` block defines the
   globals every view depends on), `client/src/main.js`, `client/src/components/FilterBar.vue`.
2. **Install the token layer.** Copy `reference/tokens.css` to
   `client/src/styles/tokens.css` verbatim. Add `import './styles/tokens.css'` to
   `client/src/main.js` before the app mounts. Custom properties pierce `scoped`, which is what
   lets views inherit without being edited.
3. **Create `client/src/components/icons/NavIcon.vue`** from `reference/nav-icons.md`. Takes a
   `name` prop; renders the matching inline SVG. *(vue-expert)*
4. **Create `client/src/composables/useSidebar.js`.** Module-level refs persisted to
   `localStorage`, matching the singleton pattern in `useFilters.js` and `useI18n.js`. Collapse
   below 1024px, off-canvas overlay below 640px; a breakpoint override must not erase the stored
   preference.
5. **Create `client/src/components/AppSidebar.vue`.** Brand block, seven `router-link`s each with
   a `NavIcon` and its `t('nav.*')` label, footer holding `LanguageSwitcher` and `ProfileMenu`,
   and a collapse toggle. `nav` landmark, `aria-current="page"` on the active link,
   `aria-expanded` on the toggle, `aria-label` on links whose text is hidden when collapsed.
   **The sidebar must not set `overflow: hidden`** — `ProfileMenu`'s dropdown is `min-width:
   280px` and has to escape a 64px rail. *(vue-expert)*
6. **Rewire `App.vue`.** `.app` becomes a two-column CSS grid. Delete `.top-nav`,
   `.nav-container`, `.nav-tabs` and their descendants. Rewrite the surviving globals against
   tokens. **The main column needs `min-width: 0`** or wide tables will blow out the grid track.
   *(vue-expert)*
7. **Re-anchor and re-skin the two dropdowns.** Both currently use `top: calc(100% + 0.5rem);
   right: 0`, correct for a top bar and wrong for a sidebar footer — flip to open upward. Their
   *buttons* are also styled white-on-light and need dark-surface variants to sit on
   `--side-bg`. *(vue-expert)*
8. **Restyle `FilterBar.vue`** as a content-area toolbar. Note `position: sticky; top: 70px` is
   hardcoded to the old nav height and must become `top: 0`. *(vue-expert)*
9. **Verify** using the checklist below.

## Verification

- `cd client && npm run build` compiles with no errors.
- `cd tests && uv run --project ../server pytest backend/ -q` → 71 passed. Nothing here touches
  the backend; this catches collateral damage.
- No dead references: `grep -rn "top-nav\|nav-tabs\|nav-container" client/src/` returns nothing.
- No magic numbers reintroduced in the shell: every spacing value in `App.vue`,
  `AppSidebar.vue` and `FilterBar.vue` is a `var(--sp-*)`.
- Playwright MCP against `http://localhost:3000`:
  - all seven routes render with no console errors
  - the collapse toggle expands and collapses, and the state survives a reload
  - both sidebar dropdowns open fully on-screen, in expanded and collapsed states
  - at 1024px the sidebar is a rail; at 640px it is an off-canvas overlay
  - switching to `ja` shows no untranslated leaks

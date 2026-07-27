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

## Known pre-existing defects, out of scope

These predate this redesign and are unrelated to the shell. Do not "fix" them as part of this
skill and do not mistake them for a regression it caused:
- `GET /api/tasks` 404s — `api.js` calls four task endpoints the backend never implemented.
- `Dashboard.vue:289` renders `<PurchaseOrderModal>`, which is never imported and has no component
  file.
- `Reports.vue` emits ~90 `console.log` statements per visit.

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
   below 1024px, off-canvas overlay below 640px (`overlayMode`); a breakpoint override must not
   erase the stored preference. Because the overlay breakpoint (640px) sits fully inside the
   collapse range (1024px), **`isOverlay` always implies `isCollapsed`** — every later step that
   reasons about "collapsed" must account for the overlay-open case separately, or it will treat
   the open mobile drawer as just a narrow rail.
5. **Create `client/src/components/AppSidebar.vue`.** Brand block, seven `router-link`s each with
   a `NavIcon` and its `t('nav.*')` label, footer holding `LanguageSwitcher` and `ProfileMenu`,
   and a collapse toggle. Give the `<aside>` `id="app-sidebar"` (step 9 needs it). `nav` landmark,
   `aria-current="page"` on the active link.
   **Label visibility and `aria-expanded` must NOT be driven by `!isCollapsed` alone** — because
   of the implication noted in step 4, that naive form makes the open mobile drawer show
   unlabeled icons only, and makes `aria-expanded` permanently `false` in the one mode where the
   toggle actually does something (in overlay mode the toggle no longer collapses/expands, it
   opens/closes `overlayOpen`). Instead:
   - `const showLabels = computed(() => !isCollapsed.value || (isOverlay.value && overlayOpen.value))`
   - `:aria-expanded="isOverlay ? overlayOpen : !isCollapsed"`
   Gate `aria-label` on nav links unconditionally (cheap, and correct in every state) rather than
   only when labels are hidden.
   **The sidebar must not set `overflow: hidden`** — `ProfileMenu`'s dropdown is `min-width:
   280px` and has to escape a 64px rail; put `overflow-y: auto` on the inner `.nav` list instead,
   not on `.sidebar` itself, so the footer dropdowns can still escape. *(vue-expert)*
6. **Rewire `App.vue`.** `.app` is a two-column CSS grid, but the split is three-way, not
   two-way: toggle `grid-template-columns` between the expanded sidebar width, the collapsed
   width, and a single content-only column, via `sidebar-collapsed` / `sidebar-overlay` classes
   on `.app` (bound from the same `isCollapsed`/`isOverlay` used everywhere else). Do not just
   change the sidebar's own width and leave the grid track wide — a full-width track holding a
   narrow panel wastes the reclaimed space instead of giving it to content. Delete `.top-nav`,
   `.nav-container`, `.nav-tabs` and their descendants. Rewrite the surviving globals against
   tokens. Keep `.main-content`'s `max-width: 1600px; margin: 0 auto` — it caps line length on
   wide displays and is independent of the sidebar's own width, so don't fold it into the
   sidebar math or drop it as dead-looking code. **The main column needs `min-width: 0`** or wide
   tables will blow out the grid track. *(vue-expert)*
7. **Re-anchor and re-skin the two dropdowns.** Both currently use `top: calc(100% + 0.5rem);
   right: 0`, correct for a top bar and wrong for a sidebar footer — flip to open upward. Their
   *buttons* are also styled white-on-light and need dark-surface variants to sit on
   `--side-bg`. *(vue-expert)*
8. **Restyle `FilterBar.vue`** as a content-area toolbar. Note `position: sticky; top: 70px` is
   hardcoded to the old nav height and must become `top: 0`. It spans the content column
   edge-to-edge (no width cap here — that lives on `.main-content` per step 6). *(vue-expert)*
9. **Add a mobile drawer opener to `FilterBar.vue`.** The sidebar's own collapse toggle (step 5)
   goes off-canvas with the panel in overlay mode — `transform: translateX(-100%)` takes it along
   — so it cannot be the only way to open the drawer once it's closed. Add a hamburger button,
   rendered only `v-if="isOverlay"`, wired to `toggle` from `useSidebar()`, with
   `:aria-expanded="overlayOpen"` and `aria-controls="app-sidebar"`. Place it in the toolbar
   (not loose in `App.vue`) so it stays reachable while the page is scrolled, since the toolbar
   is itself `position: sticky`. *(vue-expert)*
10. **Verify** using the checklist below.

## Verification

- `cd client && npm run build` compiles with no errors.
- `cd tests && uv run --project ../server pytest backend/ -q` → 71 passed. Nothing here touches
  the backend; this catches collateral damage.
- No dead references: `grep -rn "top-nav\|nav-tabs\|nav-container" client/src/` returns nothing.
- No banned literals reintroduced in the shell. Run:
  ```
  grep -nE "[0-9]+(\.[0-9]+)?rem|#[0-9a-fA-F]{3,8}|rgba\(" client/src/App.vue client/src/components/AppSidebar.vue client/src/components/FilterBar.vue client/src/components/ProfileMenu.vue client/src/components/LanguageSwitcher.vue | grep -vE "var\(--|color-mix|letter-spacing"
  ```
  Five files, matching `## Scope` (the two dropdowns are in scope). Excludes `color-mix` (the
  sanctioned way to derive a scrim or focus-ring shade from a token) rather than `rgba` — every
  `rgba(` in the shell should already be gone, so excluding `rgba` instead would just hide a
  regression. Expect **zero** hits in `App.vue`, `AppSidebar.vue`, `FilterBar.vue`. Hits in
  `ProfileMenu.vue`/`LanguageSwitcher.vue` (font-sizes, a few text/icon hex colors) are expected —
  those two files are only partially tokenized by design, per `## Scope`; do not sweep them under
  this skill. This grep does not test bare `px`: `min-width: 140px` on `.filter-select`, the
  `18px` reset-icon dimensions, and a `3px` focus-ring offset in `FilterBar.vue` are legitimate
  control-sizing literals, not spacing that belongs in `--sp-*` — leave them.
- Playwright MCP against `http://localhost:3000`:
  - all seven routes render with no console errors
  - the collapse toggle expands and collapses, and the state survives a reload
  - both sidebar dropdowns open fully on-screen, in expanded and collapsed states
  - at 1024px the sidebar is a rail; at 640px it is an off-canvas overlay reachable only via the
    step-9 hamburger, and opening it shows full labels, not an icon-only drawer
  - switching to `ja` shows no untranslated leaks

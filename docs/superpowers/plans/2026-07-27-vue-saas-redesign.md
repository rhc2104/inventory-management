# Vue SaaS Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repo-scoped skill that converts this app's shell to a modern SaaS layout, then run it — replacing the top nav bar with a collapsible left sidebar, introducing a CSS-variable token layer, and applying a crisp, dense visual treatment.

**Architecture:** Two phases. Phase 1 (Tasks 1–3) builds `.claude/skills/vue-saas-redesign/` and touches no application code. Phase 2 (Tasks 4–11) follows that skill's own procedure against `client/`. The token layer lands as a plain CSS file imported in `main.js`; because CSS custom properties pierce Vue's `scoped` attribute, the seven existing views inherit the new look through the global `.card` / `.stat-card` / `table` / `.badge` rules without their own styles being rewritten.

**Tech Stack:** Vue 3.4 Composition API, vue-router 4, Vite 5, plain CSS custom properties. No new runtime or dev dependencies.

## Global Constraints

- **Every `.vue` file creation or modification MUST be delegated to the `vue-expert` subagent.** `CLAUDE.md` states this as a mandatory rule. Tasks 5, 7, 8, 9, 10 are all `vue-expert` tasks.
- **No emojis anywhere in the UI.** Nav icons are inline stroke SVG.
- Palette is fixed to what `CLAUDE.md` already documents: ink `#0f172a`, muted `#64748b`, border `#e2e8f0`, canvas `#f8fafc`, surface `#ffffff`, plus the existing green/blue/amber/red status colors. Stray literals get consolidated into these, not preserved.
- Radius never exceeds `6px`. Cards get hairline `1px` borders and **no shadow**; the single shadow token is reserved for overlays and dropdowns.
- Scope stops at the shell. Do **not** sweep the ~400 hardcoded literals inside view-scoped styles — that is an explicit non-goal in the spec.
- No changes to backend, data files, routes, nav labels, or i18n keys.
- Skill lives at `.claude/skills/`, never `~/.claude/skills/`.

## Testing Approach — read before Task 1

**This repo has no frontend test framework.** `client/package.json` carries only `vue`, `vue-router`, `axios`, `vite`, `@vitejs/plugin-vue` — no vitest, no `@vue/test-utils`. The plan therefore does **not** use red-green unit tests for the Vue work. Each task's test cycle is instead:

1. `npm run build` in `client/` — catches template and import errors
2. A targeted assertion: a `grep` guard, or a Playwright MCP check against `http://localhost:3000`

This is a deliberate deviation from the usual TDD default. Adding vitest would be new infrastructure the spec does not ask for, and for `useSidebar.js` — the one unit with real logic — the behavior is `localStorage` plus `matchMedia`, which a real browser exercises more honestly than jsdom mocks. If you would rather have vitest, stop and say so before Task 4; retrofitting it later means rewriting every verification step.

Backend tests must keep passing throughout as a collateral-damage guard: `cd tests && uv run --project ../server pytest backend/ -q` → **71 passed**.

---

# Phase 1 — Build the skill

### Task 1: Token layer asset

**Files:**
- Create: `.claude/skills/vue-saas-redesign/reference/tokens.css`

**Interfaces:**
- Produces: the complete set of custom-property names later tasks consume. This list is the
  contract — it must enumerate every token in the file, with no summarizing shorthand, because a
  token present in the CSS but absent here becomes undocumented surface area:
  `--sp-1`, `--sp-2`, `--sp-3`, `--sp-4`, `--sp-5`, `--sp-6`;
  `--r-sm`, `--r-md`;
  `--ink`, `--ink-2`, `--muted`, `--border`, `--border-strong`, `--canvas`, `--surface`, `--hover`;
  `--green`, `--green-bg`, `--green-ink`, `--blue`, `--blue-bg`, `--blue-ink`,
  `--amber`, `--amber-bg`, `--amber-ink`, `--red`, `--red-bg`, `--red-ink`;
  `--indigo-bg`, `--indigo-ink` (consumed by `.badge.stable` in Task 8);
  `--side-bg`, `--side-border`, `--side-ink`, `--side-muted`, `--side-hover`;
  `--fs-xs`, `--fs-sm`, `--fs-base`, `--fs-lg`, `--fs-xl`,
  `--fs-stat` (consumed by `.stat-value` in Task 8);
  `--red-tint` (consumed by `.error` in Task 8);
  `--shadow-overlay`;
  `--sidebar-w`, `--sidebar-w-collapsed`, `--toolbar-h`.

- [ ] **Step 1: Create the token file**

```css
/* Design tokens for the SaaS shell redesign.
   Values consolidate the palette CLAUDE.md documents; an audit found 51 unique
   color literals and 26 ad-hoc rem spacing values, which these replace. */
:root {
  /* Spacing — the only six values the shell may use */
  --sp-1: 4px;
  --sp-2: 8px;
  --sp-3: 12px;
  --sp-4: 16px;
  --sp-5: 24px;
  --sp-6: 32px;

  /* Radius — nothing larger; large radii read as soft, which was rejected */
  --r-sm: 4px;
  --r-md: 6px;

  /* Neutral ramp */
  --ink: #0f172a;
  --ink-2: #334155;
  --muted: #64748b;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --canvas: #f8fafc;
  --surface: #ffffff;
  --hover: #f1f5f9;

  /* Status — foreground / background / text-on-background */
  --green: #059669;
  --green-bg: #d1fae5;
  --green-ink: #065f46;
  --blue: #2563eb;
  --blue-bg: #dbeafe;
  --blue-ink: #1e40af;
  --amber: #b45309;
  --amber-bg: #fef3c7;
  --amber-ink: #92400e;
  --red: #dc2626;
  --red-bg: #fecaca;
  --red-ink: #991b1b;
  --indigo-bg: #e0e7ff;
  --indigo-ink: #3730a3;

  /* Sidebar dark ramp, derived from ink */
  --side-bg: #0f172a;
  --side-border: #1e293b;
  --side-ink: #e2e8f0;
  --side-muted: #94a3b8;
  --side-hover: #1e293b;

  /* Type — 5 steps, plus one for the oversized KPI figure */
  --fs-xs: 0.75rem;
  --fs-sm: 0.813rem;
  --fs-base: 0.875rem;
  --fs-lg: 1.125rem;
  --fs-xl: 1.5rem;
  --fs-stat: 1.75rem;

  /* Single-use tint behind .error. Tokenized so the shell can contain
     literally zero magic numbers. */
  --red-tint: #fef2f2;

  /* Exactly one shadow, for overlays and dropdowns only. Never on cards. */
  --shadow-overlay: 0 10px 25px rgba(15, 23, 42, 0.12);

  /* Layout */
  --sidebar-w: 240px;
  --sidebar-w-collapsed: 64px;
  --toolbar-h: 52px;
}
```

- [ ] **Step 2: Verify it parses as valid CSS**

Run: `npx --yes csstree-validator .claude/skills/vue-saas-redesign/reference/tokens.css`
Expected: no errors reported. If `csstree-validator` is unavailable offline, fall back to `node -e "const c=require('fs').readFileSync('.claude/skills/vue-saas-redesign/reference/tokens.css','utf8'); if((c.match(/{/g)||[]).length!==(c.match(/}/g)||[]).length) throw new Error('brace mismatch'); console.log('braces balanced')"`

- [ ] **Step 3: Confirm no value violates the constraints**

Run: `grep -nE "border-radius|[0-9]+px" .claude/skills/vue-saas-redesign/reference/tokens.css | grep -vE "\-\-(sp|r|sidebar|toolbar)" | grep -vE "rgba"`
Expected: no output beyond the `--shadow-overlay` line. Any stray pixel value means a magic number slipped in.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/vue-saas-redesign/reference/tokens.css
git commit -m "Add design token asset for SaaS redesign skill"
```

---

### Task 2: Nav icon asset

**Files:**
- Create: `.claude/skills/vue-saas-redesign/reference/nav-icons.md`

**Interfaces:**
- Produces: seven icon names consumed by `NavIcon.vue` in Task 5 — `overview`, `inventory`, `orders`, `finance`, `demand`, `restocking`, `reports`. These strings are the `name` prop values; they must match exactly.

- [ ] **Step 1: Create the icon reference**

````markdown
# Nav icons

One per route. All are `24×24` viewBox, `stroke="currentColor"`, `stroke-width="1.5"`,
`fill="none"`, `stroke-linecap="round"`, `stroke-linejoin="round"` — so they inherit the nav
link's color automatically and need no fill management.

Copy the inner paths into `NavIcon.vue`'s lookup keyed by these exact names.

| name | route |
| --- | --- |
| `overview` | `/` |
| `inventory` | `/inventory` |
| `orders` | `/orders` |
| `finance` | `/spending` |
| `demand` | `/demand` |
| `restocking` | `/restocking` |
| `reports` | `/reports` |

## overview
```html
<rect x="3" y="3" width="7" height="7" rx="1" />
<rect x="14" y="3" width="7" height="7" rx="1" />
<rect x="3" y="14" width="7" height="7" rx="1" />
<rect x="14" y="14" width="7" height="7" rx="1" />
```

## inventory
```html
<path d="M21 8 12 3 3 8v8l9 5 9-5V8Z" />
<path d="M3 8l9 5 9-5" />
<path d="M12 13v8" />
```

## orders
```html
<path d="M9 3h6a1 1 0 0 1 1 1v1H8V4a1 1 0 0 1 1-1Z" />
<path d="M8 5H6a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1h-2" />
<path d="M9 11h6" />
<path d="M9 15h4" />
```

## finance
```html
<rect x="2" y="6" width="20" height="12" rx="2" />
<circle cx="12" cy="12" r="2.5" />
<path d="M6 10v4" />
<path d="M18 10v4" />
```

## demand
```html
<path d="M3 17l6-6 4 4 7-7" />
<path d="M14 8h6v6" />
```

## restocking
```html
<path d="M21 12a9 9 0 1 1-3-6.7" />
<path d="M21 4v5h-5" />
```

## reports
```html
<path d="M14 2H6a1 1 0 0 0-1 1v18a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V7Z" />
<path d="M14 2v5h5" />
<path d="M9 13h6" />
<path d="M9 17h6" />
```
````

- [ ] **Step 2: Verify all seven names are present**

Run: `for n in overview inventory orders finance demand restocking reports; do grep -q "^## $n$" .claude/skills/vue-saas-redesign/reference/nav-icons.md && echo "$n OK" || echo "$n MISSING"; done`
Expected: seven `OK` lines, no `MISSING`.

- [ ] **Step 3: Verify no emoji crept in**

Run: `python3 -c "import re; s=open('.claude/skills/vue-saas-redesign/reference/nav-icons.md',encoding='utf-8').read(); h=re.findall('[\U0001F300-\U0001FAFF]',s); print(h or 'clean')"`
Expected: `clean`

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/vue-saas-redesign/reference/nav-icons.md
git commit -m "Add nav icon asset for SaaS redesign skill"
```

---

### Task 3: SKILL.md

**Files:**
- Create: `.claude/skills/vue-saas-redesign/SKILL.md`

**Interfaces:**
- Consumes: `reference/tokens.css` (Task 1), `reference/nav-icons.md` (Task 2)
- Produces: the procedure Tasks 4–11 follow. Phase 2 is the skill executing itself, so anything omitted here is omitted from the redesign.

- [ ] **Step 1: Write SKILL.md**

Frontmatter `description` must name the trigger phrasings, not just the skill's purpose, so it is discoverable from "modernize the UI" / "replace the top nav" / "add a sidebar":

````markdown
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

Out of scope, deliberately: the ~400 hardcoded color literals and ad-hoc spacing values inside the
scoped styles of the **eight view files and nine shared components** — 17 files, every one of which
currently contains hex literals. They inherit the new look through the global `.card`,
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
````

- [ ] **Step 2: Verify frontmatter is valid and complete**

Run: `python3 -c "
import re
s=open('.claude/skills/vue-saas-redesign/SKILL.md',encoding='utf-8').read()
m=re.match(r'^---\n(.*?)\n---\n', s, re.S)
assert m, 'no frontmatter'
fm=m.group(1)
assert 'name: vue-saas-redesign' in fm, 'name wrong'
assert 'description:' in fm, 'no description'
assert len([l for l in fm.splitlines() if l.startswith(('name:','description:'))])==2
print('frontmatter OK')
"`
Expected: `frontmatter OK`

- [ ] **Step 3: Verify the skill is registered**

Run: `ls .claude/skills/`
Expected: `backend-api-test` and `vue-saas-redesign`. Restart the session if the skill does not appear in the available-skills list; skills are enumerated at startup.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/vue-saas-redesign/SKILL.md
git commit -m "Add SKILL.md for the Vue SaaS redesign skill"
```

---

# Phase 2 — Run the skill

From here, follow `SKILL.md`'s own procedure. Each task below is one of its numbered steps.

### Task 4: Install the token layer

**Files:**
- Create: `client/src/styles/tokens.css` (verbatim copy of the Task 1 asset)
- Modify: `client/src/main.js:1-3`

**Interfaces:**
- Consumes: `.claude/skills/vue-saas-redesign/reference/tokens.css`
- Produces: all custom properties from Task 1, globally available — including inside every `scoped` style block.

- [ ] **Step 1: Copy the asset in**

```bash
mkdir -p client/src/styles
cp .claude/skills/vue-saas-redesign/reference/tokens.css client/src/styles/tokens.css
```

- [ ] **Step 2: Import it in `main.js`**

Add as the first import so tokens are defined before any component style is evaluated:

```js
import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './styles/tokens.css'
import App from './App.vue'
```

- [ ] **Step 3: Verify the build resolves the import**

Run: `cd client && npm run build`
Expected: compiles; `dist/` CSS contains the tokens. Confirm with `grep -c "\-\-sidebar-w" dist/assets/*.css` → at least 1.

- [ ] **Step 4: Verify tokens reach the browser**

With dev servers running, Playwright MCP `browser_evaluate`:

```js
() => getComputedStyle(document.documentElement).getPropertyValue('--sidebar-w').trim()
```
Expected: `240px`

- [ ] **Step 5: Commit**

```bash
git add client/src/styles/tokens.css client/src/main.js
git commit -m "Add design token layer and import it at app entry"
```

---

### Task 5: NavIcon component

**Files:**
- Create: `client/src/components/icons/NavIcon.vue`

**Interfaces:**
- Consumes: `reference/nav-icons.md` icon names
- Produces: `<NavIcon name="overview" />` — accepts exactly `overview`, `inventory`, `orders`, `finance`, `demand`, `restocking`, `reports`. Renders a `24×24` SVG inheriting `currentColor`. Unknown names render nothing rather than throwing.

**DELEGATE TO `vue-expert`.**

- [ ] **Step 1: Create the component via vue-expert**

The full component, icon paths included — do not go read Task 2 for them.

Icons are static `<g v-if>` blocks rather than a `v-html` lookup. It is more
lines, but nothing is ever rendered as raw HTML, so there is no injection surface to
reason about and no script logic at all:

```vue
<template>
  <!-- currentColor means icons inherit the nav link's color, so hover and
       active states need no separate icon rules. -->
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <g v-if="name === 'overview'">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </g>
    <g v-else-if="name === 'inventory'">
      <path d="M21 8 12 3 3 8v8l9 5 9-5V8Z" />
      <path d="M3 8l9 5 9-5" />
      <path d="M12 13v8" />
    </g>
    <g v-else-if="name === 'orders'">
      <path d="M9 3h6a1 1 0 0 1 1 1v1H8V4a1 1 0 0 1 1-1Z" />
      <path d="M8 5H6a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1h-2" />
      <path d="M9 11h6" />
      <path d="M9 15h4" />
    </g>
    <g v-else-if="name === 'finance'">
      <rect x="2" y="6" width="20" height="12" rx="2" />
      <circle cx="12" cy="12" r="2.5" />
      <path d="M6 10v4" />
      <path d="M18 10v4" />
    </g>
    <g v-else-if="name === 'demand'">
      <path d="M3 17l6-6 4 4 7-7" />
      <path d="M14 8h6v6" />
    </g>
    <g v-else-if="name === 'restocking'">
      <path d="M21 12a9 9 0 1 1-3-6.7" />
      <path d="M21 4v5h-5" />
    </g>
    <g v-else-if="name === 'reports'">
      <path d="M14 2H6a1 1 0 0 0-1 1v18a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V7Z" />
      <path d="M14 2v5h5" />
      <path d="M9 13h6" />
      <path d="M9 17h6" />
    </g>
  </svg>
</template>

<script>
export default {
  name: 'NavIcon',
  props: {
    name: { type: String, required: true }
  }
}
</script>
```

An unrecognized `name` renders an empty `<svg>` rather than throwing.

- [ ] **Step 2: Verify the build compiles**

Run: `cd client && npm run build`
Expected: no errors.

- [ ] **Step 3: Verify all seven names render an SVG**

Playwright MCP, after Task 7 mounts the sidebar, will cover this in context. For now assert the constant is complete:

Run: `for n in overview inventory orders finance demand restocking reports; do grep -q "name === '$n'" client/src/components/icons/NavIcon.vue && echo "$n OK" || echo "$n MISSING"; done`
Expected: seven `OK`.

- [ ] **Step 4: Commit**

```bash
git add client/src/components/icons/NavIcon.vue
git commit -m "Add NavIcon component with seven inline stroke icons"
```

---

### Task 6: useSidebar composable

**Files:**
- Create: `client/src/composables/useSidebar.js`

**Interfaces:**
- Produces: `useSidebar()` returning `{ isCollapsed, isOverlay, overlayOpen, toggle, closeOverlay }`. `isCollapsed` and `isOverlay` are readonly computeds; `overlayOpen` is a `ref`; `toggle()` and `closeOverlay()` are functions. Task 7 consumes all five. `localStorage` key is `app-sidebar-collapsed`.

- [ ] **Step 1: Create the composable**

```js
import { computed, ref, watch } from 'vue'

const STORAGE_KEY = 'app-sidebar-collapsed'
const RAIL_MAX = 1023   // below 1024px: force the icon rail
const OVERLAY_MAX = 639 // below 640px: off-canvas overlay

// Module-level refs so every component shares one instance, matching the
// singleton pattern in useFilters.js and useI18n.js.
const userCollapsed = ref(localStorage.getItem(STORAGE_KEY) === 'true')
const forcedCollapsed = ref(false)
const overlayMode = ref(false)
const overlayOpen = ref(false)

// A narrow viewport wins while it applies, but must not overwrite what the user
// chose — widening the window restores their preference.
const isCollapsed = computed(() => forcedCollapsed.value || userCollapsed.value)
const isOverlay = computed(() => overlayMode.value)

watch(userCollapsed, (value) => {
  localStorage.setItem(STORAGE_KEY, String(value))
})

let listenersAttached = false
function attachBreakpointListeners() {
  if (listenersAttached) return
  listenersAttached = true

  const rail = window.matchMedia(`(max-width: ${RAIL_MAX}px)`)
  const overlay = window.matchMedia(`(max-width: ${OVERLAY_MAX}px)`)

  const sync = () => {
    forcedCollapsed.value = rail.matches
    overlayMode.value = overlay.matches
    // Leaving overlay mode must not strand the drawer open.
    if (!overlay.matches) overlayOpen.value = false
  }

  rail.addEventListener('change', sync)
  overlay.addEventListener('change', sync)
  sync()
}

export function useSidebar() {
  attachBreakpointListeners()

  const toggle = () => {
    if (overlayMode.value) {
      overlayOpen.value = !overlayOpen.value
    } else {
      userCollapsed.value = !userCollapsed.value
    }
  }

  const closeOverlay = () => {
    overlayOpen.value = false
  }

  return { isCollapsed, isOverlay, overlayOpen, toggle, closeOverlay }
}
```

- [ ] **Step 2: Verify the syntax parses**

Do not try to `import()` the file directly — `vue` will not resolve outside Vite and the failure
would be meaningless. Check syntax only:

Run: `cd client && node -e "new (require('vm').Script)(require('fs').readFileSync('src/composables/useSidebar.js','utf8'),{});" 2>&1 | head -3 || true`
Expected: no `SyntaxError`. ES module syntax will report `Cannot use import statement outside a
module` — that message means the file parsed and is fine. Any `SyntaxError` is a real failure.

- [ ] **Step 3: Verify via build**

Run: `cd client && npm run build`
Expected: compiles. The composable is not imported yet, so this only confirms it does not break the graph.

- [ ] **Step 4: Commit**

```bash
git add client/src/composables/useSidebar.js
git commit -m "Add useSidebar composable with persisted collapse and breakpoints"
```

---

### Task 7: AppSidebar component

**Files:**
- Create: `client/src/components/AppSidebar.vue`

**Interfaces:**
- Consumes: `useSidebar()` (Task 6), `NavIcon` (Task 5), `useI18n()` for `t`, existing `LanguageSwitcher` and `ProfileMenu` components
- Produces: `<AppSidebar @show-profile-details @show-tasks />` — re-emits the two events `ProfileMenu` already emits, so `App.vue` keeps its existing modal wiring unchanged.

**DELEGATE TO `vue-expert`.**

- [ ] **Step 1: Create the component via vue-expert**

Seven nav entries, in the order the current top nav uses — `/` Overview, `/inventory` Inventory, `/orders` Orders, `/spending` Finance, `/demand` Demand Forecast, `/restocking` Restocking, `/reports` Reports. Note `/reports` currently has a hardcoded English `Reports` label in `App.vue`; keep that exact behavior, do not invent an i18n key.

Requirements to state explicitly in the brief:

- `<nav aria-label="Main">` landmark wrapping the links
- `aria-current="page"` on the active `router-link`
- toggle button with `aria-expanded` bound to `!isCollapsed` and an `aria-label`
- when `isCollapsed`, labels are visually hidden and each link carries `:aria-label` and `:title`
- **no `overflow: hidden` on the sidebar or its footer** — `ProfileMenu`'s dropdown is 280px wide and must escape a 64px rail
- overlay mode: when `isOverlay && overlayOpen`, the sidebar is `position: fixed` with a backdrop that calls `closeOverlay()` on click
- all spacing via `var(--sp-*)`, colors via `var(--side-*)`, radius via `var(--r-sm)`/`var(--r-md)`

- [ ] **Step 2: Verify the build compiles**

Run: `cd client && npm run build`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add client/src/components/AppSidebar.vue
git commit -m "Add collapsible AppSidebar component"
```

---

### Task 8: Rewire App.vue

**Files:**
- Modify: `client/src/App.vue` — template lines 1-56, and the entire unscoped `<style>` block at lines 167-489

**Interfaces:**
- Consumes: `AppSidebar` (Task 7), `useSidebar()` (Task 6), tokens (Task 4)
- Produces: the global classes every view depends on, re-expressed against tokens with identical names — `.card`, `.card-header`, `.card-title`, `.stats-grid`, `.stat-card`, `.stat-label`, `.stat-value`, `.page-header`, `.table-container`, `table`, `thead`, `th`, `td`, `.badge` and all ten variants, `.loading`, `.error`. **Renaming any of these breaks all seven views.**

**DELEGATE TO `vue-expert`.**

- [ ] **Step 1: Check whether `.subtitle` is used outside the logo**

The global `.subtitle` class currently styles the header tagline. Before moving the brand into the sidebar, confirm nothing else depends on it:

Run: `grep -rn "class=\"[^\"]*subtitle" client/src/`
Expected: only `App.vue`'s logo block. If a view uses it, the rule must stay global rather than move into `AppSidebar.vue`.

- [ ] **Step 2: Rewrite template and styles via vue-expert**

Template: replace the `<header class="top-nav">` block with `<AppSidebar @show-profile-details="showProfileDetails = true" @show-tasks="showTasks = true" />`, keep `<FilterBar />`, `<main class="main-content"><router-view /></main>` and both modals. Bind the grid state:

```vue
<div class="app" :class="{ 'sidebar-collapsed': isCollapsed, 'sidebar-overlay': isOverlay }">
```

Styles — the layout block replacing `.app` / `.top-nav` / `.nav-*`:

```css
.app {
  display: grid;
  grid-template-columns: var(--sidebar-w) 1fr;
  min-height: 100vh;
}

.app.sidebar-collapsed {
  grid-template-columns: var(--sidebar-w-collapsed) 1fr;
}

/* Overlay mode: the sidebar leaves the grid and floats above content. */
.app.sidebar-overlay {
  grid-template-columns: 1fr;
}

/* Without min-width: 0 a wide table forces the track wider than the viewport
   and the whole page scrolls sideways. The Orders and Restocking tables do
   exactly this. */
.app-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  padding: var(--sp-5);
}
```

Deleted entirely: `.top-nav`, `.nav-container`, `.nav-container > .nav-tabs`, `.nav-container > .language-switcher`, `.nav-tabs`, `.nav-tabs a`, `.nav-tabs a:hover`, `.nav-tabs a.active`, `.nav-tabs a.active::after`. The `.logo` / `.logo h1` / `.subtitle` rules move into `AppSidebar.vue` unless Step 1 found an outside consumer.

Rewritten globals — note `max-width: 1600px; margin: 0 auto` is dropped from `.main-content`, since a sidebar layout fills the viewport:

```css
.page-header { margin-bottom: var(--sp-5); }
.page-header h2 {
  font-size: var(--fs-xl);
  font-weight: 650;
  color: var(--ink);
  margin-bottom: var(--sp-1);
  letter-spacing: -0.02em;
}
.page-header p { color: var(--muted); font-size: var(--fs-base); }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-5);
}

/* Hairline border, no shadow, no hover lift — the crisp-and-dense direction. */
.stat-card {
  background: var(--surface);
  padding: var(--sp-4);
  border-radius: var(--r-md);
  border: 1px solid var(--border);
}
.stat-label {
  color: var(--muted);
  font-size: var(--fs-xs);
  font-weight: 650;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: var(--sp-2);
}
.stat-value {
  font-size: var(--fs-stat);
  font-weight: 680;
  color: var(--ink);
  letter-spacing: -0.02em;
}
.stat-card.warning .stat-value { color: var(--amber); }
.stat-card.success .stat-value { color: var(--green); }
.stat-card.danger  .stat-value { color: var(--red); }
.stat-card.info    .stat-value { color: var(--blue); }

.card {
  background: var(--surface);
  border-radius: var(--r-md);
  padding: var(--sp-4);
  border: 1px solid var(--border);
  margin-bottom: var(--sp-4);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-3);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
}
.card-title {
  font-size: var(--fs-lg);
  font-weight: 650;
  color: var(--ink);
  letter-spacing: -0.01em;
}

.table-container { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead {
  background: var(--canvas);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
th {
  text-align: left;
  padding: var(--sp-2) var(--sp-3);
  font-weight: 650;
  color: var(--muted);
  font-size: var(--fs-xs);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
td {
  padding: var(--sp-2) var(--sp-3);
  border-top: 1px solid var(--hover);
  color: var(--ink-2);
  font-size: var(--fs-base);
}
tbody tr:hover { background: var(--canvas); }

.badge {
  display: inline-block;
  padding: var(--sp-1) var(--sp-2);
  border-radius: var(--r-sm);
  font-size: var(--fs-xs);
  font-weight: 650;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.badge.success,    .badge.increasing { background: var(--green-bg);  color: var(--green-ink); }
.badge.warning,    .badge.medium     { background: var(--amber-bg);  color: var(--amber-ink); }
.badge.danger,     .badge.decreasing,
.badge.high                          { background: var(--red-bg);    color: var(--red-ink); }
.badge.info,       .badge.low        { background: var(--blue-bg);   color: var(--blue-ink); }
.badge.stable                        { background: var(--indigo-bg); color: var(--indigo-ink); }

.loading {
  text-align: center;
  padding: var(--sp-6);
  color: var(--muted);
  font-size: var(--fs-base);
}
.error {
  background: var(--red-tint);
  border: 1px solid var(--red-bg);
  color: var(--red-ink);
  padding: var(--sp-4);
  border-radius: var(--r-md);
  margin: var(--sp-4) 0;
  font-size: var(--fs-base);
}
```

- [ ] **Step 3: Verify no dead nav references remain**

Run: `grep -rn "top-nav\|nav-tabs\|nav-container" client/src/`
Expected: no output.

- [ ] **Step 4: Verify all ten badge variants survived**

Run: `for v in success warning danger info increasing decreasing stable high medium low; do grep -q "badge\.$v" client/src/App.vue && echo "$v OK" || echo "$v MISSING"; done`
Expected: ten `OK`. A missing variant means some view's badge silently loses its color.

- [ ] **Step 5: Verify the build and all seven routes**

Run: `cd client && npm run build`
Then with dev servers up, Playwright MCP: visit `/`, `/inventory`, `/orders`, `/spending`, `/demand`, `/restocking`, `/reports`. For each, assert no console errors and that `.page-header h2` is non-empty.

- [ ] **Step 6: Verify no horizontal page scroll on the widest table**

Playwright MCP at `/orders`, `browser_evaluate`:

```js
() => ({ docScroll: document.documentElement.scrollWidth, viewport: window.innerWidth })
```
Expected: `docScroll <= viewport`. A larger value means `min-width: 0` is missing on the main column.

- [ ] **Step 7: Commit**

```bash
git add client/src/App.vue
git commit -m "Replace top nav with sidebar grid and express globals as tokens"
```

---

### Task 9: Re-anchor and re-skin the dropdowns

**Files:**
- Modify: `client/src/components/ProfileMenu.vue:123-181`
- Modify: `client/src/components/LanguageSwitcher.vue:96-146`

**Interfaces:**
- Consumes: `--side-*` and `--shadow-overlay` tokens (Task 4)
- Produces: no API change. Both components keep their existing props, emits and template structure; only styles change.

**DELEGATE TO `vue-expert`.**

- [ ] **Step 1: Re-anchor both dropdowns via vue-expert**

In **both** files, the `.dropdown-menu` rule changes from opening downward-right to upward-left, since the trigger now sits at the bottom of a sidebar:

```css
.dropdown-menu {
  position: absolute;
  bottom: calc(100% + var(--sp-2));  /* was: top: calc(100% + 0.5rem) */
  left: 0;                            /* was: right: 0 */
  min-width: 160px;                   /* 280px in ProfileMenu — keep each file's value */
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-overlay);
  z-index: 1000;
  overflow: hidden;
}
```

`overflow: hidden` stays *on the dropdown* (it clips its own rounded corners) — the prohibition is on the sidebar ancestors.

- [ ] **Step 2: Re-skin both trigger buttons for a dark surface**

`.language-button` and `.profile-button` are currently `background: white; border: 1px solid #e2e8f0` — invisible-on-dark once moved. Both become:

```css
  background: transparent;
  border: 1px solid var(--side-border);
  border-radius: var(--r-md);
  color: var(--side-ink);
```

with hover `background: var(--side-hover)`. In `LanguageSwitcher.vue`, `.globe-icon` and `.chevron` change from `#64748b` to `var(--side-muted)`. In `ProfileMenu.vue`, `.profile-name` changes from `#0f172a` to `var(--side-ink)` and `.chevron` to `var(--side-muted)`. The dropdown *contents* stay light — they sit on `--surface`, not on the sidebar.

- [ ] **Step 3: Verify no light-on-light button remains**

Run: `grep -nE "background: white|background: #fff" client/src/components/ProfileMenu.vue client/src/components/LanguageSwitcher.vue`
Expected: matches only inside `.dropdown-menu` / dropdown-item rules, never on `.profile-button` or `.language-button`.

- [ ] **Step 4: Verify both dropdowns open fully on-screen**

Playwright MCP, expanded sidebar then collapsed rail. For each dropdown, click the trigger and `browser_evaluate`:

```js
() => {
  const d = document.querySelector('.dropdown-menu');
  if (!d) return 'not open';
  const r = d.getBoundingClientRect();
  return { top: r.top, left: r.left, right: r.right, bottom: r.bottom,
           insideViewport: r.top >= 0 && r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight };
}
```
Expected: `insideViewport: true` in all four combinations (two dropdowns × expanded/collapsed).

- [ ] **Step 5: Commit**

```bash
git add client/src/components/ProfileMenu.vue client/src/components/LanguageSwitcher.vue
git commit -m "Re-anchor and re-skin sidebar dropdowns for a dark surface"
```

---

### Task 10: Restyle FilterBar as a toolbar

**Files:**
- Modify: `client/src/components/FilterBar.vue:103-194`

**Interfaces:**
- Consumes: tokens (Task 4)
- Produces: no API change. Template and script untouched; styles only.

**DELEGATE TO `vue-expert`.**

- [ ] **Step 1: Restyle via vue-expert**

The critical fix — `top: 70px` is the old nav height and strands the bar 70px down the page once the nav is gone:

```css
.filters-bar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: var(--sp-2) 0;
  position: sticky;
  top: 0;              /* was: top: 70px — the removed nav's height */
  z-index: 90;
}

.filters-container {
  /* max-width: 1600px and margin: 0 auto are dropped; the sidebar layout
     already constrains width. */
  padding: 0 var(--sp-5);
  display: flex;
  align-items: center;
  gap: var(--sp-4);
}

.filter-group { display: flex; align-items: center; gap: var(--sp-2); }
.filter-group label {
  font-size: var(--fs-xs);
  font-weight: 650;
  color: var(--muted);
  white-space: nowrap;
}

.filter-select {
  padding: var(--sp-1) var(--sp-2);
  border: 1px solid var(--border-strong);
  border-radius: var(--r-sm);
  font-size: var(--fs-sm);
  color: var(--ink);
  background: var(--surface);
  cursor: pointer;
  font-weight: 500;
  min-width: 140px;
}
.filter-select:hover { border-color: var(--muted); }
.filter-select:focus {
  outline: none;
  border-color: var(--blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.reset-filters-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-1);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  color: var(--muted);
  cursor: pointer;
  flex-shrink: 0;
}
.reset-filters-btn:hover:not(:disabled) {
  background: var(--canvas);
  border-color: var(--border-strong);
  color: var(--ink);
}
.reset-filters-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.reset-filters-btn svg { width: 18px; height: 18px; }
```

Leave the `title="Reset all filters"` attribute alone. It is untranslated, but that is pre-existing and i18n keys are out of scope.

- [ ] **Step 2: Verify the stale offset is gone**

Run: `grep -n "70px" client/src/components/FilterBar.vue`
Expected: no output.

- [ ] **Step 3: Verify the bar sticks to the top of the content column**

Playwright MCP at `/orders`: scroll down 400px, then `browser_evaluate`:

```js
() => document.querySelector('.filters-bar').getBoundingClientRect().top
```
Expected: `0`.

- [ ] **Step 4: Commit**

```bash
git add client/src/components/FilterBar.vue
git commit -m "Restyle FilterBar as a content-area toolbar"
```

---

### Task 11: Full verification sweep

**Files:**
- No production changes. Fixes discovered here are committed against the task that owns the file.

- [ ] **Step 1: Build and backend regression**

Run: `cd client && npm run build && cd ../tests && uv run --project ../server pytest backend/ -q`
Expected: build succeeds; `71 passed`.

- [ ] **Step 2: Magic-number guard on the shell**

Run: `grep -nE "[0-9]+(\.[0-9]+)?rem|#[0-9a-fA-F]{3,8}" client/src/App.vue client/src/components/AppSidebar.vue client/src/components/FilterBar.vue | grep -vE "var\(--|letter-spacing|rgba"`
Expected: **no output at all.** Every spacing value, color and font size in the shell resolves
through a token — there are no whitelisted exceptions. Any hit is a magic number to tokenize.

- [ ] **Step 3: All seven routes, no console errors**

Playwright MCP: visit each of `/`, `/inventory`, `/orders`, `/spending`, `/demand`, `/restocking`, `/reports`; collect `browser_console_messages` after each.

Expected: no `[ERROR]` or `[WARN]` entries **other than these two pre-existing defects**, both unrelated to this change and both out of scope (this redesign is presentation-only):

1. A 404 on `GET /api/tasks` — `api.js` calls four task endpoints the backend never implemented. Fires on every page load from `App.vue`'s `onMounted`.
2. `Failed to resolve component: PurchaseOrderModal` on `/` — `Dashboard.vue:289` renders `<PurchaseOrderModal>`, which is never imported and has no file in `client/src/components/`. Vue renders nothing in its place.

Both are orphans of an abandoned purchase-order feature, documented in `docs/architecture.html`. Any error or warning **beyond these two** is a regression this task introduced and must be fixed. Do not silently widen this whitelist: if a third pre-existing error appears, stop and report it rather than adding it here.

- [ ] **Step 4: Collapse toggle and persistence**

Playwright MCP: click the toggle, assert `document.querySelector('.app').classList.contains('sidebar-collapsed')` flips; reload; assert the class persists and `localStorage.getItem('app-sidebar-collapsed')` matches.

- [ ] **Step 5: Breakpoints**

Playwright MCP `browser_resize`: at `1000×800` assert the sidebar is a rail; at `600×800` assert overlay mode — sidebar off-canvas until the toggle opens it, and the backdrop closes it. Resize back to `1400×900` and assert the pre-resize preference is restored, not lost.

- [ ] **Step 6: Japanese locale**

Playwright MCP: switch to 日本語, walk the seven routes, assert no untranslated English leaks in the sidebar or toolbar.

- [ ] **Step 7: Commit any fixes and finish**

```bash
git add -A client/
git commit -m "Fix issues found during redesign verification"
```

If nothing needed fixing, skip the commit and note that verification passed clean.

---

## Self-Review

**Spec coverage.** Every spec section maps to a task: artifact layout → Tasks 1–3; token layer → Tasks 1, 4; sidebar incl. icons, composable, responsive, a11y → Tasks 2, 5, 6, 7; App shell rewiring → Task 8; dropdown re-anchoring → Task 9; FilterBar → Task 10; verification → Task 11 plus per-task steps; two-phase delivery → the Phase 1 / Phase 2 split; non-goals → Global Constraints and `SKILL.md`'s Scope section.

**Type and name consistency.** `useSidebar()` returns exactly `{ isCollapsed, isOverlay, overlayOpen, toggle, closeOverlay }` in Task 6 and Task 7 consumes those five names. `NavIcon`'s seven names are identical in Tasks 2, 5 and 7. The `localStorage` key is `app-sidebar-collapsed` in Tasks 6 and 11. The ten `.badge` variants enumerated in Task 8 match the ten in the current `App.vue`.

**Known gaps, called out rather than hidden.** One item the spec leaves to implementation and this plan resolves by decision: `/reports` keeps its hardcoded English label (Task 7), because adding an i18n key is out of scope and inventing one would be scope creep.

**Amended after the pre-flight scan** (three rubric conflicts resolved before execution):

1. Task 5 no longer uses `v-html`. Icons are static `<g v-if>` blocks, so no raw HTML is ever
   rendered and the injection question does not arise.
2. `--fs-stat` and `--red-tint` were added to the token set, so `.stat-value` and `.error` carry
   no literals. Task 11's magic-number guard is now absolute — zero expected output, no whitelist
   to defend.
3. Task 6's syntax check no longer instructs a command that is expected to fail.

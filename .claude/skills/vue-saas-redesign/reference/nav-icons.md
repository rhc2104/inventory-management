# Nav icons

One per route. All are `24×24` viewBox, `stroke="currentColor"`, `stroke-width="1.5"`,
`fill="none"`, `stroke-linecap="round"`, `stroke-linejoin="round"` — so they inherit the nav
link's color automatically and need no fill management.

`NavIcon.vue` takes a `name` prop and renders one shared `<svg>` wrapper whose contents are a
static `<g v-if="name === '...'">` / `<g v-else-if="name === '...'">` branch per icon below, one
branch per row of the table — not a JS object of markup strings keyed by these names. A
string-keyed lookup rendered with `v-html` was considered for this and rejected: it takes
untrusted-shaped string interpolation to render markup for something that is fully static at
build time, where a plain template branch does the same job with no `v-html` at all. Copy each
icon's inner paths into its own `<g v-else-if="name === '<name>'">` branch, keyed by these exact
names.

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

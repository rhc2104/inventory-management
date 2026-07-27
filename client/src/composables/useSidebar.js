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

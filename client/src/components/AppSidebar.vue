<template>
  <!-- Backdrop only exists while the off-canvas drawer is open; clicking it
       closes the drawer the same way a click outside a dropdown would. -->
  <div
    v-if="isOverlay && overlayOpen"
    class="backdrop"
    @click="closeOverlay"
  ></div>

  <aside
    class="sidebar"
    :class="{ collapsed: isCollapsed, 'is-overlay': isOverlay, 'overlay-open': isOverlay && overlayOpen }"
  >
    <div class="brand">
      <div v-if="!isCollapsed" class="brand-text">
        <h1 class="brand-name">{{ t('nav.companyName') }}</h1>
        <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
      </div>

      <button
        type="button"
        class="toggle-btn"
        :aria-expanded="!isCollapsed"
        aria-label="Toggle sidebar"
        @click="toggle"
      >
        <svg
          class="chevron"
          :class="{ flipped: isCollapsed }"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M15 6l-6 6 6 6" />
        </svg>
      </button>
    </div>

    <nav aria-label="Main" class="nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-link"
        :aria-current="$route.path === item.path ? 'page' : null"
        :aria-label="item.label"
        :title="item.label"
      >
        <NavIcon :name="item.icon" class="nav-icon" />
        <span v-if="!isCollapsed" class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="footer">
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="emit('show-profile-details')"
        @show-tasks="emit('show-tasks')"
      />
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useSidebar } from '../composables/useSidebar'
import { useI18n } from '../composables/useI18n'
import NavIcon from './icons/NavIcon.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

const emit = defineEmits(['show-profile-details', 'show-tasks'])

const { isCollapsed, isOverlay, overlayOpen, toggle, closeOverlay } = useSidebar()
const { t } = useI18n()

// /reports has no i18n key in the current app (App.vue hardcodes the English
// literal) — preserved as-is rather than inventing nav.reports.
const navItems = computed(() => [
  { path: '/', label: t('nav.overview'), icon: 'overview' },
  { path: '/inventory', label: t('nav.inventory'), icon: 'inventory' },
  { path: '/orders', label: t('nav.orders'), icon: 'orders' },
  { path: '/spending', label: t('nav.finance'), icon: 'finance' },
  { path: '/demand', label: t('nav.demandForecast'), icon: 'demand' },
  { path: '/restocking', label: t('nav.restocking'), icon: 'restocking' },
  { path: '/reports', label: 'Reports', icon: 'reports' }
])
</script>

<style scoped>
/* rgba scrim mirrors the existing .modal-overlay pattern used across the app
   (e.g. ProfileDetailsModal); tokens.css has no dedicated scrim color. */
.backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  z-index: 190;
}

.sidebar {
  display: flex;
  flex-direction: column;
  width: var(--sidebar-w);
  height: 100vh;
  background: var(--side-bg);
  border-right: 1px solid var(--side-border);
  position: sticky;
  top: 0;
  flex-shrink: 0;
  transition: width 0.2s ease;
  /* Intentionally no overflow rule here: ProfileMenu's 280px dropdown and the
     LanguageSwitcher dropdown must be able to render past a 64px rail. */
}

.sidebar.collapsed {
  width: var(--sidebar-w-collapsed);
}

/* Overlay mode takes the sidebar out of flow entirely. It stays whatever
   width .collapsed already gave it (isOverlay implies isCollapsed via the
   composable's breakpoints) and instead slides fully off-canvas with
   transform, so "closed" means gone, not just narrow. */
.sidebar.is-overlay {
  position: fixed;
  left: 0;
  top: 0;
  transform: translateX(-100%);
  transition: transform 0.2s ease;
  z-index: 200;
}

.sidebar.is-overlay.overlay-open {
  transform: translateX(0);
  box-shadow: var(--shadow-overlay);
}

.brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-3);
  border-bottom: 1px solid var(--side-border);
}

.sidebar.collapsed .brand {
  justify-content: center;
}

.brand-text {
  min-width: 0;
}

.brand-name {
  font-size: var(--fs-lg);
  font-weight: 700;
  color: var(--side-ink);
  letter-spacing: -0.025em;
  white-space: nowrap;
}

.brand-subtitle {
  display: block;
  font-size: var(--fs-xs);
  color: var(--side-muted);
  white-space: nowrap;
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--sp-6);
  height: var(--sp-6);
  flex-shrink: 0;
  background: none;
  border: none;
  border-radius: var(--r-sm);
  color: var(--side-muted);
  cursor: pointer;
}

.toggle-btn:hover {
  background: var(--side-hover);
  color: var(--side-ink);
}

.chevron {
  width: var(--sp-4);
  height: var(--sp-4);
  transition: transform 0.2s ease;
}

.chevron.flipped {
  transform: rotate(180deg);
}

.nav {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-3);
  flex: 1;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-sm);
  color: var(--side-muted);
  text-decoration: none;
  font-size: var(--fs-base);
  font-weight: 500;
  white-space: nowrap;
}

.sidebar.collapsed .nav-link {
  justify-content: center;
  padding: var(--sp-2);
}

.nav-link:hover {
  background: var(--side-hover);
  color: var(--side-ink);
}

.nav-link[aria-current='page'] {
  background: var(--side-hover);
  color: var(--blue);
}

.nav-icon {
  width: var(--sp-5);
  height: var(--sp-5);
  flex-shrink: 0;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.footer {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  padding: var(--sp-3);
  border-top: 1px solid var(--side-border);
  /* No overflow rule: this is the exact spot ProfileMenu's 280px dropdown
     must be free to escape a 64px collapsed rail. */
}
</style>

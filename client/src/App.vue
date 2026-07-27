<template>
  <div class="app" :class="{ 'sidebar-collapsed': isCollapsed, 'sidebar-overlay': isOverlay }">
    <AppSidebar
      @show-profile-details="showProfileDetails = true"
      @show-tasks="showTasks = true"
    />

    <div class="app-main">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useSidebar } from './composables/useSidebar'
import AppSidebar from './components/AppSidebar.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'

export default {
  name: 'App',
  components: {
    AppSidebar,
    FilterBar,
    ProfileDetailsModal,
    TasksModal
  },
  setup() {
    const { currentUser } = useAuth()
    const { isCollapsed, isOverlay } = useSidebar()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      isCollapsed,
      isOverlay,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--canvas);
  color: var(--ink-2);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

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
</style>

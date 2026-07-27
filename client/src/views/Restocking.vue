<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="candidates.length === 0" class="card">
      <p class="empty-state">{{ t('restocking.noRecommendations') }}</p>
    </div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.availableBudget') }}</h3>
        </div>
        <div class="budget-body">
          <input
            type="range"
            class="budget-slider"
            v-model.number="budget"
            :min="0"
            :max="sliderMax"
            :step="sliderStep"
          />
          <div class="budget-range-labels">
            <span>{{ formatCurrency(0, currentCurrency) }}</span>
            <span>{{ formatCurrency(sliderMax, currentCurrency) }}</span>
          </div>
          <div class="budget-stats">
            <div class="budget-stat">
              <div class="budget-stat-label">{{ t('restocking.availableBudget') }}</div>
              <div class="budget-stat-value">{{ formatCurrency(budget, currentCurrency) }}</div>
            </div>
            <div class="budget-stat">
              <div class="budget-stat-label">{{ t('restocking.allocated') }}</div>
              <div class="budget-stat-value">{{ formatCurrency(allocated, currentCurrency) }}</div>
            </div>
            <div class="budget-stat">
              <div class="budget-stat-label">{{ t('restocking.remaining') }}</div>
              <div class="budget-stat-value">{{ formatCurrency(remaining, currentCurrency) }}</div>
            </div>
          </div>
          <p class="budget-meta">
            {{ t('restocking.itemsSelected', { count: selectedItems.length, total: candidates.length }) }}
          </p>
          <p class="budget-meta">
            {{ t('restocking.totalToRestockAll', { amount: formatCurrency(totalLineCost, currentCurrency) }) }}
          </p>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.onHand') }}</th>
                <th>{{ t('restocking.table.forecastChange') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
                <th>{{ t('restocking.table.urgency') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in candidates"
                :key="item.sku"
                :class="{ 'row-selected': isSelected(item.sku), 'row-dimmed': !isSelected(item.sku) }"
              >
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td>{{ translateWarehouse(item.warehouse) }}</td>
                <td>
                  <span :class="{ 'stock-below': item.quantity_on_hand < item.reorder_point }">
                    {{ item.quantity_on_hand }} / {{ item.reorder_point }}
                  </span>
                </td>
                <td>
                  <span :style="{ color: getGrowthColor(item.growth_pct) }">
                    {{ formatGrowth(item.growth_pct) }}%
                  </span>
                </td>
                <td><strong>{{ item.recommended_quantity }}</strong></td>
                <td>{{ formatCurrency(item.unit_cost, currentCurrency) }}</td>
                <td>{{ formatCurrency(item.line_cost, currentCurrency) }}</td>
                <td>{{ t('restocking.daysCount', { days: item.lead_time_days }) }}</td>
                <td>
                  <span :class="['badge', urgencyClass(item.urgency)]">
                    {{ t('restocking.urgencyLabel.' + item.urgency) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="candidates.length > 0 && selectedItems.length === 0" class="table-caption">
          {{ t('restocking.noneInBudget') }}
        </p>
        <p v-else-if="dimmedCount > 0" class="table-caption">
          {{ t('restocking.skippedNote') }}
        </p>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.placeOrder') }}</h3>
        </div>
        <div class="place-order-body">
          <button
            class="place-order-btn"
            :disabled="selectedItems.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
          <p v-if="orderMessage" :class="['order-message', orderMessageType]">{{ orderMessage }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const candidates = ref([])

    // Budget is kept in USD internally; only converted for display.
    const budget = ref(0)
    const budgetInitialized = ref(false)

    const submitting = ref(false)
    const orderMessage = ref('')
    const orderMessageType = ref('')

    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const totalLineCost = computed(() => {
      return candidates.value.reduce((sum, item) => sum + item.line_cost, 0)
    })

    // Round up to a "clean" number based on magnitude, e.g. 12345 -> 20000
    const niceCeil = (value) => {
      if (value <= 0) return 0
      const magnitude = Math.pow(10, Math.floor(Math.log10(value)))
      return Math.ceil(value / magnitude) * magnitude
    }

    const sliderMax = computed(() => niceCeil(totalLineCost.value))
    const sliderStep = computed(() => Math.max(1, Math.round(sliderMax.value / 100)))

    // Client-side only: walk the already-sorted (most-urgent-first) candidate
    // list and greedily fit as many items as possible into the budget,
    // skipping (not stopping on) items that don't fit so cheaper urgent
    // items later in the list still get picked up.
    const selection = computed(() => {
      let allocated = 0
      const selectedSkus = new Set()
      const selectedItems = []

      for (const item of candidates.value) {
        if (allocated + item.line_cost <= budget.value) {
          allocated += item.line_cost
          selectedSkus.add(item.sku)
          selectedItems.push(item)
        }
      }

      return { selectedSkus, selectedItems, allocated }
    })

    const selectedSkus = computed(() => selection.value.selectedSkus)
    const selectedItems = computed(() => selection.value.selectedItems)
    const allocated = computed(() => selection.value.allocated)
    const remaining = computed(() => Math.max(budget.value - allocated.value, 0))
    const dimmedCount = computed(() => candidates.value.length - selectedItems.value.length)

    const isSelected = (sku) => selectedSkus.value.has(sku)

    const loadCandidates = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()

        // Restock candidates only support warehouse/category filters.
        candidates.value = await api.getRestockCandidates({
          warehouse: filters.warehouse,
          category: filters.category
        })

        if (!budgetInitialized.value && sliderMax.value > 0) {
          budget.value = Math.round(sliderMax.value * 0.3)
          budgetInitialized.value = true
        }
      } catch (err) {
        error.value = 'Failed to load restock candidates: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch only warehouse/category - period and status have no meaning here.
    watch([selectedLocation, selectedCategory], () => {
      loadCandidates()
    })

    watch(budget, () => {
      orderMessage.value = ''
      orderMessageType.value = ''
    })

    const placeOrder = async () => {
      if (selectedItems.value.length === 0 || submitting.value) return

      submitting.value = true
      orderMessage.value = ''
      orderMessageType.value = ''

      try {
        const order = await api.createRestockOrder({
          budget: budget.value,
          items: selectedItems.value.map(item => ({ sku: item.sku, quantity: item.recommended_quantity }))
        })
        orderMessage.value = t('restocking.orderPlaced', { orderNumber: order.order_number })
        orderMessageType.value = 'success'
        await loadCandidates()
      } catch (err) {
        orderMessage.value = t('restocking.orderFailed')
        orderMessageType.value = 'error'
        console.error('Failed to place restock order:', err)
      } finally {
        submitting.value = false
      }
    }

    const getGrowthColor = (pct) => {
      if (Math.abs(pct) <= 2) return '#3b82f6' // Blue for near-zero change
      return pct > 0 ? '#10b981' : '#ef4444'
    }

    const formatGrowth = (pct) => {
      const rounded = Number(pct).toFixed(1)
      return pct > 0 ? `+${rounded}` : `${rounded}`
    }

    const urgencyClass = (urgency) => {
      const map = { critical: 'danger', watch: 'warning', healthy: 'success' }
      return map[urgency] || 'info'
    }

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    onMounted(loadCandidates)

    return {
      t,
      currentCurrency,
      loading,
      error,
      candidates,
      budget,
      sliderMax,
      sliderStep,
      allocated,
      remaining,
      totalLineCost,
      selectedItems,
      dimmedCount,
      isSelected,
      submitting,
      orderMessage,
      orderMessageType,
      placeOrder,
      getGrowthColor,
      formatGrowth,
      urgencyClass,
      translateCategory,
      translateProductName,
      translateWarehouse,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.budget-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: -0.5rem;
}

.budget-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-top: 0.5rem;
}

.budget-stat {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.875rem 1rem;
}

.budget-stat-label {
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.375rem;
}

.budget-stat-value {
  font-size: 1.375rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-meta {
  color: #64748b;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.row-selected {
  background: #f0fdf4;
}

.row-dimmed {
  opacity: 0.45;
}

.stock-below {
  color: #dc2626;
  font-weight: 600;
}

.table-caption {
  margin-top: 0.875rem;
  color: #64748b;
  font-size: 0.813rem;
  font-style: italic;
}

.place-order-body {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.order-message {
  font-size: 0.938rem;
  font-weight: 500;
}

.order-message.success {
  color: #059669;
}

.order-message.error {
  color: #dc2626;
}
</style>

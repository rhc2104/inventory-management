<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="isEmpty" class="empty-state">{{ t('reports.noData') }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterlyPerformance') }}</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('reports.table.quarter') }}</th>
                <th>{{ t('reports.table.totalOrders') }}</th>
                <th>{{ t('reports.table.totalRevenue') }}</th>
                <th>{{ t('reports.table.avgOrderValue') }}</th>
                <th>{{ t('reports.table.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ formatQuarter(q.quarter) }}</strong></td>
                <td>{{ q.total_orders }}</td>
                <td>{{ money(q.total_revenue) }}</td>
                <td>{{ money(q.avg_order_value) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyRevenueTrend') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="m in monthlyData" :key="m.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(m.revenue) + 'px' }"
                  :title="money(m.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(m.month) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthOverMonth') }}</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('reports.table.month') }}</th>
                <th>{{ t('reports.table.orders') }}</th>
                <th>{{ t('reports.table.revenue') }}</th>
                <th>{{ t('reports.table.change') }}</th>
                <th>{{ t('reports.table.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(m, index) in monthlyData" :key="m.month">
                <td><strong>{{ formatMonth(m.month) }}</strong></td>
                <td>{{ m.order_count }}</td>
                <td>{{ money(m.revenue) }}</td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(m.revenue, monthlyData[index - 1].revenue)">
                    {{ getChangeValue(m.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>—</span>
                </td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(m.revenue, monthlyData[index - 1].revenue)">
                    {{ getGrowthRate(m.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.totalRevenueYtd') }}</div>
          <div class="stat-value">{{ money(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ money(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.totalOrdersYtd') }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.bestQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

// Tallest bar in the chart, in px. Mirrors .bar-container's fixed height.
const MAX_BAR_PX = 200

export default {
  name: 'Reports',
  setup() {
    const { t, currentLocale, currentCurrency } = useI18n()
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()

        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])

        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        error.value = t('reports.loadError')
        console.error('Failed to load reports:', err)
      } finally {
        loading.value = false
      }
    }

    // Reports aggregate orders, and orders honour all four filters — unlike the
    // inventory-backed views, which have no time dimension.
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], loadData)

    const isEmpty = computed(() => quarterlyData.value.length === 0 && monthlyData.value.length === 0)

    const money = (amount) => formatCurrency(amount, currentCurrency.value)

    const formatMonth = (monthStr) => {
      const [year, month] = String(monthStr).split('-')
      const key = MONTH_KEYS[parseInt(month, 10) - 1]
      if (!key) return monthStr

      const shortMonth = t(`months.${key}`)
      // Japanese dates read largest unit first, and its months.* values already
      // carry the 月 suffix, so the same key serves both orderings.
      return currentLocale.value === 'ja' ? `${year}年${shortMonth}` : `${shortMonth} ${year}`
    }

    const formatQuarter = (quarterStr) => {
      // API label is "Q<N>-<YYYY>"; both locales reorder it, so never render it raw.
      const [quarter, year] = String(quarterStr).split('-')
      if (!year) return quarterStr
      return currentLocale.value === 'ja'
        ? `${year}年第${quarter.replace('Q', '')}四半期`
        : `${quarter} ${year}`
    }

    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.revenue, 0)
    )

    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length ? totalRevenue.value / monthlyData.value.length : 0
    )

    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.order_count, 0)
    )

    const bestQuarter = computed(() => {
      const best = quarterlyData.value.reduce(
        (top, q) => (top === null || q.total_revenue > top.total_revenue ? q : top),
        null
      )
      return best ? formatQuarter(best.quarter) : '—'
    })

    // Computed rather than rescanned per bar: getBarHeight runs once per month,
    // and the old inline scan made rendering the chart O(n²).
    const maxRevenue = computed(() =>
      monthlyData.value.reduce((max, m) => Math.max(max, m.revenue), 0)
    )

    const getBarHeight = (revenue) => {
      if (maxRevenue.value === 0) return 0
      return (revenue / maxRevenue.value) * MAX_BAR_PX
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    const getChangeValue = (current, previous) => {
      const delta = current - previous
      if (delta === 0) return '—'
      // Sign stays outside formatCurrency so the currency symbol keeps its place.
      const sign = delta > 0 ? '+' : '−'
      return sign + money(Math.abs(delta))
    }

    const getChangeClass = (current, previous) => {
      const delta = current - previous
      if (delta > 0) return 'positive-change'
      if (delta < 0) return 'negative-change'
      return ''
    }

    const getGrowthRate = (current, previous) => {
      if (previous === 0) return t('reports.notAvailable')
      const rate = ((current - previous) / previous) * 100
      // Same typographic minus as getChangeValue: toFixed() would emit an ASCII
      // hyphen, leaving the two adjacent columns visibly mismatched.
      const sign = rate > 0 ? '+' : rate < 0 ? '−' : ''
      return `${sign}${Math.abs(rate).toFixed(1)}%`
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      isEmpty,
      quarterlyData,
      monthlyData,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      money,
      formatMonth,
      formatQuarter,
      getBarHeight,
      getFulfillmentClass,
      getChangeValue,
      getChangeClass,
      getGrowthRate
    }
  }
}
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: var(--sp-6);
  color: var(--muted);
  font-size: var(--fs-base);
}

.chart-container {
  padding: var(--sp-6) var(--sp-4);
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: var(--sp-2);
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: var(--blue);
  border-radius: var(--r-sm) var(--r-sm) 0 0;
  transition: background 0.2s ease;
  cursor: pointer;
}

.bar:hover {
  background: color-mix(in srgb, var(--blue) 85%, black);
}

.bar-label {
  margin-top: var(--sp-5);
  font-size: var(--fs-xs);
  color: var(--muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
}

.positive-change {
  color: var(--green);
  font-weight: 600;
}

.negative-change {
  color: var(--red);
  font-weight: 600;
}
</style>

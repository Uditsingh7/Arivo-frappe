<script setup>
import { ref, onMounted, computed } from 'vue'
import { useCollectionsStore } from '@/store/collections.js'
import ReminderModal from '@/components/ReminderModal.vue'
import PromiseBadge from '@/components/PromiseBadge.vue'
import LogPromiseModal from '@/components/LogPromiseModal.vue'
import { getPromiseStatus, getDailyBriefing } from '@/utils/api.js'

const store = useCollectionsStore()

const promiseMap = ref({})
const activePromiseInvoice = ref(null)
const briefing = ref(null)
const briefingLoading = ref(false)

const totalPages = computed(() =>
  Math.max(1, Math.ceil(store.totalCount / store.pageSize))
)

async function loadPromises() {
  promiseMap.value = {}
  if (!Array.isArray(store.invoices)) return
  for (const inv of store.invoices) {
    const res = await getPromiseStatus(inv.invoice)
    if (res?.message) promiseMap.value[inv.invoice] = res.message
  }
}

async function loadBriefing() {
  briefingLoading.value = true
  try {
    const res = await getDailyBriefing()
    briefing.value = res.message || res
  } finally {
    briefingLoading.value = false
  }
}

function fmt(amount) {
  return `AED ${Number(amount || 0).toLocaleString('en', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`
}

function timeAgo(dateStr) {
  const diffDays = Math.floor((Date.now() - new Date(dateStr)) / 86400000)
  if (diffDays <= 0) return 'today'
  if (diffDays === 1) return '1 day ago'
  return `${diffDays} days ago`
}

function overdueClass(days) {
  if (days >= 30) return 'text-red-600 font-semibold'
  if (days >= 15) return 'text-amber-600 font-medium'
  if (days >= 7)  return 'text-blue-600 font-medium'
  return 'text-gray-500'
}

function priorityClass(priority) {
  const map = {
    Critical: 'bg-red-100 text-red-600',
    High: 'bg-amber-100 text-amber-600',
    Medium: 'bg-blue-100 text-blue-600',
    Low: 'bg-gray-100 text-gray-500',
  }
  return map[priority] || 'bg-gray-100 text-gray-500'
}

async function onPromiseSaved(invoiceName) {
  const res = await getPromiseStatus(invoiceName)
  if (res?.message) promiseMap.value[invoiceName] = res.message
}

function attentionLabel(type) {
  switch (type) {
    case 'broken_promises':   return 'Broken promises'
    case 'no_contact_gt_10d': return 'No contact > 10 days'
    case 'newly_30_plus':     return 'Newly 30+ days'
    case 'never_contacted':   return 'Never contacted'
    default:                  return 'All'
  }
}

async function setAttention(type) {
  await store.setAttentionType(type)
  await loadPromises()
}

async function goNextPage() {
  await store.nextPage()
  await loadPromises()
}

async function goPrevPage() {
  await store.prevPage()
  await loadPromises()
}

onMounted(async () => {
  await store.fetchAll()
  await loadPromises()
  await loadBriefing()
})
</script>

<template>
  <div class="flex flex-col gap-5">

    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">Collections Board</h1>
        <p class="text-sm text-gray-400 mt-0.5">Arivo · AR Collections Copilot</p>
      </div>
      <button
        class="text-sm text-gray-500 border border-gray-200 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
        @click="async () => { await store.fetchAll(); await loadPromises(); await loadBriefing(); }"
      >
        Refresh
      </button>
    </div>

    <!-- Today's Workload — commanding block -->
    <div class="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4">
      <p class="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-2">Today's workload</p>
      <p v-if="briefingLoading" class="text-sm text-amber-600">Calculating…</p>
      <template v-else-if="briefing">
        <div class="flex flex-col gap-1">
          <button
            v-if="briefing.broken_promises.count > 0"
            class="text-left text-sm text-amber-900 hover:text-amber-700 transition-colors"
            @click="setAttention('broken_promises')"
          >
            ⚠ <span class="font-semibold">{{ briefing.broken_promises.count }} invoices with broken promises</span>
            — {{ fmt(briefing.broken_promises.amount) }} at risk · <span class="underline text-xs">View →</span>
          </button>
          <button
            v-if="briefing.no_contact_gt_10d.count > 0"
            class="text-left text-sm text-amber-900 hover:text-amber-700 transition-colors"
            @click="setAttention('no_contact_gt_10d')"
          >
            · <span class="font-semibold">{{ briefing.no_contact_gt_10d.count }} invoices with no contact in 10+ days</span>
            — {{ fmt(briefing.no_contact_gt_10d.amount) }} going cold · <span class="underline text-xs">View →</span>
          </button>
          <button
            v-if="briefing.newly_30_plus.count > 0"
            class="text-left text-sm text-amber-900 hover:text-amber-700 transition-colors"
            @click="setAttention('newly_30_plus')"
          >
            · <span class="font-semibold">{{ briefing.newly_30_plus.count }} invoices newly crossed 30 days overdue</span>
            — {{ fmt(briefing.newly_30_plus.amount) }} just turned critical · <span class="underline text-xs">View →</span>
          </button>
          <p
            v-if="briefing.broken_promises.count === 0 && briefing.no_contact_gt_10d.count === 0 && briefing.newly_30_plus.count === 0"
            class="text-sm text-amber-700"
          >
            No urgent actions today.
          </p>
        </div>
      </template>
      <p v-else class="text-sm text-amber-600">No briefing data available.</p>
    </div>

    <!-- Stat cards -->
    <div class="grid grid-cols-4 gap-4">
      <div class="bg-white rounded-lg border border-gray-200 p-5">
        <p class="text-xs font-medium text-gray-400 uppercase tracking-wide">Total Overdue</p>
        <p class="text-2xl font-bold text-gray-900 mt-2">{{ fmt(store.totalOutstanding) }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ store.totalCount }} invoices</p>
      </div>
      <div class="bg-white rounded-lg border border-gray-200 p-5">
        <p class="text-xs font-medium text-gray-400 uppercase tracking-wide">Critical (30+ days)</p>
        <p class="text-2xl font-bold text-red-600 mt-2">{{ fmt(store.criticalAmount) }}</p>
      </div>
      <div class="bg-white rounded-lg border border-gray-200 p-5">
        <p class="text-xs font-medium text-gray-400 uppercase tracking-wide">High (15–29 days)</p>
        <p class="text-2xl font-bold text-amber-500 mt-2">{{ fmt(store.highAmount) }}</p>
      </div>
      <div class="bg-white rounded-lg border border-gray-200 p-5">
        <p class="text-xs font-medium text-gray-400 uppercase tracking-wide">Medium (7–14 days)</p>
        <p class="text-2xl font-bold text-blue-600 mt-2">{{ fmt(store.mediumAmount) }}</p>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">

      <!-- Table header bar -->
      <div class="px-5 py-3 border-b border-gray-200 flex items-center justify-between gap-4">

        <!-- Focus filters -->
        <div class="flex flex-wrap gap-2 items-center">
          <span class="text-xs text-gray-400 mr-1">Focus:</span>
          <button
            v-for="type in ['all','broken_promises','no_contact_gt_10d','newly_30_plus','never_contacted']"
            :key="type"
            @click="setAttention(type)"
            :class="[
              'px-3 py-1 rounded-full text-xs font-medium border transition-colors',
              store.attentionType === type
                ? 'bg-gray-900 text-white border-gray-900'
                : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
            ]"
          >
            {{ attentionLabel(type) }}
          </button>
        </div>

        <!-- Pagination -->
        <div class="flex items-center gap-2 text-xs text-gray-500 shrink-0">
          <button
            class="px-2 py-1 border border-gray-200 rounded disabled:opacity-40 hover:bg-gray-50"
            :disabled="store.page <= 1"
            @click="goPrevPage"
          >
            ← Prev
          </button>
          <span class="text-gray-400">Page {{ store.page }} of {{ totalPages }}</span>
          <button
            class="px-2 py-1 border border-gray-200 rounded disabled:opacity-40 hover:bg-gray-50"
            :disabled="store.page >= totalPages"
            @click="goNextPage"
          >
            Next →
          </button>
        </div>
      </div>

      <div v-if="store.loading" class="p-12 text-center text-sm text-gray-400">Loading invoices...</div>
      <div v-else-if="store.error" class="p-12 text-center text-sm text-red-500">{{ store.error }}</div>
      <div v-else-if="!store.invoices.length" class="p-12 text-center text-sm text-gray-400">
        No invoices match this filter.
      </div>

      <table v-else class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-200">
            <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Customer</th>
            <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Due Date</th>
            <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Overdue</th>
            <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Amount</th>
            <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Priority</th>
            <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Last Action</th>
            <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Promise</th>
            <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="inv in store.invoices"
            :key="inv.invoice"
            class="border-t border-gray-100 hover:bg-gray-50 transition-colors"
          >
            <!-- Customer — invoice ID as muted subline -->
            <td class="px-5 py-3">
              <p class="text-sm font-medium text-gray-900">{{ inv.customer_name }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ inv.invoice }}</p>
            </td>

            <td class="px-5 py-3 text-sm text-gray-600">{{ inv.due_date }}</td>

            <!-- Overdue days — color intensity by severity -->
            <td class="px-5 py-3">
              <span :class="['text-sm', overdueClass(inv.days_overdue)]">
                {{ inv.days_overdue }}d
              </span>
            </td>

            <td class="px-5 py-3 text-sm font-medium text-gray-900">{{ fmt(inv.outstanding_amount) }}</td>

            <td class="px-5 py-3">
              <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', priorityClass(inv.priority)]">
                {{ inv.priority }}
              </span>
            </td>

            <td class="px-5 py-3 text-xs">
              <span v-if="inv.last_action" class="text-blue-600 font-medium">
                ✉ {{ inv.reminder_count }}× · {{ timeAgo(inv.last_action.creation) }}
              </span>
              <span v-else class="text-gray-400">—</span>
            </td>

            <td class="px-5 py-3 text-xs">
              <div class="flex flex-col gap-1 items-start">
                <PromiseBadge :promise="promiseMap[inv.invoice]" />
                <button
                  @click="activePromiseInvoice = inv.invoice"
                  class="text-xs text-indigo-500 hover:underline"
                >
                  + Log
                </button>
              </div>
            </td>

            <td class="px-5 py-3">
              <button
                :disabled="store.drafting === inv.invoice"
                :class="[
                  'text-xs font-medium px-3 py-1.5 rounded-md border transition-colors',
                  inv.last_action
                    ? 'border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-40'
                    : 'border-blue-600 text-blue-600 hover:bg-blue-50 disabled:opacity-40'
                ]"
                @click="store.draftReminder(inv.invoice)"
              >
                {{ store.drafting === inv.invoice ? 'Drafting…' : inv.last_action ? 'Follow Up' : 'Draft Reminder' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>

  <ReminderModal
    v-model="store.modalOpen"
    :draft="store.reminderDraft"
    :sending="store.sending"
    @send="store.sendReminder"
  />

  <LogPromiseModal
    v-if="activePromiseInvoice"
    :invoice-name="activePromiseInvoice"
    @close="activePromiseInvoice = null"
    @saved="onPromiseSaved(activePromiseInvoice)"
  />
</template>

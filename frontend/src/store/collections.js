import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { call, getOverdueInvoicesPaged, getArSummary } from '@/utils/api.js'

export const useCollectionsStore = defineStore('collections', () => {
  const invoices = ref([])
  const summary = ref({})
  const loading = ref(false)
  const error = ref(null)

  const reminderDraft = ref(null)
  const modalOpen = ref(false)
  const drafting = ref(null)
  const sending = ref(false)

  const page = ref(1)
  const pageSize = ref(50)
  const totalCount = ref(0)
  const attentionType = ref('all')

  async function fetchSummary() {
    try {
      summary.value = await getArSummary()
    } catch (e) {
      console.error('Summary fetch failed:', e)
    }
  }

  async function fetchInvoices() {
    loading.value = true
    error.value = null
    try {
      const payload = await getOverdueInvoicesPaged({
        page: page.value,
        pageSize: pageSize.value,
        attentionType: attentionType.value,
      })
      invoices.value = payload?.invoices || []
      totalCount.value = payload?.total_count || 0
      page.value = payload?.page || 1
      pageSize.value = payload?.page_size || pageSize.value
    } catch (e) {
      error.value = 'Failed to load invoices'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchAll() {
    await Promise.all([fetchSummary(), fetchInvoices()])
  }

  async function setAttentionType(type) {
    attentionType.value = type
    page.value = 1
    await fetchInvoices()
  }

  function nextPage() {
    const totalPages = Math.max(1, Math.ceil(totalCount.value / pageSize.value))
    if (page.value < totalPages) {
      page.value += 1
      return fetchInvoices()
    }
  }

  function prevPage() {
    if (page.value > 1) {
      page.value -= 1
      return fetchInvoices()
    }
  }

  async function draftReminder(invoiceName) {
    drafting.value = invoiceName
    try {
      const result = await call('arivo.arivo.api.ai.draft_reminder', {
        invoice_name: invoiceName,
      })
      reminderDraft.value = result
      modalOpen.value = true
    } catch (e) {
      error.value = 'Failed to draft reminder. Check API key.'
      console.error(e)
    } finally {
      drafting.value = null
    }
  }

  async function sendReminder({ subject, body, customer_email }) {
    sending.value = true
    try {
      await call('arivo.arivo.api.ai.send_reminder', {
        invoice_name: reminderDraft.value.invoice,
        subject,
        body,
        customer_email,
      })
      modalOpen.value = false
      reminderDraft.value = null
      await fetchInvoices()
      return true
    } catch (e) {
      error.value = 'Failed to send reminder'
      console.error(e)
      return false
    } finally {
      sending.value = false
    }
  }

  const totalOutstanding = computed(() => summary.value?.total_outstanding || 0)
  const criticalAmount = computed(() => summary.value?.critical_amount || 0)
  const highAmount = computed(() => summary.value?.high_amount || 0)
  const mediumAmount = computed(() => summary.value?.medium_amount || 0)

  return {
    invoices, summary, loading, error,
    reminderDraft, modalOpen, drafting, sending,
    page, pageSize, totalCount, attentionType,
    fetchAll, fetchInvoices, fetchSummary,
    setAttentionType, nextPage, prevPage,
    draftReminder, sendReminder,
    totalOutstanding, criticalAmount, highAmount, mediumAmount,
  }
})

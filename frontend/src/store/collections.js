import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { call } from '@/utils/api.js'

export const useCollectionsStore = defineStore('collections', () => {
    const invoices = ref([])
    const summary = ref({})
    const loading = ref(false)
    const error = ref(null)

    const reminderDraft = ref(null)
    const modalOpen = ref(false)
    const drafting = ref(null)
    const sending = ref(false)

    async function fetchSummary() {
        try {
            summary.value = await call('arivo.arivo.api.collections.get_ar_summary')
        } catch(e) {
            console.error('Summary fetch failed:', e)
        }
    }

    async function fetchInvoices() {
        loading.value = true
        error.value = null
        try {
            invoices.value = await call('arivo.arivo.api.collections.get_overdue_invoices')
        } catch(e) {
            error.value = 'Failed to load invoices'
            console.error(e)
        } finally {
            loading.value = false
        }
    }

    async function fetchAll() {
        await Promise.all([fetchSummary(), fetchInvoices()])
    }

    async function draftReminder(invoiceName) {
        drafting.value = invoiceName
        try {
            const result = await call('arivo.arivo.api.ai.draft_reminder', {
                invoice_name: invoiceName
            })
            reminderDraft.value = result
            modalOpen.value = true
        } catch(e) {
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
                customer_email
            })
            modalOpen.value = false
            reminderDraft.value = null
            await fetchInvoices()
            return true
        } catch(e) {
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
        fetchAll, fetchInvoices, fetchSummary,
        draftReminder, sendReminder,
        totalOutstanding, criticalAmount, highAmount, mediumAmount
    }
})

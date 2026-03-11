<script setup>
import { onMounted } from 'vue'
import { useCollectionsStore } from '@/store/collections.js'
import ReminderModal from '@/components/ReminderModal.vue'

const store = useCollectionsStore()

function fmt(amount) {
    return `AED ${Number(amount || 0).toLocaleString('en', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })}`
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

onMounted(() => store.fetchAll())
</script>

<template>
    <div class="flex flex-col gap-6">

        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-xl font-semibold text-gray-900">Collections Board</h1>
                <p class="text-sm text-gray-500 mt-0.5">AI-powered AR Collections Copilot</p>
            </div>
            <button
                class="text-sm text-gray-500 border border-gray-200 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                @click="store.fetchAll()"
            >
                Refresh
            </button>
        </div>

        <div class="grid grid-cols-4 gap-4">
            <div class="bg-white rounded-lg border border-gray-200 p-5">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wide">Total Overdue</p>
                <p class="text-2xl font-bold text-gray-900 mt-2">{{ fmt(store.totalOutstanding) }}</p>
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

        <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <h2 class="text-sm font-semibold text-gray-900">Today's Collections Board</h2>
                <span class="text-xs text-gray-400">{{ store.invoices.length }} invoices need attention</span>
            </div>

            <div v-if="store.loading" class="p-12 text-center text-sm text-gray-400">Loading invoices...</div>
            <div v-else-if="store.error" class="p-12 text-center text-sm text-red-500">{{ store.error }}</div>
            <div v-else-if="!store.invoices.length" class="p-12 text-center text-sm text-gray-400">No overdue invoices. Great job!</div>

            <table v-else class="w-full">
                <thead>
                    <tr class="bg-gray-50 border-b border-gray-200">
                        <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Customer</th>
                        <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Invoice</th>
                        <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Due Date</th>
                        <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Overdue</th>
                        <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Amount</th>
                        <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Priority</th>
                        <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Last Action</th>
                        <th class="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Action</th>
                    </tr>
                </thead>
                <tbody>
                    <tr
                        v-for="inv in store.invoices"
                        :key="inv.invoice"
                        class="border-t border-gray-100 hover:bg-gray-50 transition-colors"
                    >
                        <td class="px-5 py-4 text-sm font-medium text-gray-900">{{ inv.customer_name }}</td>
                        <td class="px-5 py-4 text-xs text-gray-400">{{ inv.invoice }}</td>
                        <td class="px-5 py-4 text-sm text-gray-600">{{ inv.due_date }}</td>
                        <td class="px-5 py-4 text-sm font-medium text-gray-900">{{ inv.days_overdue }} days</td>
                        <td class="px-5 py-4 text-sm font-medium text-gray-900">{{ fmt(inv.outstanding_amount) }}</td>
                        <td class="px-5 py-4">
                            <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', priorityClass(inv.priority)]">
                                {{ inv.priority }}
                            </span>
                        </td>
                        <td class="px-5 py-4 text-xs text-gray-400">
                            {{ inv.last_reminder ? inv.last_reminder.reminder_type + ' sent' : 'Not contacted' }}
                        </td>
                        <td class="px-5 py-4">
                            <button
                                :disabled="store.drafting === inv.invoice"
                                class="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-xs font-medium px-4 py-2 rounded-lg transition-colors"
                                @click="store.draftReminder(inv.invoice)"
                            >
                                {{ store.drafting === inv.invoice ? 'Drafting...' : 'Draft Reminder' }}
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
</template>

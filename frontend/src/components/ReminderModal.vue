<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" @click.self="$emit('update:modelValue', false)">
      <div class="bg-white rounded-xl w-[620px] max-w-[95vw] p-7 shadow-2xl">

        <div class="flex items-center gap-3 mb-5">
          <h3 class="text-base font-semibold text-gray-900">AI Drafted Reminder</h3>
          <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', toneClass]">{{ draft?.tone }}</span>
        </div>

        <div class="bg-gray-50 rounded-lg p-4 mb-5 text-sm text-gray-600 leading-7">
          <span class="font-semibold text-gray-900">Customer:</span> {{ draft?.customer }}<br />
          <span class="font-semibold text-gray-900">Invoice:</span> {{ draft?.invoice }}<br />
          <span class="font-semibold text-gray-900">Amount:</span> {{ fmt(draft?.amount, draft?.currency) }}<br />
          <span class="font-semibold text-gray-900">Days Overdue:</span> {{ draft?.days_overdue }} days
        </div>

        <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Subject</label>
        <input v-model="form.subject" type="text" class="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500" />

        <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Email Body</label>
        <textarea v-model="form.body" class="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 mb-4 h-44 resize-y focus:outline-none focus:ring-2 focus:ring-blue-500" />

        <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Send To (Email)</label>
        <input v-model="form.email" type="email" placeholder="customer@example.com" class="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 mb-6 focus:outline-none focus:ring-2 focus:ring-blue-500" />

        <div class="flex gap-3 justify-end">
          <button class="bg-gray-100 text-gray-600 text-sm px-5 py-2 rounded-lg hover:bg-gray-200 transition-colors" @click="$emit('update:modelValue', false)">Cancel</button>
          <button :disabled="sending || !form.email" class="bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors" @click="handleSend">
            {{ sending ? 'Sending...' : 'Send Reminder' }}
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({ modelValue: Boolean, draft: Object, sending: Boolean })
const emit = defineEmits(['update:modelValue', 'send'])

const form = ref({ subject: '', body: '', email: '' })

watch(() => props.draft, (d) => {
    if (d) {
        form.value.subject = d.subject || ''
        form.value.body = d.body || ''
        form.value.email = d.customer_email && d.customer_email !== 'N/A' ? d.customer_email : ''
    }
}, { immediate: true })

const toneClass = computed(() => {
    const t = props.draft?.tone || ''
    if (t === 'Final Notice') return 'bg-red-100 text-red-700'
    if (t === 'Firm') return 'bg-amber-100 text-amber-700'
    return 'bg-green-100 text-green-700'
})

function fmt(amount, currency = 'AED') {
    return `${currency} ${Number(amount || 0).toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function handleSend() {
    if (!form.value.email) return
    emit('send', { ...form.value })
}
</script>

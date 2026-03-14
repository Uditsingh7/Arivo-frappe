<template>
  <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-xl p-6 w-96">
      <h3 class="text-lg font-semibold mb-4">📅 Log Payment Promise</h3>

      <label class="block text-sm text-gray-600 mb-1">Promise Date</label>
      <input type="date" v-model="promiseDate" class="w-full border rounded px-3 py-2 mb-3 text-sm" />

      <label class="block text-sm text-gray-600 mb-1">Amount (optional)</label>
      <input type="number" v-model="promiseAmount" placeholder="Leave blank for full amount"
        class="w-full border rounded px-3 py-2 mb-3 text-sm" />

      <label class="block text-sm text-gray-600 mb-1">Note (optional)</label>
      <textarea v-model="note" rows="2" placeholder="e.g. Customer confirmed over call"
        class="w-full border rounded px-3 py-2 mb-4 text-sm"></textarea>

      <div class="flex gap-2 justify-end">
        <button @click="$emit('close')" class="px-4 py-2 text-sm rounded border">Cancel</button>
        <button @click="submit" class="px-4 py-2 text-sm rounded bg-blue-600 text-white font-medium">Log Promise</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { logPromise } from '../utils/api'

const props = defineProps({ invoiceName: String, outstandingAmount: Number })
const emit = defineEmits(['close', 'saved'])

const promiseDate = ref('')
const promiseAmount = ref(null)
const note = ref('')

async function submit() {
  if (!promiseDate.value) return alert('Please select a date')
  await logPromise(props.invoiceName, promiseDate.value, promiseAmount.value, note.value)
  emit('saved')
  emit('close')
}
</script>

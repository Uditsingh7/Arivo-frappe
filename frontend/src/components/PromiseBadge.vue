<template>
  <span v-if="promise" :class="badgeClass">
    {{ badgeText }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ promise: Object })

const badgeClass = computed(() => ({
  'px-2 py-0.5 rounded text-xs font-medium': true,
  'bg-yellow-100 text-yellow-800': props.promise?.promise_status === 'Pending',
  'bg-red-100 text-red-700': props.promise?.promise_status === 'Broken',
  'bg-green-100 text-green-700': props.promise?.promise_status === 'Kept',
}))

const badgeText = computed(() => {
  if (props.promise?.promise_status === 'Broken') return '🔴 Broken Promise'
  if (props.promise?.promise_status === 'Kept') return '✅ Promise Kept'
  return `🟡 Promise: ${props.promise?.promise_date}`
})
</script>

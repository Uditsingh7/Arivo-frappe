function csrfToken() {
  return (
    window.frappe?.csrf_token ||
    document.cookie.split('; ').find(r => r.startsWith('X-Frappe-CSRF-Token='))?.split('=')[1] ||
    'fetch'
  )
}

export async function call(method, params = {}) {
  const response = await fetch(`/api/method/${method}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': csrfToken(),
    },
    credentials: 'include',
    body: JSON.stringify(params),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err?.exception || `API Error: ${response.status}`)
  }
  const data = await response.json()
  return data.message
}

export async function getOverdueInvoicesPaged({ page = 1, pageSize = 50, attentionType = 'all' } = {}) {
  return call('arivo.arivo.api.collections.get_overdue_invoices_paged', {
    page,
    page_size: pageSize,
    attention_type: attentionType,
  })
}

export async function getArSummary() {
  return call('arivo.arivo.api.collections.get_ar_summary')
}

export async function getDailyBriefing() {
  return call('arivo.arivo.api.collections.get_daily_briefing')
}

export async function getPromiseStatus(invoiceName) {
  return call('arivo.arivo.promise_utils.get_promise_status', {
    invoice_name: invoiceName,
  })
}

export async function logPromise(invoiceName, promiseDate, promiseAmount = null, note = '') {
  return call('arivo.arivo.promise_utils.log_promise', {
    invoice_name: invoiceName,
    promise_date: promiseDate,
    promise_amount: promiseAmount,
    note,
  })
}

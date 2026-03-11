export async function call(method, params = {}) {
    const csrfToken = 
        window.frappe?.csrf_token ||
        document.cookie.split('; ')
            .find(r => r.startsWith('X-Frappe-CSRF-Token='))
            ?.split('=')[1] || 'fetch'

    const response = await fetch(`/api/method/${method}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Frappe-CSRF-Token': csrfToken,
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

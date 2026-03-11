import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router/index.js'
import App from './App.vue'
import './index.css'

function mountArivo(el) {
    const app = createApp(App)
    app.use(createPinia())
    app.use(router)
    app.mount(el)
}

// Standalone dev mode
if (document.getElementById('app')) {
    mountArivo(document.getElementById('app'))
}

// Expose for Frappe Desk
window.mountArivo = mountArivo

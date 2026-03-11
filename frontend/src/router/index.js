import { createRouter, createWebHistory } from 'vue-router'
import CollectionsBoard from '@/pages/CollectionsBoard.vue'
import Settings from '@/pages/Settings.vue'

const routes = [
    {
        path: '/',
        name: 'CollectionsBoard',
        component: CollectionsBoard,
    },
    {
        path: '/settings',
        name: 'Settings',
        component: Settings,
    },
]

export default createRouter({
    history: createWebHistory('/arivo/'),
    routes,
})

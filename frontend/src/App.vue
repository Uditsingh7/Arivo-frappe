<template>
    <div class="min-h-screen bg-gray-50">
        <nav class="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
            <div class="flex items-center gap-8">
                <span class="text-xl font-bold text-blue-600">
                    Arivo<span class="text-amber-400">.</span>
                </span>
                <div class="flex gap-6">
                    <router-link
                        to="/"
                        class="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
                        active-class="text-blue-600"
                    >
                        Collections
                    </router-link>
                    <router-link
                        to="/settings"
                        class="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
                        active-class="text-blue-600"
                    >
                        Settings
                    </router-link>
                </div>
            </div>
            <span class="text-xs text-gray-400">AR Collections Copilot</span>
        </nav>
        <main class="px-8 py-6">
            <router-view />
        </main>
    </div>
</template>

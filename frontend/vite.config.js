import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: { '@': path.resolve(__dirname, 'src') },
    },
    server: {
        port: 8080,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
                secure: false,
            },
        },
    },
    build: {
        outDir: '../arivo/public/frontend',
        emptyOutDir: true,
        rollupOptions: {
            input: 'index.html',
            output: {
                entryFileNames: 'index.js',
                chunkFileNames: '[name].js',
                assetFileNames: '[name].[ext]',
            },
        },
    },
})

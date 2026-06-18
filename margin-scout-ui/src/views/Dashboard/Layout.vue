<template>
  <div class="dashboard-layout flex">
    <!-- サイドバー -->
    <div class="w-64 bg-gray-100 border-r min-h-screen flex flex-col">
      <div class="p-4 border-b">
        <h2 class="text-lg font-bold text-gray-800">ダッシュボード</h2>
      </div>
      <nav class="p-4 space-y-2">
        <router-link to="/dashboard" class="block px-4 py-2 rounded hover:bg-gray-200" :class="{ 'bg-blue-600 text-white': $route.path === '/dashboard' }">
          📊 概要
        </router-link>
        <router-link to="/dashboard/history" class="block px-4 py-2 rounded hover:bg-gray-200" :class="{ 'bg-blue-600 text-white': $route.path.includes('/dashboard/history') }">
          📋 取得履歴
        </router-link>
        <router-link to="/dashboard/items" class="block px-4 py-2 rounded hover:bg-gray-200" :class="{ 'bg-blue-600 text-white': $route.path.includes('/dashboard/items') }">
          💾 保存済み商品
        </router-link>
        <router-link to="/dashboard/saved-searches" class="block px-4 py-2 rounded hover:bg-gray-200" :class="{ 'bg-blue-600 text-white': $route.path.includes('/dashboard/saved-searches') }">
          🔍 保存済み検索
        </router-link>
        <router-link to="/dashboard/settings" class="block px-4 py-2 rounded hover:bg-gray-200" :class="{ 'bg-blue-600 text-white': $route.path === '/dashboard/settings' }">
          ⚙️ 設定
        </router-link>
      </nav>
      <div class="p-4 border-t mt-auto">
        <button @click="logout" class="w-full px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
          ログアウト
        </button>
      </div>
    </div>

    <!-- メインコンテンツ -->
    <div class="flex-1 p-8 bg-gray-50 min-h-screen">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router"
import { useAuthStore } from "../../stores/auth"

const router = useRouter()
const auth = useAuthStore()

const logout = () => {
  auth.logout()
  router.push("/auth/login")
}
</script>

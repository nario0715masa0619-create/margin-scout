<template>
  <div class="dashboard-home">
    <h1 class="text-3xl font-bold mb-6">ダッシュボード</h1>

    <!-- KPI カード -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="bg-white p-6 rounded-lg shadow">
        <p class="text-gray-600 text-sm font-semibold">月間取得件数</p>
        <p class="text-3xl font-bold text-blue-600 mt-2">{{ stats.monthlyCount }}</p>
        <p class="text-gray-500 text-xs mt-2">今月のインポート</p>
      </div>

      <div class="bg-white p-6 rounded-lg shadow">
        <p class="text-gray-600 text-sm font-semibold">マッチング成功率</p>
        <p class="text-3xl font-bold text-green-600 mt-2">{{ stats.matchSuccessRate }}%</p>
        <p class="text-gray-500 text-xs mt-2">eBay 照合結果</p>
      </div>

      <div class="bg-white p-6 rounded-lg shadow">
        <p class="text-gray-600 text-sm font-semibold">平均利益</p>
        <p class="text-3xl font-bold text-orange-600 mt-2">¥{{ formatNumber(stats.avgProfit) }}</p>
        <p class="text-gray-500 text-xs mt-2">直近 30 日</p>
      </div>
    </div>

    <!-- 最近のセッション -->
    <div class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-lg font-semibold mb-4">最近の取得セッション</h2>
      <div v-if="recentSessions.length === 0" class="text-center py-8 text-gray-500">
        取得セッションがありません
      </div>
      <table v-else class="w-full text-sm">
        <thead class="border-b">
          <tr>
            <th class="text-left py-2 px-4">ソース</th>
            <th class="text-left py-2 px-4">取得日</th>
            <th class="text-right py-2 px-4">件数</th>
            <th class="text-right py-2 px-4">マッチ</th>
            <th class="text-right py-2 px-4">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="session in recentSessions" :key="session.id" class="border-b hover:bg-gray-50">
            <td class="py-3 px-4">{{ sourceLabel(session.source) }}</td>
            <td class="py-3 px-4">{{ formatDate(session.created_at) }}</td>
            <td class="py-3 px-4 text-right">{{ session.item_count }}</td>
            <td class="py-3 px-4 text-right font-semibold">{{ session.matched_count }}</td>
            <td class="py-3 px-4 text-right">
              <router-link :to="`/dashboard/history/${session.id}`" class="text-blue-600 hover:underline">
                詳細
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { capturesAPI } from "../../services/api"

interface ImportSession {
  id: string
  source: string
  created_at: string
  item_count: number
  matched_count: number
  error_count: number
}

const stats = ref({
  monthlyCount: 0,
  matchSuccessRate: 0,
  avgProfit: 0,
})

const recentSessions = ref<ImportSession[]>([])

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString("ja-JP")
}

const formatNumber = (num: number) => num.toLocaleString()

const sourceLabel = (source: string) => {
  const labels: { [key: string]: string } = {
    mercari: "Mercari",
    yahoo_auction: "Yahoo Auction",
    yahoo_flea: "Yahoo Flea",
  }
  return labels[source] || source
}

onMounted(async () => {
  try {
    const response = await capturesAPI.getImportSessions(10)
    recentSessions.value = response.data.sessions

    // KPI 計算（簡略版）
    const totalItems = recentSessions.value.reduce((sum, s) => sum + s.item_count, 0)
    const totalMatched = recentSessions.value.reduce((sum, s) => sum + s.matched_count, 0)

    stats.value.monthlyCount = totalItems
    stats.value.matchSuccessRate = totalItems > 0 ? Math.round((totalMatched / totalItems) * 100) : 0
    stats.value.avgProfit = 0 // TODO: Backend から aggregated 値を取得
  } catch (error) {
    console.error("Failed to load dashboard:", error)
  }
})
</script>

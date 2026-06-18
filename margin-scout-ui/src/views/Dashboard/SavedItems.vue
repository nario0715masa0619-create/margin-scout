<template>
  <div class="saved-items">
    <h1 class="text-3xl font-bold mb-6">保存済み商品</h1>

    <!-- フィルタ・操作バー -->
    <div class="bg-white p-4 rounded-lg shadow mb-4 flex flex-wrap items-center gap-4">
      <input
        v-model="searchText"
        type="text"
        placeholder="商品名で検索"
        class="flex-1 min-w-48 px-3 py-2 border rounded"
      />
      <select v-model="filterSource" class="px-3 py-2 border rounded">
        <option value="">全てのソース</option>
        <option value="mercari">Mercari</option>
        <option value="yahoo_auction">Yahoo Auction</option>
        <option value="yahoo_flea">Yahoo Flea</option>
      </select>
      <select v-model="sortBy" class="px-3 py-2 border rounded">
        <option value="date_desc">最新順</option>
        <option value="profit_desc">利益（多い順）</option>
        <option value="margin_desc">利益率（高い順）</option>
      </select>

      <button
        v-if="selectedItems.length > 0"
        @click="exportCSV"
        :disabled="isExporting"
        class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
      >
        {{ isExporting ? "出力中..." : `CSV (${selectedItems.length}件)` }}
      </button>
    </div>

    <!-- 商品テーブル -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div v-if="filteredItems.length === 0" class="text-center py-8 text-gray-500">
        商品がありません
      </div>
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-100 border-b">
          <tr>
            <th class="px-4 py-3 text-left">
              <input
                type="checkbox"
                :checked="allSelected"
                @change="toggleSelectAll"
              />
            </th>
            <th class="px-4 py-3 text-left">商品名</th>
            <th class="px-4 py-3 text-left">ソース</th>
            <th class="px-4 py-3 text-right">フリマ価格</th>
            <th class="px-4 py-3 text-right">eBay価格</th>
            <th class="px-4 py-3 text-right">利益</th>
            <th class="px-4 py-3 text-right">利益率</th>
            <th class="px-4 py-3 text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in filteredItems"
            :key="item.id"
            class="border-b hover:bg-gray-50"
          >
            <td class="px-4 py-3">
              <input
                type="checkbox"
                :checked="selectedItems.includes(item.id)"
                @change="toggleSelect(item.id)"
              />
            </td>
            <td class="px-4 py-3 font-semibold">
              <a :href="item.url" target="_blank" class="text-blue-600 hover:underline">
                {{ item.title }}
              </a>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ sourceLabel(item.source) }}</td>
            <td class="px-4 py-3 text-right">¥{{ formatNumber(item.source_price_jpy) }}</td>
            <td class="px-4 py-3 text-right">
              {{ item.ebay_price_jpy ? `¥${formatNumber(item.ebay_price_jpy)}` : "-" }}
            </td>
            <td
              class="px-4 py-3 text-right font-semibold"
              :class="item.profit_jpy && item.profit_jpy > 0 ? 'text-green-600' : item.profit_jpy ? 'text-red-600' : 'text-gray-600'"
            >
              {{ item.profit_jpy ? `¥${formatNumber(item.profit_jpy)}` : "-" }}
            </td>
            <td class="px-4 py-3 text-right">
              {{ item.profit_margin_pct ? `${item.profit_margin_pct.toFixed(1)}%` : "-" }}
            </td>
            <td class="px-4 py-3 text-center">
              <router-link :to="`/dashboard/items/${item.id}`" class="text-blue-600 hover:underline text-xs">
                詳細
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ページング -->
    <div class="mt-4 flex justify-center gap-2">
      <button
        v-if="offset > 0"
        @click="offset -= limit"
        class="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
      >
        前へ
      </button>
      <span class="px-4 py-2 text-gray-600">
        {{ offset + 1 }} - {{ Math.min(offset + limit, total) }} / {{ total }}
      </span>
      <button
        v-if="offset + limit < total"
        @click="offset += limit"
        class="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
      >
        次へ
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue"
import { capturesAPI } from "../../services/api"

interface SourceItem {
  id: string
  title: string
  source: string
  source_price_jpy: number
  url: string
  ebay_price_jpy?: number
  profit_jpy?: number
  profit_margin_pct?: number
  created_at: string
}

const items = ref<SourceItem[]>([])
const selectedItems = ref<string[]>([])
const searchText = ref("")
const filterSource = ref("")
const sortBy = ref("date_desc")
const limit = ref(100)
const offset = ref(0)
const total = ref(0)
const isLoading = ref(false)
const isExporting = ref(false)

const filteredItems = computed(() => {
  let filtered = items.value.filter((item) => {
    const matchesSearch = item.title.toLowerCase().includes(searchText.value.toLowerCase())
    const matchesSource = !filterSource.value || item.source === filterSource.value
    return matchesSearch && matchesSource
  })

  // ソート
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case "profit_desc":
        return (b.profit_jpy || 0) - (a.profit_jpy || 0)
      case "margin_desc":
        return (b.profit_margin_pct || 0) - (a.profit_margin_pct || 0)
      case "date_desc":
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      default:
        return 0
    }
  })

  return filtered
})

const allSelected = computed(() => {
  return items.value.length > 0 && selectedItems.value.length === items.value.length
})

const formatNumber = (num: number) => num.toLocaleString()

const sourceLabel = (source: string) => {
  const labels: { [key: string]: string } = {
    mercari: "Mercari",
    yahoo_auction: "Yahoo Auction",
    yahoo_flea: "Yahoo Flea",
  }
  return labels[source] || source
}

const toggleSelect = (itemId: string) => {
  const index = selectedItems.value.indexOf(itemId)
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    selectedItems.value.push(itemId)
  }
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    selectedItems.value = []
  } else {
    selectedItems.value = items.value.map((item) => item.id)
  }
}

const exportCSV = async () => {
  isExporting.value = true
  try {
    const response = await capturesAPI.exportSavedItemsCSV(selectedItems.value)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", `margin-scout-items-${new Date().toISOString().split("T")[0]}.csv`)
    document.body.appendChild(link)
    link.click()
    link.parentNode?.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error("Export failed:", error)
  } finally {
    isExporting.value = false
  }
}

const loadItems = async () => {
  isLoading.value = true
  try {
    const response = await capturesAPI.getSavedItems(
      limit.value,
      offset.value,
      filterSource.value || undefined,
      sortBy.value
    )
    items.value = response.data.items
    total.value = response.data.total
    selectedItems.value = []
  } catch (error) {
    console.error("Failed to load items:", error)
  } finally {
    isLoading.value = false
  }
}

watch([offset, filterSource, sortBy], () => {
  offset.value = 0
  loadItems()
})

onMounted(loadItems)
</script>

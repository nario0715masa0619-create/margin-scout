<template>
  <div class="csv-export-container">
    <h1>💾 CSV出力</h1>

    <div class="export-card">
      <!-- 出力情報 -->
      <section class="section">
        <h2>出力設定</h2>
        <div class="info">
          <p><strong>ジョブID:</strong> <code>{{ route.params.jobId }}</code></p>
          <p><strong>出力件数:</strong> <span class="highlight">{{ store.selectedCandidates.size }} 件</span></p>
        </div>
      </section>

      <!-- 出力オプション -->
      <section class="section">
        <h2>オプション</h2>
        <div class="options">
          <label>
            <input v-model="includeMargin" type="checkbox" />
            利益率を含める
          </label>
          <label>
            <input v-model="includeUrl" type="checkbox" />
            URL を含める
          </label>
          <label>
            <input v-model="onlyProfitable" type="checkbox" />
            黒字のみ出力
          </label>
        </div>
      </section>

      <!-- 列プレビュー -->
      <section class="section">
        <h2>出力列</h2>
        <div class="columns-preview">
          <span v-for="col in outputColumns" :key="col" class="column-badge">
            {{ col }}
          </span>
        </div>
      </section>

      <!-- 操作ボタン -->
      <div class="actions">
        <button
          @click="downloadCsv"
          :disabled="store.selectedCandidates.size === 0 || isExporting"
          class="btn btn-primary"
        >
          {{ isExporting ? '⏳ 処理中...' : '📥 CSV ダウンロード' }}
        </button>
        <button @click="goBack" class="btn btn-secondary">戻る</button>
      </div>

      <!-- 処理結果 -->
      <div v-if="message" :class="['message', message.type]">
        {{ message.text }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useResearchStore } from '../stores/research'

const route = useRoute()
const router = useRouter()
const store = useResearchStore()

const includeMargin = ref(true)
const includeUrl = ref(true)
const onlyProfitable = ref(false)
const message = ref<{ type: string; text: string } | null>(null)
const isExporting = ref(false)

const outputColumns = computed(() => {
  const cols = [
    'candidate_id',
    'product_name',
    'source_channel',
    'source_price_jpy',
    'ebay_title',
    'ebay_price_usd',
    'profit_jpy'
  ]
  if (includeMargin.value) cols.push('profit_margin_pct')
  if (includeUrl.value) cols.push('source_url')
  return cols
})

const generateCsvContent = () => {
  const selectedCandidates = store.candidatesList.filter(c =>
    store.selectedCandidates.has(c.candidateId)
  )

  const filteredCandidates = onlyProfitable.value
    ? selectedCandidates.filter(c => c.profitJpy > 0)
    : selectedCandidates

  // CSV ヘッダー
  const header = outputColumns.value.join(',')

  // CSV 行
  const rows = filteredCandidates.map(candidate => {
    const cols = [
      candidate.candidateId,
      `"${candidate.productName}"`,
      candidate.sourceChannel,
      candidate.sourcePrice,
      `"${candidate.ebayTitle}"`,
      candidate.ebayPrice.toFixed(2),
      candidate.profitJpy
    ]

    if (includeMargin.value) {
      cols.push(candidate.profitMarginPct.toFixed(2))
    }

    if (includeUrl.value) {
      cols.push(`"${candidate.sourceUrl}"`)
    }

    return cols.join(',')
  })

  return [header, ...rows].join('\n')
}

const downloadCsv = async () => {
  try {
    isExporting.value = true
    message.value = null

    const csvContent = generateCsvContent()
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)

    const timestamp = new Date().toISOString().slice(0, 19).replace(/T|-|:/g, (m) => m === 'T' ? '_' : '')
    const filename = `research_results_${timestamp}.csv`

    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    URL.revokeObjectURL(url)

    message.value = {
      type: 'success',
      text: `✅ CSV をダウンロードしました (${filename})`
    }
  } catch (err: any) {
    console.error('CSV Export Error:', err)
    message.value = {
      type: 'error',
      text: `❌ CSV出力に失敗しました: ${err.message}`
    }
  } finally {
    isExporting.value = false
  }
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.csv-export-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
}

h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.export-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.section {
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
}

.section h2 {
  font-size: 1.1rem;
  margin-bottom: 1rem;
  color: #333;
}

.info p {
  margin: 0.5rem 0;
}

.info code {
  background: #f5f5f5;
  padding: 0.2rem 0.4rem;
  border-radius: 2px;
  font-family: monospace;
  font-size: 0.9rem;
}

.highlight {
  color: #007bff;
  font-weight: 600;
  font-size: 1.1rem;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.options label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: normal;
  gap: 0.5rem;
}

.options input {
  cursor: pointer;
}

.columns-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.column-badge {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.actions {
  padding: 1.5rem;
  display: flex;
  gap: 1rem;
}

.btn {
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
  transform: translateY(-2px);
}

.message {
  padding: 1rem;
  border-radius: 4px;
  text-align: center;
  font-weight: 600;
  margin-top: 1rem;
  animation: slideIn 0.3s ease;
}

.message.success {
  background: #d4edda;
  color: #155724;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

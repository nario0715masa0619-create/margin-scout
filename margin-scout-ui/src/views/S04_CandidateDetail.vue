<template>
  <div class="candidate-detail-container">
    <h1>🔍 候補詳細</h1>

    <div v-if="candidate" class="detail-card">
      <!-- 基本情報 -->
      <section class="section">
        <h2>基本情報</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">商品名:</span>
            <span class="value">{{ candidate.productName }}</span>
          </div>
          <div class="info-item">
            <span class="label">取得元:</span>
            <span class="value">{{ candidate.sourceChannel }}</span>
          </div>
          <div class="info-item">
            <span class="label">条件:</span>
            <span class="value">{{ candidate.conditionText }}</span>
          </div>
        </div>
      </section>

      <!-- 価格比較 -->
      <section class="section">
        <h2>価格比較</h2>
        <div class="comparison">
          <div class="price-box">
            <span class="label">仕入価格</span>
            <span class="price">¥{{ formatNumber(candidate.sourcePrice) }}</span>
            <a
              v-if="candidate.sourceUrl"
              :href="candidate.sourceUrl"
              target="_blank"
              rel="noopener"
              class="link"
            >
              商品ページ →
            </a>
          </div>
          <div class="arrow">→</div>
          <div class="price-box">
            <span class="label">eBay販売予想価格</span>
            <span class="price">${{ candidate.ebayPrice.toFixed(2) }}</span>
            <span class="source">eBay</span>
          </div>
        </div>
      </section>

      <!-- 利益計算 -->
      <section class="section">
        <h2>利益計算</h2>
        <div class="profit-grid">
          <div class="profit-item" :class="candidate.profitJpy >= 0 ? 'positive' : 'negative'">
            <span class="label">利益:</span>
            <span class="value">¥{{ formatNumber(candidate.profitJpy) }}</span>
          </div>
          <div class="profit-item" :class="candidate.profitMarginPct >= 0 ? 'positive' : 'negative'">
            <span class="label">利益率:</span>
            <span class="value">{{ candidate.profitMarginPct.toFixed(1) }}%</span>
          </div>
          <div class="profit-item">
            <span class="label">マッチスコア:</span>
            <span class="value">{{ candidate.matchScore.toFixed(3) }}</span>
          </div>
          <div class="profit-item">
            <span class="label">ステータス:</span>
            <span class="value" :class="candidate.status === 'success' ? 'status-success' : ''">
              {{ candidate.status }}
            </span>
          </div>
        </div>
      </section>

      <!-- eBay情報 -->
      <section class="section">
        <h2>eBay マッチ情報</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">eBay商品名:</span>
            <span class="value">{{ candidate.ebayTitle }}</span>
          </div>
          <div class="info-item">
            <span class="label">eBay Item ID:</span>
            <span class="value"><code>{{ candidate.ebayItemId }}</code></span>
          </div>
        </div>
      </section>

      <!-- 操作ボタン -->
      <div class="actions">
        <button @click="toggleSelection" :class="['btn', isSelected ? 'btn-success' : 'btn-secondary']">
          {{ isSelected ? '✓ 選択済み' : '選択' }}
        </button>
        <button @click="goBack" class="btn btn-secondary">戻る</button>
        <button v-if="hasPrevious" @click="goToPrevious" class="btn btn-outline">◀ 前</button>
        <button v-if="hasNext" @click="goToNext" class="btn btn-outline">次 ▶</button>
      </div>
    </div>

    <div v-else class="loading">
      <div class="spinner"></div>
      <p>読み込み中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useResearchStore } from '../stores/research'
import { researchAPI } from '../services/api'
import type { Candidate } from '../stores/research'

const route = useRoute()
const router = useRouter()
const store = useResearchStore()

const candidate = ref<Candidate | null>(null)
const currentIndex = ref(0)

const isSelected = computed(() => {
  return candidate.value ? store.selectedCandidates.has(candidate.value.candidateId) : false
})

const hasPrevious = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < store.candidatesList.length - 1)

const toggleSelection = () => {
  if (candidate.value) {
    store.toggleSelectedCandidate(candidate.value.candidateId)
  }
}

const goBack = () => {
  router.back()
}

const goToPrevious = () => {
  if (hasPrevious.value) {
    currentIndex.value--
    const prev = store.candidatesList[currentIndex.value]
    router.replace({
      params: {
        jobId: route.params.jobId,
        candidateId: prev.candidateId
      }
    })
    fetchCandidateDetail()
  }
}

const goToNext = () => {
  if (hasNext.value) {
    currentIndex.value++
    const next = store.candidatesList[currentIndex.value]
    router.replace({
      params: {
        jobId: route.params.jobId,
        candidateId: next.candidateId
      }
    })
    fetchCandidateDetail()
  }
}

const formatNumber = (num: number) => {
  return num.toLocaleString('ja-JP')
}

const fetchCandidateDetail = async () => {
  try {
    const jobId = route.params.jobId as string
    const candidateId = route.params.candidateId as string
    const data = await researchAPI.getCandidateDetail(jobId, candidateId)

    candidate.value = data

    // 現在のインデックスを更新
    const idx = store.candidatesList.findIndex(c => c.candidateId === candidateId)
    if (idx >= 0) {
      currentIndex.value = idx
    }
  } catch (err: any) {
    console.error('Failed to fetch candidate detail:', err)
  }
}

onMounted(() => {
  fetchCandidateDetail()
})
</script>

<style scoped>
.candidate-detail-container {
  max-width: 900px;
  margin: 2rem auto;
  padding: 2rem;
}

h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.detail-card {
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

.info-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.label {
  font-weight: 600;
  color: #666;
  margin-bottom: 0.25rem;
}

.value {
  color: #333;
  word-break: break-word;
}

.value code {
  background: #f5f5f5;
  padding: 0.2rem 0.4rem;
  border-radius: 2px;
  font-family: monospace;
  font-size: 0.9rem;
}

.comparison {
  display: flex;
  align-items: center;
  justify-content: space-around;
  gap: 1rem;
  padding: 1.5rem;
  background: #f9f9f9;
  border-radius: 8px;
}

.price-box {
  text-align: center;
  flex: 1;
}

.price-box .label {
  display: block;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.price {
  display: block;
  font-size: 1.5rem;
  font-weight: bold;
  color: #007bff;
  margin-bottom: 0.5rem;
}

.price-box .link,
.source {
  display: block;
  font-size: 0.9rem;
  color: #666;
}

.link {
  color: #007bff;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.arrow {
  font-size: 2rem;
  color: #999;
}

.profit-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.profit-item {
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 4px;
  text-align: center;
}

.profit-item.positive {
  background: #d4edda;
}

.profit-item.negative {
  background: #f8d7da;
}

.profit-item .label {
  display: block;
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.profit-item .value {
  display: block;
  font-size: 1.2rem;
  font-weight: bold;
  color: #333;
}

.status-success {
  color: #28a745;
}

.actions {
  padding: 1.5rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn {
  flex: 1;
  min-width: 100px;
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover {
  background: #218838;
  transform: translateY(-2px);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
  transform: translateY(-2px);
}

.btn-outline {
  background: none;
  border: 1px solid #007bff;
  color: #007bff;
}

.btn-outline:hover {
  background: #007bff;
  color: white;
  transform: translateY(-2px);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>

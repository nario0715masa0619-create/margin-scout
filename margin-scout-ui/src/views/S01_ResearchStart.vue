<template>
  <div class="research-start-container">
    <h1>📋 リサーチ条件設定</h1>
    
    <form @submit.prevent="startResearch" class="research-form">
      <!-- キーワード入力 -->
      <div class="form-group">
        <label>キーワード (カンマ区切り)</label>
        <input
          v-model="keywords"
          type="text"
          placeholder="iPhone, Canon, Gucci"
          class="form-input"
        />
        <small>複数キーワードはカンマで区切ってください</small>
      </div>

      <!-- ソース選択 -->
      <div class="form-group">
        <label>取得元（複数選択可）</label>
        <div class="checkbox-group">
          <label v-for="source in availableSources" :key="source" class="checkbox-label">
            <input v-model="selectedSources" :value="source" type="checkbox" />
            {{ source }}
          </label>
        </div>
      </div>

      <!-- 日数指定 -->
      <div class="form-group">
        <label>取得対象期間（日）</label>
        <input v-model.number="daysBack" type="number" min="1" max="365" class="form-input" />
      </div>

      <!-- 最小販売数 -->
      <div class="form-group">
        <label>最小販売数</label>
        <input v-model.number="minSales" type="number" min="1" class="form-input" />
      </div>

      <!-- 検索オプション -->
      <div class="form-group">
        <label>検索オプション（複数選択可）</label>
        <div class="checkbox-group">
          <label class="checkbox-label">
            <input type="checkbox" value="on_sale" v-model="selectedOptions" /> 販売中
          </label>
          <label class="checkbox-label">
            <input type="checkbox" value="sold_out" v-model="selectedOptions" /> 売り切れ
          </label>
          <label class="checkbox-label">
            <input type="checkbox" value="fixed_price" v-model="selectedOptions" /> 通常出品
          </label>
          <label class="checkbox-label">
            <input type="checkbox" value="auction" v-model="selectedOptions" /> オークション
          </label>
        </div>
      </div>

      <!-- コンディション -->
      <div class="form-group">
        <label>コンディション（複数選択可）</label>
        <div class="checkbox-group">
          <label class="checkbox-label">
            <input type="checkbox" value="new" v-model="selectedConditions" /> 新品、未使用
          </label>
          <label class="checkbox-label">
            <input type="checkbox" value="almost_new" v-model="selectedConditions" /> 未使用に近い
          </label>
          <label class="checkbox-label">
            <input type="checkbox" value="no_scratches" v-model="selectedConditions" /> 目立った傷や汚れなし
          </label>
          <label class="checkbox-label">
            <input type="checkbox" value="slight_scratches" v-model="selectedConditions" /> やや傷や汚れあり
          </label>
          <label class="checkbox-label">
            <input type="checkbox" value="scratched" v-model="selectedConditions" /> 傷や汚れあり
          </label>
          <label class="checkbox-label">
            <input type="checkbox" value="bad_condition" v-model="selectedConditions" /> 全体的に状態が悪い
          </label>
        </div>
      </div>

      <!-- 送信ボタン -->
      <button
        :disabled="!keywords || selectedSources.length === 0 || isLoading"
        type="submit"
        class="btn btn-primary"
      >
        {{ isLoading ? '⏳ 開始中...' : '🚀 リサーチ開始' }}
      </button>
    </form>

    <!-- エラー表示 -->
    <div v-if="error" class="error-message">
      <span>⚠️ {{ error }}</span>
      <button @click="error = ''" class="btn-close">×</button>
    </div>

    <!-- ローディング表示 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p>リサーチを開始しています...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useResearchStore } from '../stores/research'
import { researchAPI } from '../services/api'

// TypeScript エラーを防ぐため chrome を declare しておく
declare const chrome: any;

const router = useRouter()
const store = useResearchStore()

const keywords = ref('')
const selectedSources = ref(['mercari', 'yahoo_flea', 'yahoo_auction', 'hardoff'])
const daysBack = ref(90)
const minSales = ref(2)
const selectedOptions = ref<string[]>(['on_sale', 'fixed_price'])
const selectedConditions = ref<string[]>(['new', 'almost_new', 'no_scratches'])
const error = ref('')
const isLoading = ref(false)

const availableSources = ['mercari', 'yahoo_flea', 'yahoo_auction', 'hardoff']

// Chrome 拡張機能にメッセージを送る
const sendToExtension = (keyword: string, jobId: string) => {
  try {
    // Chromeオブジェクトが存在するかチェック（普通のWebブラウザ上で ReferenceError でクラッシュしないように）
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage(
        // ※注意: Webページから直接拡張機能へ送るには、拡張機能のIDを指定するか、externally_connectableが必要です。
        {
          action: 'scrape',
          keyword: keyword,
          jobId: jobId
        },
        (response: any) => {
          if (chrome.runtime.lastError) {
            console.warn('Extension message error:', chrome.runtime.lastError)
          } else {
            console.log('Extension response:', response)
          }
        }
      )
    } else {
      // Content Script が注入されている場合は window.postMessage の方が確実です
      window.postMessage({
        type: 'MARGINSCOUT_SCRAPE_REQUEST',
        action: 'scrape',
        keyword: keyword,
        jobId: jobId
      }, '*')
      console.warn('chrome.runtime is not available on standard web pages. Sent via postMessage fallback.')
    }
  } catch (err) {
    console.warn('Could not communicate with extension:', err)
    // 拡張機能がない場合は無視（eBay モックデータだけで続行）
  }
}

const startResearch = async () => {
  if (!keywords.value.trim()) {
    error.value = 'キーワードを入力してください'
    return
  }

  if (selectedSources.value.length === 0) {
    error.value = '取得元を選択してください'
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    const keywordList = keywords.value.split(',').map(k => k.trim()).filter(k => k)

    // ストア更新
    store.setExecutionConditions({
      keywords: keywordList,
      sources: selectedSources.value,
      daysBack: daysBack.value,
      minSales: minSales.value,
      selectedOptions: selectedOptions.value,
      selectedConditions: selectedConditions.value
    })

    // API 呼び出し
    const response = await researchAPI.startResearch({
      title: "Untitled Research",
      conditions: {
        keywords: keywordList,
        sources: selectedSources.value,
        days_back: daysBack.value,
        min_sales: minSales.value,
        selected_options: selectedOptions.value,
        selected_conditions: selectedConditions.value
      }
    })

    const jobId = response.id || response.job_id

    // ジョブ状態を更新
    store.setJobState({
      jobId: jobId,
      status: 'running',
      progress: 0,
      totalItems: 0,
      matchedItems: 0,
      startedAt: response.created_at,
      completedAt: null
    })

    // 🔥 Chrome 拡張機能にメッセージを送信（各キーワードについて）
    keywordList.forEach(keyword => {
      sendToExtension(keyword, jobId)
    })

    // モニター画面へ遷移
    router.push({ name: 'ExecutionMonitor', params: { jobId } })
  } catch (err: any) {
    console.error('API Error:', err)
    error.value = err.message || 'リサーチ開始に失敗しました。もう一度お試しください。'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.research-start-container {
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

h1 {
  text-align: center;
  margin-bottom: 2rem;
  color: #2c3e50;
}

.research-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-weight: 600;
  color: #333;
}

small {
  color: #666;
  font-size: 0.875rem;
}

.form-input {
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
}

.checkbox-group {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  font-weight: normal;
  cursor: pointer;
  gap: 0.5rem;
}

.checkbox-label input {
  cursor: pointer;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  width: 100%;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

.error-message {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  margin-top: 1rem;
  animation: slideIn 0.3s ease;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #721c24;
  cursor: pointer;
  padding: 0;
}

.btn-close:hover {
  opacity: 0.7;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
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

.loading-overlay p {
  color: white;
  font-size: 1.1rem;
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

<template>
  <div class="monitor-container">
    <h1>⚙️ 実行中モニター</h1>

    <div v-if="jobState.jobId" class="monitor-card">
      <!-- ジョブ情報 -->
      <div class="job-info">
        <p><strong>ジョブID:</strong> <code>{{ jobState.jobId }}</code></p>
        <p><strong>状態:</strong> <span class="status-badge" :class="jobState.status">{{ statusText }}</span></p>
        <p><strong>進捗:</strong> {{ jobState.progress }}%</p>
      </div>

      <!-- プログレスバー -->
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: jobState.progress + '%' }">
          <span v-if="jobState.progress > 10">{{ jobState.progress }}%</span>
        </div>
      </div>

      <!-- 統計情報 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">取得件数</div>
          <div class="stat-value">{{ jobState.totalItems }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">マッチ件数</div>
          <div class="stat-value">{{ jobState.matchedItems }}</div>
        </div>
      </div>

      <!-- 操作ボタン -->
      <div class="actions">
        <button
          @click="cancelJob"
          :disabled="jobState.status !== 'running'"
          class="btn btn-warning"
        >
          ⏸️ キャンセル
        </button>
        <button
          @click="goToCandidates"
          :disabled="jobState.status === 'running'"
          class="btn btn-success"
        >
          ✓ 候補一覧へ
        </button>
      </div>

      <!-- ステータスメッセージ -->
      <div v-if="statusMessage" :class="['status-message', statusMessage.type]">
        {{ statusMessage.text }}
      </div>
    </div>

    <div v-else class="loading">
      <div class="spinner"></div>
      <p>ジョブ情報を読み込み中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useResearchStore } from '../stores/research'
import { researchAPI } from '../services/api'

const router = useRouter()
const route = useRoute()
const store = useResearchStore()

const jobState = computed(() => store.jobState)
const statusMessage = ref<{ type: string; text: string } | null>(null)

const statusText = computed(() => {
  const statuses: Record<string, string> = {
    running: '🔄 実行中',
    completed: '✅ 完了',
    failed: '❌ 失敗',
    cancelled: '⏹️ キャンセル済み'
  }
  return statuses[jobState.value.status] || '不明'
})

let pollInterval: number | null = null

const fetchJobStatus = async () => {
  try {
    const jobId = route.params.jobId as string
    const data = await researchAPI.getJobStatus(jobId)

    store.setJobState({
      jobId: data.job_id,
      status: data.status,
      progress: data.progress || 0,
      totalItems: data.total_items || 0,
      matchedItems: data.matched_items || 0,
      startedAt: data.started_at,
      completedAt: data.completed_at
    })

    if (data.status === 'completed') {
      statusMessage.value = { type: 'success', text: '✅ リサーチが完了しました！' }
      stopPolling()
      // 2秒後に自動遷移
      setTimeout(() => {
        router.push({ name: 'CandidateList', params: { jobId } })
      }, 2000)
    } else if (data.status === 'failed') {
      statusMessage.value = { type: 'error', text: '❌ リサーチに失敗しました' }
      stopPolling()
    } else if (data.status === 'cancelled') {
      statusMessage.value = { type: 'info', text: '⏹️ リサーチはキャンセルされました' }
      stopPolling()
    }
  } catch (err: any) {
    console.error('Poll Error:', err)
    statusMessage.value = { type: 'error', text: `エラー: ${err.message}` }
  }
}

const cancelJob = async () => {
  try {
    const jobId = route.params.jobId as string
    await researchAPI.cancelJob(jobId)
    statusMessage.value = { type: 'info', text: 'キャンセルしました' }
    stopPolling()
  } catch (err: any) {
    statusMessage.value = { type: 'error', text: `キャンセル失敗: ${err.message}` }
  }
}

const goToCandidates = () => {
  const jobId = route.params.jobId as string
  router.push({ name: 'CandidateList', params: { jobId } })
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onMounted(() => {
  fetchJobStatus()
  pollInterval = window.setInterval(fetchJobStatus, 2000)
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.monitor-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
}

h1 {
  text-align: center;
  margin-bottom: 2rem;
  color: #2c3e50;
}

.monitor-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

.job-info {
  background: #e3f2fd;
  padding: 1.5rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
}

.job-info p {
  margin: 0.5rem 0;
  font-size: 0.95rem;
}

.job-info code {
  background: #f5f5f5;
  padding: 0.2rem 0.4rem;
  border-radius: 2px;
  font-family: monospace;
  font-size: 0.85rem;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.9rem;
}

.status-badge.running {
  background: #fff3cd;
  color: #856404;
}

.status-badge.completed {
  background: #d4edda;
  color: #155724;
}

.status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.status-badge.cancelled {
  background: #e2e3e5;
  color: #383d41;
}

.progress-bar {
  width: 100%;
  height: 30px;
  background: #ddd;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #45a049);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 0.9rem;
  transition: width 0.5s ease;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 4px;
  text-align: center;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #007bff;
}

.actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.btn {
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-warning {
  background: #ffc107;
  color: #333;
}

.btn-warning:hover:not(:disabled) {
  background: #ffb300;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(255, 193, 7, 0.3);
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
}

.btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.status-message {
  padding: 1rem;
  border-radius: 4px;
  text-align: center;
  font-weight: 600;
}

.status-message.success {
  background: #d4edda;
  color: #155724;
}

.status-message.error {
  background: #f8d7da;
  color: #721c24;
}

.status-message.info {
  background: #d1ecf1;
  color: #0c5460;
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

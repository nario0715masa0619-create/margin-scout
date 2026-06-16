<template>
  <div class="log-panel" :class="{ collapsed }">
    <!-- Header -->
    <div class="log-header" @click="collapsed = !collapsed">
      <span class="log-title">📋 実行ログ ({{ errorStore.logs.length }} 件)</span>
      <button class="btn-toggle">{{ collapsed ? '▼' : '▲' }}</button>
    </div>

    <!-- Content -->
    <div v-if="!collapsed" class="log-content">
      <!-- Filter -->
      <div class="log-filter">
        <label v-for="level in ['info', 'warning', 'error', 'success']" :key="level">
          <input v-model="selectedLevels" :value="level" type="checkbox" />
          <span :class="`log-level-${level}`">{{ level }}</span>
        </label>
      </div>

      <!-- Logs -->
      <div class="log-entries">
        <div
          v-for="log in filteredLogs"
          :key="log.id"
          :class="`log-entry log-${log.level}`"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span :class="`log-level log-level-${log.level}`">[{{ log.level.toUpperCase() }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>

        <div v-if="filteredLogs.length === 0" class="log-empty">
          ℹ️ ログがありません
        </div>
      </div>

      <!-- Actions -->
      <div class="log-actions">
        <button @click="errorStore.clearAllLogs" class="btn btn-sm btn-warning">🗑️ ログクリア</button>
        <button @click="errorStore.exportLogs" class="btn btn-sm btn-secondary">📥 エクスポート</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useErrorStore } from '../stores/error'

const errorStore = useErrorStore()
const collapsed = ref(true)
const selectedLevels = ref(['info', 'warning', 'error', 'success'])

const filteredLogs = computed(() => {
  return errorStore.logs.filter(log => selectedLevels.value.includes(log.level))
})

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString('ja-JP')
}
</script>

<style scoped>
.log-panel {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-top: 1px solid #ddd;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 300px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.log-panel.collapsed {
  max-height: 50px;
}

.log-header {
  padding: 1rem;
  background: #2c3e50;
  color: white;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
}

.log-title {
  font-weight: 600;
}

.btn-toggle {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 1rem;
}

.log-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.log-filter {
  padding: 0.75rem;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.log-filter label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
}

.log-filter input {
  cursor: pointer;
}

.log-level-info { color: #0c5460; }
.log-level-warning { color: #856404; }
.log-level-error { color: #721c24; }
.log-level-success { color: #155724; }

.log-entries {
  flex: 1;
  overflow-y: auto;
  font-size: 0.9rem;
  font-family: monospace;
  padding: 0.5rem;
}

.log-entry {
  padding: 0.5rem;
  margin-bottom: 0.25rem;
  border-left: 3px solid #ccc;
  border-radius: 2px;
}

.log-entry.log-info { background: #d1ecf1; border-left-color: #0c5460; }
.log-entry.log-warning { background: #fff3cd; border-left-color: #856404; }
.log-entry.log-error { background: #f8d7da; border-left-color: #721c24; }
.log-entry.log-success { background: #d4edda; border-left-color: #155724; }

.log-time {
  color: #666;
  margin-right: 0.5rem;
}

.log-level {
  font-weight: 600;
  margin-right: 0.5rem;
}

.log-message {
  color: #333;
}

.log-empty {
  text-align: center;
  padding: 1rem;
  color: #999;
}

.log-actions {
  padding: 0.75rem;
  background: #f5f5f5;
  border-top: 1px solid #ddd;
  display: flex;
  gap: 0.5rem;
}

.btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-sm {
  flex: 1;
}

.btn-warning {
  background: #ffc107;
  color: #333;
}

.btn-warning:hover {
  background: #ffb300;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}
</style>

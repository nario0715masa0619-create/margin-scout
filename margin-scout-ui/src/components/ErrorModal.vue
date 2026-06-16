<template>
  <div v-if="errorStore.showErrorModal" class="error-modal-overlay">
    <div class="error-modal">
      <div class="error-header">
        <span class="error-icon">⚠️</span>
        <h2>エラーが発生しました</h2>
        <button @click="errorStore.clearError" class="btn-close">×</button>
      </div>

      <div class="error-content">
        <p class="error-message">{{ errorStore.currentError?.message }}</p>
        <details v-if="errorStore.currentError?.details" class="error-details">
          <summary>詳細を表示</summary>
          <pre>{{ errorStore.currentError.details }}</pre>
        </details>
      </div>

      <div class="error-footer">
        <button @click="errorStore.clearError" class="btn btn-primary">了解</button>
        <button @click="retry" class="btn btn-secondary">再試行</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useErrorStore } from '../stores/error'
import { useRouter } from 'vue-router'

const errorStore = useErrorStore()
const router = useRouter()

const retry = () => {
  errorStore.clearError()
  router.go(-1)
}
</script>

<style scoped>
.error-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.error-modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 90%;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.error-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  border-bottom: 1px solid #f8d7da;
  background: #f8d7da;
  color: #721c24;
}

.error-icon {
  font-size: 1.5rem;
}

.error-header h2 {
  flex: 1;
  margin: 0;
  font-size: 1.1rem;
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

.error-content {
  padding: 1.5rem;
}

.error-message {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #333;
}

.error-details {
  background: #f5f5f5;
  padding: 0.75rem;
  border-radius: 4px;
  cursor: pointer;
}

.error-details summary {
  font-weight: 600;
  color: #666;
}

.error-details pre {
  margin: 0.75rem 0 0 0;
  font-size: 0.85rem;
  color: #333;
  overflow-x: auto;
}

.error-footer {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #eee;
  background: #f9f9f9;
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
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}
</style>

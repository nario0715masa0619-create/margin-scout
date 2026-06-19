// src/services/api.ts
import axios from 'axios'
import { useErrorStore } from '../stores/error'
import { useAuthStore } from '../stores/auth'
import router from '../router'
import type { ResearchStartPayload } from '../types/research'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000
})

let isRefreshing = false
let failedQueue: Array<{ resolve: (token: string) => void; reject: (error: any) => void }> = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) prom.reject(error)
    else prom.resolve(token!)
  })
  failedQueue = []
}

api.interceptors.request.use(
  config => {
    const authStore = useAuthStore()
    if (authStore.accessToken) {
      config.headers['Authorization'] = `Bearer ${authStore.accessToken}`
    }
    return config
  },
  error => Promise.reject(error)
)

api.interceptors.response.use(
  response => response,
  async error => {
    const errorStore = useErrorStore()
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url.includes('/auth/login')) {
      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token
          return api(originalRequest)
        }).catch(err => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true
      const authStore = useAuthStore()

      try {
        const newAccessToken = await authStore.refreshAccessToken()
        processQueue(null, newAccessToken)
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        authStore.logout()
        router.push('/login')
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 既存のエラーハンドリング
    if (error.response && error.response.status !== 401) {
      errorStore.addLog('error', error.response.data?.detail || 'API エラーが発生', `Status: ${error.response.status}`)
    }
    return Promise.reject(error)
  }
)

export const researchAPI = {
  // 既存メソッドの実装を維持（パスを /research-jobs に適応）
  async startResearch(payload: ResearchStartPayload) {
    const response = await api.post('/research-jobs', payload)
    return response.data
  },
  async getJobStatus(jobId: string) {
    const response = await api.get(`/research-jobs/${jobId}`)
    return response.data
  },
  async getCandidates(jobId: string, limit: number = 100, offset: number = 0) {
    const response = await api.get(`/research-jobs/${jobId}/results`, { params: { limit, offset } })
    return response.data
  },
  async getCandidateDetail(jobId: string, candidateId: string) {
    const response = await api.get(`/research-jobs/${jobId}/results/${candidateId}`)
    return response.data
  },
  async exportCsv(jobId: string) {
    const response = await api.post(`/research-jobs/${jobId}/export/csv`)
    return response.data
  },
  async cancelJob(jobId: string) {
    const response = await api.post(`/research-jobs/${jobId}/cancel`)
    return response.data
  }
}

export default api

// SavedSearch CRUD + 監視制御
export const savedSearchAPI = {
  list: (limit = 20, offset = 0) =>
    api.get("/saved-searches", { params: { limit, offset } }),
  
  get: (id: string) =>
    api.get(`/saved-searches/${id}`),
  
  create: (payload: {
    name: string;
    source: "mercari" | "yahoo_auction" | "yahoo_flea";
    filters: Record<string, any>;
    is_monitoring_enabled: boolean;
    monitoring_interval_hours: number;
  }) =>
    api.post("/saved-searches", payload),
  
  update: (id: string, payload: Partial<any>) =>
    api.put(`/saved-searches/${id}`, payload),
  
  delete: (id: string) =>
    api.delete(`/saved-searches/${id}`),
  
  rerun: (id: string) =>
    api.post(`/saved-searches/${id}/rerun`),
  
  disableMonitoring: (id: string) =>
    api.post(`/saved-searches/${id}/disable-monitoring`),
  
  // 監視ジョブ手動実行
  dispatchMonitoring: () =>
    api.post("/monitoring/dispatch"),
  
  getTaskStatus: (taskId: string) =>
    api.get(`/monitoring/task-status/${taskId}`),
};

// Trigger Heroku rebuild

export const capturesAPI = {
  getImportSessions: (limit = 10) =>
    api.get("/captures", { params: { limit } }),
    
  getSavedItems: (limit = 100, offset = 0, source?: string, sort_by?: string) =>
    api.get("/captures/items", { params: { limit, offset, source, sort_by } }),
    
  exportSavedItemsCSV: (itemIds: string[]) =>
    api.post("/captures/export", { item_ids: itemIds }, { responseType: 'blob' })
};

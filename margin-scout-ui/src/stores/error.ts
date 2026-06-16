import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface LogEntry {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'success'
  message: string
  details?: string
}

export const useErrorStore = defineStore('error', () => {
  // State
  const logs = ref<LogEntry[]>([])
  const currentError = ref<LogEntry | null>(null)
  const showErrorModal = ref(false)

  // Max logs to keep in memory
  const MAX_LOGS = 100

  // Actions
  const addLog = (level: 'info' | 'warning' | 'error' | 'success', message: string, details?: string) => {
    const logEntry: LogEntry = {
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toISOString(),
      level,
      message,
      details
    }

    logs.value.unshift(logEntry)

    // Keep only last 100 logs
    if (logs.value.length > MAX_LOGS) {
      logs.value = logs.value.slice(0, MAX_LOGS)
    }

    // Auto-save to localStorage
    saveLogs()

    return logEntry.id
  }

  const showError = (message: string, details?: string) => {
    const id = addLog('error', message, details)
    currentError.value = logs.value.find(l => l.id === id) || null
    showErrorModal.value = true
  }

  const clearError = () => {
    currentError.value = null
    showErrorModal.value = false
  }

  const clearAllLogs = () => {
    logs.value = []
    localStorage.removeItem('research_logs')
  }

  const saveLogs = () => {
    try {
      localStorage.setItem('research_logs', JSON.stringify(logs.value.slice(0, 50)))
    } catch (e) {
      console.error('Failed to save logs to localStorage', e)
    }
  }

  const loadLogs = () => {
    try {
      const saved = localStorage.getItem('research_logs')
      if (saved) {
        logs.value = JSON.parse(saved)
      }
    } catch (e) {
      console.error('Failed to load logs from localStorage', e)
    }
  }

  const exportLogs = () => {
    const content = logs.value
      .map(log => `[${log.level.toUpperCase()}] ${log.timestamp} - ${log.message}${log.details ? ' (' + log.details + ')' : ''}`)
      .join('\n')

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)

    link.setAttribute('href', url)
    link.setAttribute('download', `research_logs_${new Date().toISOString().slice(0, 10)}.log`)
    link.style.visibility = 'hidden'

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Load logs on init
  loadLogs()

  return {
    logs,
    currentError,
    showErrorModal,
    addLog,
    showError,
    clearError,
    clearAllLogs,
    exportLogs
  }
})

import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

import type { SearchOption, ItemCondition } from '../types/research'

// ==================== Types ====================
export interface ExecutionConditions {
  sources: string[]
  keywords: string[]
  daysBack: number
  minSales: number
  selectedOptions: SearchOption[]
  selectedConditions: ItemCondition[]
}

export interface JobState {
  jobId: string
  status: 'idle' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  startedAt: string | null
  completedAt: string | null
  totalItems: number
  matchedItems: number
  conditions: Record<string, any> | null
}

export interface Candidate {
  candidateId: string
  productName: string
  sourceChannel: string
  sourcePrice: number
  sourceUrl?: string
  conditionText?: string
  ebayTitle: string
  ebayPrice: number
  ebayPriceJpy: number
  profitJpy: number
  profitMarginPct: number
  matchScore: number
  status: string
}

// ==================== Pinia Store ====================
export const useResearchStore = defineStore('research', () => {
  // State: 実行条件 (S01)
  const executionConditions = reactive<ExecutionConditions>({
    sources: ['mercari', 'yahoo_flea', 'yahoo_auction', 'hardoff'],
    keywords: [],
    daysBack: 90,
    minSales: 2,
    selectedOptions: ['on_sale', 'fixed_price'],
    selectedConditions: ['new', 'almost_new', 'no_scratches']
  })

  // State: ジョブ実行状態 (S02)
  const jobState = reactive<JobState>({
    jobId: '',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    totalItems: 0,
    matchedItems: 0,
    conditions: null,
  })

  // State: 候補一覧 (S03)
  const candidatesList = ref<Candidate[]>([])

  // State: 選択済み候補 (S05)
  const selectedCandidates = ref<Set<string>>(new Set())

  // Actions
  const setExecutionConditions = (conditions: Partial<ExecutionConditions>) => {
    Object.assign(executionConditions, conditions)
  }

  const setJobState = (state: Partial<JobState>) => {
    Object.assign(jobState, state)
  }

  const setCandidatesList = (candidates: Candidate[]) => {
    candidatesList.value = candidates
  }

  const toggleSelectedCandidate = (candidateId: string) => {
    if (selectedCandidates.value.has(candidateId)) {
      selectedCandidates.value.delete(candidateId)
    } else {
      selectedCandidates.value.add(candidateId)
    }
  }

  const clearSelection = () => {
    selectedCandidates.value.clear()
  }

  return {
    executionConditions,
    jobState,
    candidatesList,
    selectedCandidates,
    setExecutionConditions,
    setJobState,
    setCandidatesList,
    toggleSelectedCandidate,
    clearSelection,
  }
})

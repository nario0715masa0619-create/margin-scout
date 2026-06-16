// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import LoginPage from '../pages/LoginPage.vue'
import RegisterPage from '../pages/RegisterPage.vue'
import ResearchStartView from '../views/S01_ResearchStart.vue'
import ExecutionMonitorView from '../views/S02_ExecutionMonitor.vue'
import CandidateListView from '../views/S03_CandidateList.vue'
import CandidateDetailView from '../views/S04_CandidateDetail.vue'
import CsvExportView from '../views/S05_CsvExport.vue'

const routes: Array<RouteRecordRaw> = [
  { path: '/', redirect: '/research' },
  { path: '/login', name: 'Login', component: LoginPage, meta: { public: true } },
  { path: '/register', name: 'Register', component: RegisterPage, meta: { public: true } },
  { path: '/research', name: 'ResearchStart', component: ResearchStartView },
  { path: '/monitor/:jobId', name: 'ExecutionMonitor', component: ExecutionMonitorView },
  { path: '/candidates/:jobId', name: 'CandidateList', component: CandidateListView },
  { path: '/candidates/:jobId/:candidateId', name: 'CandidateDetail', component: CandidateDetailView },
  { path: '/export/:jobId', name: 'CsvExport', component: CsvExportView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  if (!authStore.isLoggedIn && authStore.refreshToken) {
    await authStore.loadFromLocalStorage()
  }

  const isPublic = to.matched.some(record => record.meta.public)

  if (!isPublic && !authStore.isLoggedIn) {
    next({ name: 'Login' })
  } else if ((to.name === 'Login' || to.name === 'Register') && authStore.isLoggedIn) {
    next({ name: 'ResearchStart' })
  } else {
    next()
  }
})

export default router

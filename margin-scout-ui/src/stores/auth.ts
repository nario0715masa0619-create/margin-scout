// src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, TokenResponse, RegisterRequest, LoginRequest } from '../types/auth'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const AUTH_API_URL = `${API_BASE_URL}/auth`

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const isAuthenticated = ref<boolean>(false)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  const isLoggedIn = computed(() => isAuthenticated.value && !!accessToken.value)
  const currentUser = computed(() => user.value)

  function setTokens(tokens: TokenResponse) {
    accessToken.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
    localStorage.setItem('refresh_token', tokens.refresh_token)
    isAuthenticated.value = true
  }

  function clearTokens() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('refresh_token')
  }

  async function register(data: RegisterRequest) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.post<TokenResponse>(`${AUTH_API_URL}/register`, data)
      setTokens(response.data)
      await fetchUser()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '登録に失敗しました'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function login(data: LoginRequest) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.post<TokenResponse>(`${AUTH_API_URL}/login`, data)
      setTokens(response.data)
      await fetchUser()
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'ログインに失敗しました'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    clearTokens()
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) throw new Error('No refresh token')
    try {
      const response = await axios.post<{ access_token: string }>(`${AUTH_API_URL}/refresh`, {
        refresh_token: refreshToken.value
      })
      accessToken.value = response.data.access_token
      isAuthenticated.value = true
      return response.data.access_token
    } catch (err) {
      clearTokens()
      throw err
    }
  }

  async function fetchUser() {
    if (!accessToken.value) return
    try {
      const response = await axios.get<User>(`${AUTH_API_URL}/me`, {
        headers: { Authorization: `Bearer ${accessToken.value}` }
      })
      user.value = response.data
    } catch (err) {
      console.error('User fetch failed', err)
    }
  }

  async function loadFromLocalStorage() {
    if (refreshToken.value) {
      try {
        await refreshAccessToken()
        await fetchUser()
      } catch (err) {
        clearTokens()
      }
    }
  }

  return {
    user, accessToken, refreshToken, isAuthenticated, loading, error,
    isLoggedIn, currentUser,
    register, login, logout, refreshAccessToken, fetchUser, loadFromLocalStorage
  }
})

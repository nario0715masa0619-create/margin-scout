// src/composables/useAuth.ts
import { storeToRefs } from 'pinia'
import { useAuthStore } from '../stores/auth'
import type { RegisterRequest, LoginRequest } from '../types/auth'

export function useAuth() {
  const authStore = useAuthStore()
  const { user, isAuthenticated, loading, error, isLoggedIn } = storeToRefs(authStore)

  const register = async (data: RegisterRequest) => await authStore.register(data)
  const login = async (data: LoginRequest) => await authStore.login(data)
  const logout = async () => await authStore.logout()
  const refreshToken = async () => await authStore.refreshAccessToken()

  return {
    user, isAuthenticated, loading, error, isLoggedIn,
    register, login, logout, refreshToken
  }
}

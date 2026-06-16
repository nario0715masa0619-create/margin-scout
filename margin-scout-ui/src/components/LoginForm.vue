<!-- src/components/LoginForm.vue -->
<template>
  <div class="auth-card">
    <h2 class="title">ログイン</h2>
    <form @submit.prevent="handleSubmit" class="auth-form">
      <div v-if="error" class="error-alert">{{ error }}</div>
      
      <div class="form-group">
        <label for="email">メールアドレス</label>
        <input id="email" type="email" v-model="email" required placeholder="example@example.com" />
      </div>

      <div class="form-group">
        <label for="password">パスワード</label>
        <input id="password" type="password" v-model="password" required placeholder="••••••••" />
      </div>

      <button type="submit" :disabled="loading" class="btn-primary">
        {{ loading ? 'ログイン中...' : 'ログイン' }}
      </button>
      
      <div class="auth-links">
        <span>アカウントをお持ちでないですか？</span>
        <router-link to="/register">登録はこちら</router-link>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { login, loading, error } = useAuth()
const email = ref('')
const password = ref('')

const handleSubmit = async () => {
  if (!email.value || !password.value) return
  try {
    await login({ email: email.value, password: password.value })
    router.push('/research')
  } catch (err) {
    console.error('Login error', err)
  }
}
</script>

<style scoped>
.auth-card {
  max-width: 400px; margin: 0 auto; padding: 2rem;
  background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.title { text-align: center; margin-bottom: 1.5rem; }
.auth-form { display: flex; flex-direction: column; gap: 1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.5rem; }
input { padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 4px; }
.error-alert { padding: 0.75rem; background: #fee2e2; color: #b91c1c; border-radius: 4px; font-size: 0.9rem; }
.btn-primary { padding: 0.75rem; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; }
.btn-primary:disabled { background: #9ca3af; cursor: not-allowed; }
.auth-links { margin-top: 1rem; text-align: center; font-size: 0.9rem; }
</style>

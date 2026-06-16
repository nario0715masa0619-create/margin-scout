<!-- src/components/RegisterForm.vue -->
<template>
  <div class="auth-card">
    <h2 class="title">アカウント登録</h2>
    <form @submit.prevent="handleSubmit" class="auth-form">
      <div v-if="error" class="error-alert">{{ error }}</div>
      <div v-if="validationError" class="error-alert">{{ validationError }}</div>
      
      <div class="form-group">
        <label for="username">ユーザー名</label>
        <input id="username" type="text" v-model="username" required />
      </div>

      <div class="form-group">
        <label for="email">メールアドレス</label>
        <input id="email" type="email" v-model="email" required />
      </div>

      <div class="form-group">
        <label for="password">パスワード (8文字以上)</label>
        <input id="password" type="password" v-model="password" required minlength="8" />
      </div>

      <div class="form-group">
        <label for="passwordConfirm">パスワード (確認)</label>
        <input id="passwordConfirm" type="password" v-model="passwordConfirm" required />
      </div>

      <button type="submit" :disabled="loading" class="btn-primary">
        {{ loading ? '登録中...' : '登録する' }}
      </button>
      
      <div class="auth-links">
        <span>すでにアカウントをお持ちですか？</span>
        <router-link to="/login">ログインはこちら</router-link>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { register, loading, error } = useAuth()
const email = ref(''); const username = ref('')
const password = ref(''); const passwordConfirm = ref('')
const validationError = ref('')

const handleSubmit = async () => {
  validationError.value = ''
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    validationError.value = '有効なメールアドレスを入力してください'
    return
  }
  if (password.value.length < 8) {
    validationError.value = 'パスワードは8文字以上で入力してください'
    return
  }
  if (password.value !== passwordConfirm.value) {
    validationError.value = 'パスワードが一致しません'
    return
  }
  try {
    await register({ email: email.value, username: username.value, password: password.value })
    router.push('/research')
  } catch (err) {
    console.error('Register error', err)
  }
}
</script>

<style scoped>
.auth-card { max-width: 400px; margin: 0 auto; padding: 2rem; background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.title { text-align: center; margin-bottom: 1.5rem; }
.auth-form { display: flex; flex-direction: column; gap: 1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.5rem; }
input { padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 4px; }
.error-alert { padding: 0.75rem; background: #fee2e2; color: #b91c1c; border-radius: 4px; font-size: 0.9rem; }
.btn-primary { padding: 0.75rem; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer; }
.btn-primary:disabled { background: #9ca3af; cursor: not-allowed; }
.auth-links { margin-top: 1rem; text-align: center; font-size: 0.9rem; }
</style>

<template>
  <div id="app">
    <!-- ナビゲーションバー -->
    <nav class="navbar">
      <div class="navbar-brand">
        <router-link to="/">MarginScout v2.1</router-link>
      </div>
      <div class="navbar-menu">
        <router-link to="/dashboard" class="nav-link">ダッシュボード</router-link>
        <router-link to="/research" class="nav-link">リサーチ（旧）</router-link>
      </div>
    </nav>

    <!-- メインコンテンツ -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- フッター -->
    <footer class="footer">
      <p>&copy; 2026 MarginScout. All rights reserved.</p>
    </footer>

    <!-- グローバルコンポーネント -->
    <ErrorModal />
    <LogPanel />
  </div>
</template>

<script setup lang="ts">
import ErrorModal from './components/ErrorModal.vue'
import LogPanel from './components/LogPanel.vue'
import { useErrorStore } from './stores/error'
import { onMounted } from 'vue'

const errorStore = useErrorStore()

onMounted(() => {
  errorStore.addLog('info', 'MarginScout v2.1 起動')
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f5f5;
  color: #333;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding-bottom: 50px;  /* LogPanel スペース確保 */
}

.navbar {
  background: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar-brand a {
  color: white;
  text-decoration: none;
  font-size: 1.5rem;
  font-weight: bold;
}

.navbar-brand a:hover {
  color: #3498db;
}

.navbar-menu {
  display: flex;
  gap: 2rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  transition: color 0.3s;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: #3498db;
}

.main-content {
  flex: 1;
  padding: 2rem 0;
  background: #f5f5f5;
}

.footer {
  background: #2c3e50;
  color: white;
  text-align: center;
  padding: 1.5rem;
  margin-top: 2rem;
}

.footer p {
  margin: 0;
}
</style>

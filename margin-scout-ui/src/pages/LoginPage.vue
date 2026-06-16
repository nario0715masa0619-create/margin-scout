<!-- src/pages/LoginPage.vue -->
<template>
  <div class="page-layout">
    <LoginForm />
  </div>
</template>
<script setup lang="ts">
import LoginForm from '../components/LoginForm.vue'
</script>
<style scoped>
.page-layout { min-height: 100vh; display: flex; align-items: center; justify-content: center; background-color: #f3f4f6; }
</style>

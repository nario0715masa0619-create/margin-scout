<!-- src/pages/RegisterPage.vue -->
<template>
  <div class="page-layout">
    <RegisterForm />
  </div>
</template>
<script setup lang="ts">
import RegisterForm from '../components/RegisterForm.vue'
</script>
<style scoped>
.page-layout { min-height: 100vh; display: flex; align-items: center; justify-content: center; background-color: #f3f4f6; }
</style>

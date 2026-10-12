<template>
  <div class="spinner-wrap" :style="{ minHeight: height }">
    <div class="spinner"></div>
    <p v-if="text" class="spinner-text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  text:   { type: String, default: 'AI 分析中...' },
  height: { type: String, default: '120px' }
})
</script>

<style scoped>
.spinner-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.spinner {
  width: 36px; height: 36px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.spinner-text { font-size: 13px; color: var(--text-muted); }
</style>

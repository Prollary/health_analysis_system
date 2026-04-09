<template>
  <Transition name="sos-slide">
    <div v-if="sosStore.triggered" class="sos-overlay" @click.self="sosStore.dismissSos()">
      <div class="sos-modal">
        <div class="sos-ring">
          <i class="fa-solid fa-triangle-exclamation"></i>
        </div>
        <h2 class="sos-title">紧急健康告警</h2>
        <p class="sos-msg">{{ sosStore.message }}</p>
        <p class="sos-hint">已自动发送告警邮件至绑定家属</p>
        <button class="sos-dismiss-btn" @click="sosStore.dismissSos()">
          <i class="fa-solid fa-check"></i> 我已知晓，解除告警
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { useSosStore } from '@/stores/sos'
const sosStore = useSosStore()
</script>

<style scoped>
.sos-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}
.sos-modal {
  background: var(--bg-card);
  border: 2px solid var(--danger);
  border-radius: 20px;
  padding: 40px;
  text-align: center;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 0 40px rgba(255, 71, 87, 0.4);
  animation: sos-modal-pulse 1s infinite;
}
@keyframes sos-modal-pulse {
  0%, 100% { box-shadow: 0 0 40px rgba(255, 71, 87, 0.4); }
  50%       { box-shadow: 0 0 60px rgba(255, 71, 87, 0.7); }
}
.sos-ring {
  width: 80px; height: 80px;
  border-radius: 50%;
  background: rgba(255, 71, 87, 0.2);
  border: 3px solid var(--danger);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-size: 32px;
  color: var(--danger);
  animation: ring-spin 2s linear infinite;
}
@keyframes ring-spin {
  0% { box-shadow: 0 0 0 0 rgba(255,71,87,0.4); }
  70% { box-shadow: 0 0 0 16px rgba(255,71,87,0); }
  100% { box-shadow: 0 0 0 0 rgba(255,71,87,0); }
}
.sos-title { font-size: 22px; font-weight: 700; color: var(--danger); margin-bottom: 12px; }
.sos-msg { font-size: 15px; color: var(--text-primary); margin-bottom: 8px; line-height: 1.6; }
.sos-hint { font-size: 12px; color: var(--text-muted); margin-bottom: 24px; }
.sos-dismiss-btn {
  background: var(--danger);
  color: white;
  border: none;
  border-radius: 10px;
  padding: 12px 28px;
  font-size: 15px;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.2s;
}
.sos-dismiss-btn:hover { opacity: 0.85; }

/* 进入/离开动画 */
.sos-slide-enter-active, .sos-slide-leave-active { transition: all 0.3s ease; }
.sos-slide-enter-from, .sos-slide-leave-to { opacity: 0; transform: scale(0.9); }
</style>

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSosStore = defineStore('sos', () => {
  const triggered = ref(false)
  const message = ref('')
  // 告警历史列表
  const alertHistory = ref([])

  function triggerSos(msg) {
    triggered.value = true
    message.value = msg
    alertHistory.value.unshift({
      time: new Date().toLocaleString('zh-CN'),
      msg,
      id: Date.now()
    })
    // 播放告警音效
    playAlertSound()
  }

  function dismissSos() {
    triggered.value = false
    message.value = ''
  }

  function playAlertSound() {
    try {
      const ctx = new AudioContext()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = 880
      osc.type = 'square'
      gain.gain.setValueAtTime(0.3, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8)
      osc.start(ctx.currentTime)
      osc.stop(ctx.currentTime + 0.8)
    } catch (e) {
      // 浏览器限制，忽略
    }
  }

  return { triggered, message, alertHistory, triggerSos, dismissSos }
})

<template>
  <div class="page mirror-page">
    <div class="page-header">
      <h1 class="page-title"><i class="fa-solid fa-camera"></i> 智能镜子 · 身心综合分析</h1>
    </div>

    <!-- 主区：镜子 + 分析结果 -->
    <div class="mirror-main">
      <!-- 镜子交互区 -->
      <div class="card mirror-panel">
        <div class="mirror-frame" :class="{ streaming: isStreaming }">
          <!-- 摄像头流 / 预览图 -->
          <video v-if="isStreaming" ref="videoEl" autoplay playsinline class="mirror-video"></video>
          <img v-else-if="previewUrl" :src="previewUrl" class="mirror-preview" alt="preview" />
          <div v-else class="mirror-placeholder">
            <i class="fa-solid fa-camera-retro"></i>
            <p>智能镜子</p>
          </div>
          <!-- 扫描动画线 -->
          <div v-if="scanning" class="scan-line"></div>
        </div>

        <div class="mirror-controls">
          <button v-if="!isStreaming" class="btn-outline" @click="openCamera">
            <i class="fa-solid fa-video"></i> 开启摄像头
          </button>
          <button v-if="isStreaming" class="btn-primary" @click="capture" :disabled="scanning">
            <i class="fa-solid fa-camera"></i> 拍照分析
          </button>
          <button v-if="isStreaming" class="btn-outline" @click="closeCamera">
            <i class="fa-solid fa-video-slash"></i> 关闭
          </button>
          <label class="btn-outline upload-btn">
            <i class="fa-solid fa-upload"></i> 上传照片
            <input type="file" accept="image/*" @change="handleUpload" hidden />
          </label>
        </div>
      </div>

      <!-- 分析结果区 -->
      <div class="result-panel">
        <!-- 情绪识别卡 -->
        <div class="card emotion-card">
          <div class="card-header">
            <h2><i class="fa-solid fa-face-smile"></i> 情绪识别</h2>
          </div>
          <LoadingSpinner v-if="analyzing" text="百度AI识别中..." />
          <div v-else-if="result" class="emotion-display">
            <div class="emotion-icon">{{ emotionEmoji }}</div>
            <div class="emotion-detail">
              <span class="emotion-label">{{ result.emotion }}</span>
              <span class="emotion-hint">由百度人脸识别API分析</span>
            </div>
          </div>
          <div v-else class="empty-hint sm">
            <i class="fa-solid fa-face-meh"></i>
            <p>等待拍照/上传</p>
          </div>
        </div>

        <!-- 疲劳指数仪表盘 -->
        <div class="card gauge-card">
          <div class="card-header">
            <h2><i class="fa-solid fa-gauge"></i> 疲劳/压力指数</h2>
          </div>
          <div ref="gaugeEl" class="gauge-area"></div>
          <div v-if="result" class="fatigue-level" :class="fatigueLevelClass">
            {{ fatigueLevelText }}
          </div>
        </div>
      </div>
    </div>

    <!-- 身心综合报告 -->
    <Transition name="slide-up">
      <div v-if="result" class="card report-card">
        <div class="card-header">
          <h2><i class="fa-solid fa-brain"></i> 身心综合报告</h2>
        </div>
        <p class="report-text">{{ result.report }}</p>
      </div>
    </Transition>

    <!-- 历史情绪趋势（占位，实际可对接后端历史） -->
    <div class="card">
      <div class="card-header">
        <h2><i class="fa-solid fa-chart-bar"></i> 近期情绪与疲劳趋势</h2>
      </div>
      <div ref="historyChartEl" class="echart-area"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { mirrorApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const videoEl = ref(null)
const gaugeEl = ref(null)
const historyChartEl = ref(null)
let stream = null
let gaugeChart = null
let historyChart = null

const isStreaming = ref(false)
const scanning    = ref(false)
const analyzing   = ref(false)
const previewUrl  = ref('')
const result      = ref(null)

const emotionMap = { '高兴': '😊', '悲伤': '😢', '愤怒': '😠', '厌恶': '😒', '恐惧': '😨', '惊讶': '😲', '平静': '😌', '困惑': '😕' }
const emotionEmoji = computed(() => emotionMap[result.value?.emotion] || '😶')

const fatigueLevelText = computed(() => {
  const f = result.value?.fatigue_index || 0
  if (f >= 70) return '高度疲劳/压力'
  if (f >= 40) return '中度疲劳'
  return '状态良好'
})
const fatigueLevelClass = computed(() => {
  const f = result.value?.fatigue_index || 0
  return f >= 70 ? 'danger' : f >= 40 ? 'warn' : 'ok'
})

async function openCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
    isStreaming.value = true
    await new Promise(r => setTimeout(r, 100))
    if (videoEl.value) videoEl.value.srcObject = stream
  } catch (e) {
    alert('无法访问摄像头，请检查权限或使用上传功能')
  }
}

function closeCamera() {
  stream?.getTracks().forEach(t => t.stop())
  isStreaming.value = false
  stream = null
}

async function capture() {
  if (!videoEl.value) return
  const canvas = document.createElement('canvas')
  canvas.width  = videoEl.value.videoWidth
  canvas.height = videoEl.value.videoHeight
  canvas.getContext('2d').drawImage(videoEl.value, 0, 0)
  const dataUrl = canvas.toDataURL('image/jpeg', 0.8)
  previewUrl.value = dataUrl
  closeCamera()
  await doAnalyze(dataUrl)
}

async function handleUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = async (ev) => {
    previewUrl.value = ev.target.result
    await doAnalyze(ev.target.result)
  }
  reader.readAsDataURL(file)
}

async function doAnalyze(dataUrl) {
  scanning.value = true
  analyzing.value = true
  result.value = null
  await new Promise(r => setTimeout(r, 800)) // 扫描动画效果
  scanning.value = false
  try {
    const res = await mirrorApi.analyze({ user_id: authStore.userId, image: dataUrl })
    if (res.code === 200) {
      result.value = res.data
      renderGauge(res.data.fatigue_index || 0)
    }
  } catch (e) {
    alert('分析失败：' + (e.message || '请检查网络'))
  } finally {
    analyzing.value = false
  }
}

function renderGauge(value) {
  if (!gaugeChart) return
  const color = value >= 70 ? '#ff4757' : value >= 40 ? '#ffa726' : '#00d2a8'
  gaugeChart.setOption({
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge',
      startAngle: 200, endAngle: -20,
      min: 0, max: 100,
      radius: '88%',
      pointer: { length: '60%', width: 5, itemStyle: { color } },
      progress: { show: true, width: 10, itemStyle: { color } },
      axisLine: { lineStyle: { width: 10, color: [[1, '#1e2535']] } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { color: '#64748b', fontSize: 10, distance: -28 },
      anchor: { show: true, size: 12, itemStyle: { color } },
      detail: { valueAnimation: true, formatter: '{value}', color, fontSize: 28, fontWeight: 700, offsetCenter: [0, '30%'] },
      data: [{ value, name: '疲劳指数' }],
      title: { color: '#64748b', fontSize: 12, offsetCenter: [0, '55%'] }
    }]
  })
}

function renderHistoryChart() {
  if (!historyChart) return
  // 模拟历史数据
  const emotions = ['平静', '高兴', '平静', '困惑', '悲伤', '平静', '高兴']
  const fatigues = [25, 18, 35, 55, 70, 40, 22]
  const dates = ['04-02', '04-03', '04-04', '04-05', '04-06', '04-07', '04-08']
  historyChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#1e2535', borderColor: '#2d3748', textStyle: { color: '#e2e8f0' } },
    legend: { data: ['情绪得分', '疲劳指数'], textStyle: { color: '#94a3b8' }, top: 0 },
    grid: { left: 40, right: 20, top: 36, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: dates, axisLabel: { color: '#64748b' }, axisLine: { lineStyle: { color: '#2d3748' } } },
    yAxis: { type: 'value', max: 100, axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#1e2535' } } },
    series: [
      { name: '情绪得分', type: 'bar', barMaxWidth: 28,
        data: [65, 85, 68, 45, 30, 60, 80],
        itemStyle: { color: '#0d84ff', borderRadius: [4, 4, 0, 0] }
      },
      { name: '疲劳指数', type: 'line', smooth: true, symbol: 'circle', symbolSize: 7,
        data: fatigues,
        lineStyle: { color: '#ff4757', width: 2 }, itemStyle: { color: '#ff4757' }
      }
    ]
  })
}

onMounted(() => {
  gaugeChart   = echarts.init(gaugeEl.value)
  historyChart = echarts.init(historyChartEl.value)
  renderGauge(0)
  renderHistoryChart()
  window.addEventListener('resize', () => { gaugeChart?.resize(); historyChart?.resize() })
})
onUnmounted(() => {
  closeCamera()
  gaugeChart?.dispose()
  historyChart?.dispose()
})
</script>

<style scoped>
.mirror-page { display: flex; flex-direction: column; gap: 20px; }

/* 主布局 */
.mirror-main { display: grid; grid-template-columns: 360px 1fr; gap: 16px; }

/* 镜子面板 */
.mirror-panel { display: flex; flex-direction: column; gap: 16px; align-items: center; padding: 24px; }
.mirror-frame {
  width: 280px; height: 280px;
  border-radius: 50%;
  border: 4px solid var(--border-color);
  overflow: hidden;
  position: relative;
  background: var(--bg-deep);
  display: flex; align-items: center; justify-content: center;
  transition: border-color 0.3s;
}
.mirror-frame.streaming { border-color: var(--primary); box-shadow: 0 0 24px rgba(13,132,255,0.4); }
.mirror-video, .mirror-preview { width: 100%; height: 100%; object-fit: cover; }
.mirror-placeholder { text-align: center; color: var(--text-muted); }
.mirror-placeholder i { font-size: 48px; opacity: 0.3; display: block; margin-bottom: 8px; }
.mirror-placeholder p { font-size: 13px; }

/* 扫描线动画 */
.scan-line {
  position: absolute;
  left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #0d84ff, transparent);
  animation: scan 1.5s linear infinite;
  z-index: 2;
}
@keyframes scan { 0% { top: 0; } 100% { top: 100%; } }

.mirror-controls { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
.upload-btn { cursor: pointer; }

/* 结果面板 */
.result-panel { display: flex; flex-direction: column; gap: 16px; }
.emotion-card, .gauge-card { flex: 1; }
.gauge-area { height: 180px; }

.emotion-display { display: flex; align-items: center; gap: 16px; padding: 10px 0; }
.emotion-icon { font-size: 52px; line-height: 1; }
.emotion-detail { display: flex; flex-direction: column; gap: 4px; }
.emotion-label { font-size: 22px; font-weight: 700; color: var(--text-primary); }
.emotion-hint  { font-size: 11px; color: var(--text-muted); }

.fatigue-level {
  text-align: center; font-size: 14px; font-weight: 600;
  padding: 6px; border-radius: 6px; margin-top: -8px;
}
.fatigue-level.ok     { color: var(--success); background: rgba(0,210,168,0.1); }
.fatigue-level.warn   { color: var(--warning); background: rgba(255,167,38,0.1); }
.fatigue-level.danger { color: var(--danger);  background: rgba(255,71,87,0.1); }

/* 综合报告 */
.report-card .report-text {
  font-size: 15px; color: var(--text-secondary);
  line-height: 1.8; padding: 4px 0;
}

.echart-area { height: 240px; }

.empty-hint.sm { display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--text-muted); padding: 20px; }
.empty-hint.sm i { font-size: 24px; opacity: 0.3; }
.empty-hint.sm p { font-size: 12px; }

.slide-up-enter-active, .slide-up-leave-active { transition: opacity 0.4s, transform 0.4s; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(16px); }
</style>

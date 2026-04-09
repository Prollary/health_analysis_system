<template>
  <div class="page dashboard-page">
    <div class="page-header">
      <h1 class="page-title"><i class="fa-solid fa-gauge-high"></i> 健康大屏总览</h1>
      <span class="page-sub">{{ familyStore.currentMemberName ? `当前查看：${familyStore.currentMemberName}` : '个人健康数据' }}</span>
    </div>

    <!-- 行1：KPI 速览 -->
    <div class="kpi-row">
      <KpiCard icon="fa-wave-square"   label="平均心率" :value="kpi.heartRate" unit="bpm" :sub="kpi.hrSub"    :subClass="kpi.hrClass"    accent="red"    :loading="loading" />
      <KpiCard icon="fa-moon"          label="昨晚睡眠" :value="kpi.sleep"     unit="h"   :sub="kpi.sleepSub" :subClass="kpi.sleepClass" accent="blue"   :loading="loading" />
      <KpiCard icon="fa-person-walking" label="今日步数" :value="kpi.steps"    unit="步"  :sub="kpi.stepsSub" :subClass="kpi.stepsClass" accent="green"  :loading="loading" />
      <KpiCard icon="fa-robot"          label="健康评分" :value="kpi.score"    unit="分"  :sub="kpi.scoreSub" :subClass="kpi.scoreClass" accent="purple" :loading="loading" />
    </div>

    <!-- 行2：图表区 -->
    <div class="chart-row">
      <!-- 体征趋势折线图 -->
      <div class="card chart-main">
        <div class="card-header">
          <h2><i class="fa-solid fa-chart-line"></i> 7日体征趋势</h2>
        </div>
        <div ref="trendChartEl" class="echart-area"></div>
      </div>
      <!-- 健康雷达图 -->
      <div class="card chart-radar">
        <div class="card-header">
          <h2><i class="fa-solid fa-spider"></i> 健康维度评估</h2>
        </div>
        <div ref="radarChartEl" class="echart-area"></div>
      </div>
    </div>

    <!-- 行3：AI交互区 -->
    <div class="ai-row">
      <!-- 实时 AI 诊断 -->
      <div class="card ai-console">
        <div class="card-header">
          <h2><i class="fa-solid fa-wand-magic-sparkles"></i> 实时 AI 诊断</h2>
        </div>
        <form class="analyze-form" @submit.prevent="runAnalyze">
          <div class="form-grid">
            <div class="field-group">
              <label><i class="fa-solid fa-heart"></i> 即时心率</label>
              <input v-model.number="form.heart_rate" type="number" placeholder="例: 75" min="30" max="200" required />
            </div>
            <div class="field-group">
              <label><i class="fa-solid fa-bed"></i> 睡眠时长</label>
              <input v-model.number="form.sleep_hours" type="number" step="0.1" placeholder="例: 7.5" min="0" max="24" required />
            </div>
            <div class="field-group">
              <label><i class="fa-solid fa-shoe-prints"></i> 今日步数</label>
              <input v-model.number="form.steps" type="number" placeholder="例: 8000" min="0" required />
            </div>
            <div class="field-group">
              <label><i class="fa-solid fa-temperature-half"></i> 卧室温度</label>
              <input v-model.number="form.room_temp" type="number" step="0.1" placeholder="例: 24" min="10" max="40" />
            </div>
          </div>
          <button type="submit" class="btn-primary" :disabled="analyzing">
            <LoadingSpinner v-if="analyzing" height="20px" text="" />
            <span v-else><i class="fa-solid fa-brain"></i> 启动 AI 分析</span>
          </button>
        </form>
        <!-- 分析结果 -->
        <Transition name="fade">
          <div v-if="analysisResult" class="analysis-result">
            <div class="score-ring" :style="{ '--score-color': scoreColor }">
              <span class="score-num">{{ analysisResult.local?.health_score }}</span>
              <span class="score-label">健康分</span>
            </div>
            <div class="result-detail">
              <div class="risk-tag" :class="`risk-${analysisResult.local?.risk_level}`">
                {{ analysisResult.local?.risk_level }}
              </div>
              <p class="suggestion-text">{{ analysisResult.local?.suggestion }}</p>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 云端 AI 建议 -->
      <div class="card cloud-ai">
        <div class="card-header">
          <h2><i class="fa-solid fa-cloud-bolt"></i> 百度千帆 · 深度报告</h2>
          <button class="btn-outline sm" @click="generateFullReport" :disabled="generating">
            <i class="fa-solid fa-list-check"></i> 生成干预方案
          </button>
        </div>
        <LoadingSpinner v-if="generating" text="AI 深度分析中..." />
        <div v-else-if="cloudReport" class="cloud-report-text">
          <div class="report-content" v-html="formatReport(cloudReport)"></div>
        </div>
        <div v-else class="empty-hint">
          <i class="fa-solid fa-circle-info"></i>
          <p>先在左侧启动 AI 分析，或点击右上角生成详细干预方案</p>
        </div>
        <!-- PDF 下载 -->
        <a v-if="cloudReport" :href="pdfUrl" target="_blank" class="btn-download">
          <i class="fa-solid fa-file-pdf"></i> 下载本周健康周报 PDF
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import KpiCard from '@/components/common/KpiCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { healthApi, sensorApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'
import { useSosStore } from '@/stores/sos'

const authStore = useAuthStore()
const familyStore = useFamilyStore()
const sosStore = useSosStore()

const loading = ref(true)
const analyzing = ref(false)
const generating = ref(false)
const trendChartEl = ref(null)
const radarChartEl = ref(null)
let trendChart = null
let radarChart = null

const historyData = ref([])
const analysisResult = ref(null)
const cloudReport = ref('')

const form = reactive({
  heart_rate: null, sleep_hours: null, steps: null, room_temp: null,
  humidity: null, co2_level: null, user_id: null
})

const kpi = computed(() => {
  if (!historyData.value.length) return { heartRate: '--', sleep: '--', steps: '--', score: '--', hrSub: '', sleepSub: '', stepsSub: '', scoreSub: '', hrClass: '', sleepClass: '', stepsClass: '', scoreClass: '' }
  const latest = historyData.value[historyData.value.length - 1]
  const avgHr = Math.round(historyData.value.reduce((s, d) => s + d.heart_rate, 0) / historyData.value.length)
  return {
    heartRate: avgHr,
    sleep: latest.sleep_hours?.toFixed(1),
    steps: latest.steps?.toLocaleString(),
    score: latest.health_score || '--',
    hrSub: avgHr > 100 ? '偏高 ⚠' : avgHr < 55 ? '偏低 ⚠' : '正常范围',
    hrClass: avgHr > 100 || avgHr < 55 ? 'warn' : 'ok',
    sleepSub: (latest.sleep_hours >= 7) ? '睡眠充足' : '睡眠不足 ⚠',
    sleepClass: latest.sleep_hours >= 7 ? 'ok' : 'warn',
    stepsSub: latest.steps >= 8000 ? '达标 ✓' : '未达8000步目标',
    stepsClass: latest.steps >= 8000 ? 'ok' : 'warn',
    scoreSub: latest.risk_level || '',
    scoreClass: latest.risk_level === '高风险' ? 'danger' : latest.risk_level === '中风险' ? 'warn' : 'ok'
  }
})

const scoreColor = computed(() => {
  const s = analysisResult.value?.local?.health_score || 0
  if (s >= 80) return '#00d2a8'
  if (s >= 60) return '#ffa726'
  return '#ff4757'
})

const pdfUrl = computed(() => healthApi.getPdfUrl(familyStore.getTargetUserId()))

async function loadData() {
  // 首次加载时显示 loading，轮询时静默刷新（不重置 loading 防止闪烁）
  if (!historyData.value.length) loading.value = true
  try {
    const res = await healthApi.getHistory()
    historyData.value = Array.isArray(res) ? res : []
    renderTrendChart(historyData.value)
    renderRadarChart(historyData.value)
  } catch (e) {
    console.error('loadData error:', e)
  } finally {
    loading.value = false
  }
}

async function runAnalyze() {
  analyzing.value = true
  const userId = familyStore.getTargetUserId()
  // 先上传传感器数据
  try {
    const uploadRes = await sensorApi.upload({ ...form, user_id: userId })
    if (uploadRes.sos_alert) {
      sosStore.triggerSos(uploadRes.sos_msg)
    }
  } catch (e) { /* 可能后端直接处理 */ }

  try {
    const res = await healthApi.analyze(userId)
    if (res.code === 200) {
      analysisResult.value = res.data
      cloudReport.value = res.data.cloud_advice
    }
  } catch (e) {
    console.error(e)
  } finally {
    analyzing.value = false
  }
}

async function generateFullReport() {
  generating.value = true
  try {
    const res = await healthApi.generateReport(familyStore.getTargetUserId())
    if (res.code === 200) cloudReport.value = res.plan
  } catch (e) {
    console.error(e)
  } finally {
    generating.value = false
  }
}

function formatReport(text) {
  return text.replace(/\n/g, '<br>').replace(/【(.+?)】/g, '<strong>【$1】</strong>')
}

function renderTrendChart(data) {
  if (!trendChart) return
  const dates = data.map(d => d.timestamp?.slice(5, 10) || '')
  const hrs = data.map(d => d.heart_rate)
  const sleeps = data.map(d => d.sleep_hours)
  const steps = data.map(d => d.steps)

  trendChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#1e2535', borderColor: '#2d3748', textStyle: { color: '#e2e8f0' } },
    legend: { data: ['心率', '睡眠', '步数'], textStyle: { color: '#94a3b8' }, top: 0 },
    grid: { left: 40, right: 60, top: 36, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: dates, axisLabel: { color: '#64748b' }, axisLine: { lineStyle: { color: '#2d3748' } } },
    yAxis: [
      { type: 'value', name: 'bpm/h', nameTextStyle: { color: '#64748b', fontSize: 11 }, axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#1e2535' } } },
      { type: 'value', name: '步', nameTextStyle: { color: '#64748b', fontSize: 11 }, axisLabel: { color: '#64748b' }, splitLine: { show: false } }
    ],
    series: [
      { name: '心率', type: 'line', data: hrs, smooth: true, symbol: 'circle', symbolSize: 6, yAxisIndex: 0,
        lineStyle: { color: '#ff4757', width: 2 }, itemStyle: { color: '#ff4757' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(255,71,87,0.3)' }, { offset: 1, color: 'transparent' }] } }
      },
      { name: '睡眠', type: 'line', data: sleeps, smooth: true, symbol: 'circle', symbolSize: 6, yAxisIndex: 0,
        lineStyle: { color: '#0d84ff', width: 2 }, itemStyle: { color: '#0d84ff' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(13,132,255,0.25)' }, { offset: 1, color: 'transparent' }] } }
      },
      { name: '步数', type: 'bar', data: steps, yAxisIndex: 1, barMaxWidth: 20,
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(0,210,168,0.8)' }, { offset: 1, color: 'rgba(0,210,168,0.1)' }] } }
      }
    ]
  })
}

function renderRadarChart(data) {
  if (!radarChart || !data.length) return
  const latest = data[data.length - 1]
  const hrScore = Math.max(0, 100 - Math.abs(latest.heart_rate - 75) * 2)
  const sleepScore = Math.min(100, (latest.sleep_hours / 8) * 100)
  const stepsScore = Math.min(100, (latest.steps / 10000) * 100)
  const tempScore = latest.room_temp ? Math.max(0, 100 - Math.abs(latest.room_temp - 22) * 6) : 70
  const co2Score = latest.co2_level ? Math.max(0, 100 - Math.max(0, latest.co2_level - 600) / 10) : 80
  const overall = (hrScore + sleepScore + stepsScore + tempScore + co2Score) / 5

  radarChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { backgroundColor: '#1e2535', borderColor: '#2d3748', textStyle: { color: '#e2e8f0' } },
    radar: {
      indicator: [
        { name: '心率健康', max: 100 }, { name: '睡眠质量', max: 100 },
        { name: '运动达标', max: 100 }, { name: '室内环境', max: 100 },
        { name: '空气质量', max: 100 }, { name: '综合评分', max: 100 }
      ],
      splitArea: { areaStyle: { color: ['rgba(13,132,255,0.03)', 'rgba(13,132,255,0.06)'] } },
      axisLine: { lineStyle: { color: '#2d3748' } },
      splitLine: { lineStyle: { color: '#2d3748' } },
      axisName: { color: '#94a3b8', fontSize: 11 }
    },
    series: [{
      type: 'radar',
      data: [{ value: [hrScore, sleepScore, stepsScore, tempScore, co2Score, overall], name: '当前状态',
        areaStyle: { color: 'rgba(13,132,255,0.2)' },
        lineStyle: { color: '#0d84ff', width: 2 },
        itemStyle: { color: '#0d84ff' }
      }]
    }]
  })
}

// 响应 family 成员切换，重新加载
watch(() => familyStore.currentMemberId, () => {
  loadData()
})

let pollTimer = null

onMounted(async () => {
  // 先初始化图表实例，再加载数据（避免 renderXxx 时 chart 为 null）
  trendChart = echarts.init(trendChartEl.value, null, { renderer: 'canvas' })
  radarChart  = echarts.init(radarChartEl.value, null, { renderer: 'canvas' })
  window.addEventListener('resize', handleResize)

  await loadData()

  // 每 5 秒轮询一次，同步 simulator 写入的最新数据
  pollTimer = setInterval(loadData, 5000)
})

onUnmounted(() => {
  clearInterval(pollTimer)
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  radarChart?.dispose()
})

function handleResize() {
  trendChart?.resize()
  radarChart?.resize()
}
</script>

<style scoped>
.dashboard-page { display: flex; flex-direction: column; gap: 20px; }

/* KPI 行 */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }

/* 图表行 */
.chart-row { display: grid; grid-template-columns: 7fr 3fr; gap: 16px; }
.chart-main, .chart-radar { min-height: 300px; }
.echart-area { height: 260px; }

/* AI 行 */
.ai-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

/* 分析表单 */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
.field-group { display: flex; flex-direction: column; gap: 6px; }
.field-group label { font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; }
.field-group input {
  background: var(--bg-deep);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 9px 12px;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.field-group input:focus { border-color: var(--primary); }

/* 分析结果 */
.analysis-result {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-deep);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}
.score-ring {
  width: 76px; height: 76px;
  border-radius: 50%;
  border: 3px solid var(--score-color, #0d84ff);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 0 16px rgba(0,0,0,0.2);
}
.score-num { font-size: 22px; font-weight: 700; color: var(--text-primary); line-height: 1; }
.score-label { font-size: 10px; color: var(--text-muted); }
.result-detail { flex: 1; }
.risk-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}
.risk-低风险 { background: rgba(0,210,168,0.2); color: var(--success); }
.risk-中风险 { background: rgba(255,167,38,0.2); color: var(--warning); }
.risk-高风险 { background: rgba(255,71,87,0.2);  color: var(--danger);  }
.suggestion-text { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }

/* 云端报告 */
.cloud-report-text {
  flex: 1;
  overflow-y: auto;
  max-height: 240px;
  padding-right: 4px;
}
.report-content { font-size: 13px; color: var(--text-secondary); line-height: 1.8; }
.empty-hint {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--text-muted);
}
.empty-hint i { font-size: 28px; opacity: 0.4; }
.empty-hint p { font-size: 13px; text-align: center; }

.btn-download {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px;
  background: rgba(255,71,87,0.1);
  border: 1px solid var(--danger);
  border-radius: 10px;
  color: var(--danger);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.2s;
}
.btn-download:hover { background: rgba(255,71,87,0.2); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s, transform 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(8px); }
</style>

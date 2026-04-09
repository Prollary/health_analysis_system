<template>
  <div class="page report-page">
    <div class="page-header">
      <h1 class="page-title"><i class="fa-solid fa-file-waveform"></i> 健康报告中心</h1>
    </div>

    <!-- 操作栏 -->
    <div class="card action-bar">
      <div class="period-tabs">
        <button v-for="p in periods" :key="p.val" :class="{ active: period === p.val }" @click="period = p.val">{{ p.label }}</button>
      </div>
      <div class="action-btns">
        <button class="btn-primary" @click="generateReport" :disabled="generating">
          <LoadingSpinner v-if="generating" height="20px" text="" />
          <span v-else><i class="fa-solid fa-wand-magic-sparkles"></i> 生成 AI 干预方案</span>
        </button>
        <a :href="pdfUrl" target="_blank" class="btn-download">
          <i class="fa-solid fa-file-pdf"></i> 下载 PDF 周报
        </a>
      </div>
    </div>

    <!-- 评分趋势 + 本周总评 -->
    <div class="overview-row">
      <div class="card flex-grow">
        <div class="card-header">
          <h2><i class="fa-solid fa-chart-line"></i> 健康评分趋势</h2>
        </div>
        <div ref="scoreChartEl" class="echart-area"></div>
      </div>
      <div class="card summary-card">
        <div class="card-header">
          <h2><i class="fa-solid fa-star"></i> 本期总评</h2>
        </div>
        <div class="summary-body">
          <div class="big-score" :style="{ color: scoreColor }">{{ weekScore }}</div>
          <div class="score-ring-outer" :style="{ '--pct': weekScore / 100 }">
            <svg viewBox="0 0 80 80">
              <circle cx="40" cy="40" r="34" fill="none" stroke="var(--border-color)" stroke-width="6"/>
              <circle cx="40" cy="40" r="34" fill="none" :stroke="scoreColor" stroke-width="6"
                stroke-dasharray="213.6" :stroke-dashoffset="213.6 * (1 - weekScore / 100)"
                stroke-linecap="round" transform="rotate(-90 40 40)" style="transition: stroke-dashoffset 1s ease"/>
            </svg>
          </div>
          <div class="summary-items">
            <div class="sum-item">
              <span>风险等级</span>
              <span :class="`risk-${weekRisk}`">{{ weekRisk }}</span>
            </div>
            <div class="sum-item">
              <span>环比上周</span>
              <span :class="weekDelta >= 0 ? 'up' : 'down'">{{ weekDelta >= 0 ? '↑' : '↓' }} {{ Math.abs(weekDelta) }} 分</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 个性化干预方案 -->
    <Transition name="slide-up">
      <div v-if="interventionPlan" class="intervention-row">
        <div class="card diet-card">
          <div class="card-header">
            <h2><i class="fa-solid fa-bowl-rice"></i> 饮食推荐方案</h2>
            <span class="plan-badge">AI 个性化生成</span>
          </div>
          <div class="plan-content" v-html="formatPlan(dietPlan)"></div>
        </div>
        <div class="card exercise-card">
          <div class="card-header">
            <h2><i class="fa-solid fa-dumbbell"></i> 运动处方</h2>
            <span class="plan-badge">AI 个性化生成</span>
          </div>
          <div class="plan-content" v-html="formatPlan(exercisePlan)"></div>
        </div>
      </div>
    </Transition>

    <!-- 加载占位 -->
    <div v-if="generating" class="card">
      <LoadingSpinner text="百度千帆大模型深度分析中，请稍候..." height="140px" />
    </div>

    <!-- 历史报告列表 -->
    <div class="card">
      <div class="card-header">
        <h2><i class="fa-solid fa-history"></i> 历史报告记录</h2>
      </div>
      <div v-if="historyData.length" class="report-table">
        <div class="rt-header">
          <span>时间</span><span>健康评分</span><span>风险等级</span><span>AI 建议摘要</span>
        </div>
        <div v-for="r in historyData.slice(0, 10)" :key="r.id" class="rt-row">
          <span>{{ formatDate(r.timestamp) }}</span>
          <span class="score-val" :style="{ color: getScoreColor(r.health_score) }">{{ r.health_score || '--' }}</span>
          <span :class="`risk-${r.risk_level}`">{{ r.risk_level || '--' }}</span>
          <span class="advice-excerpt">{{ r.ai_suggestion?.slice(0, 50) }}...</span>
        </div>
      </div>
      <div v-else class="empty-hint">
        <i class="fa-solid fa-file-circle-xmark"></i>
        <p>暂无报告记录，先在总览页进行 AI 分析</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { healthApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'

const authStore = useAuthStore()
const familyStore = useFamilyStore()
const scoreChartEl = ref(null)
let scoreChart = null

const period = ref('week')
const generating = ref(false)
const historyData = ref([])
const interventionPlan = ref('')

const periods = [
  { val: 'week', label: '本周' },
  { val: 'lastweek', label: '上周' },
  { val: 'month', label: '本月' }
]

// 模拟周评分
const weekScore = computed(() => {
  if (!historyData.value.length) return 0
  const scores = historyData.value.map(d => d.health_score).filter(Boolean)
  return scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0
})
const weekRisk = computed(() => weekScore.value >= 80 ? '低风险' : weekScore.value >= 60 ? '中风险' : '高风险')
const weekDelta = ref(5) // 模拟
const scoreColor = computed(() => getScoreColor(weekScore.value))

// 干预方案解析（从百度AI返回的大段文本中分段）
const dietPlan = computed(() => {
  if (!interventionPlan.value) return ''
  const idx = interventionPlan.value.indexOf('饮食')
  const idx2 = interventionPlan.value.indexOf('运动')
  return idx !== -1 && idx2 !== -1 ? interventionPlan.value.slice(idx, idx2) : interventionPlan.value.slice(0, Math.floor(interventionPlan.value.length / 2))
})
const exercisePlan = computed(() => {
  if (!interventionPlan.value) return ''
  const idx = interventionPlan.value.indexOf('运动')
  return idx !== -1 ? interventionPlan.value.slice(idx) : interventionPlan.value.slice(Math.floor(interventionPlan.value.length / 2))
})

const pdfUrl = computed(() => healthApi.getPdfUrl(familyStore.getTargetUserId()))

function getScoreColor(score) {
  if (!score) return '#64748b'
  return score >= 80 ? '#00d2a8' : score >= 60 ? '#ffa726' : '#ff4757'
}

function formatDate(ts) {
  if (!ts) return '--'
  return (ts.slice ? ts.slice(0, 10) : String(ts))
}

function formatPlan(text) {
  return (text || '').replace(/\n/g, '<br>').replace(/【(.+?)】/g, '<strong class="plan-section">【$1】</strong>').replace(/(\d+[.、])/g, '<br>$1')
}

async function loadData() {
  try {
    const res = await healthApi.getHistory()
    historyData.value = res
    renderScoreChart(res)
  } catch (e) { console.error(e) }
}

async function generateReport() {
  generating.value = true
  try {
    const res = await healthApi.generateReport(familyStore.getTargetUserId())
    if (res.code === 200) interventionPlan.value = res.plan
  } catch (e) {
    alert('生成失败：' + (e.message || '请重试'))
  } finally {
    generating.value = false
  }
}

function renderScoreChart(data) {
  if (!scoreChart) return
  const labels = data.map((_, i) => `记录${i + 1}`)
  const scores = data.map(d => d.health_score || 0)
  scoreChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#1e2535', borderColor: '#2d3748', textStyle: { color: '#e2e8f0' },
      formatter: p => `${p[0].axisValue}<br>健康分: <strong>${p[0].data}</strong>` },
    grid: { left: 40, right: 20, top: 30, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: labels, axisLabel: { color: '#64748b' }, axisLine: { lineStyle: { color: '#2d3748' } } },
    yAxis: { type: 'value', min: 0, max: 100, axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#1e2535' } } },
    visualMap: { show: false, pieces: [{ lt: 60, color: '#ff4757' }, { gte: 60, lt: 80, color: '#ffa726' }, { gte: 80, color: '#00d2a8' }] },
    series: [{
      type: 'line', data: scores, smooth: true, symbol: 'circle', symbolSize: 8,
      lineStyle: { width: 3 },
      areaStyle: { opacity: 0.2 },
      markLine: {
        silent: true,
        data: [
          { yAxis: 80, lineStyle: { color: '#00d2a8', type: 'dashed' }, label: { formatter: '80 优秀', color: '#00d2a8' } },
          { yAxis: 60, lineStyle: { color: '#ffa726', type: 'dashed' }, label: { formatter: '60 警戒', color: '#ffa726' } }
        ]
      }
    }]
  })
}

watch(period, loadData)

onMounted(async () => {
  await loadData()
  scoreChart = echarts.init(scoreChartEl.value)
  if (historyData.value.length) renderScoreChart(historyData.value)
  window.addEventListener('resize', () => scoreChart?.resize())
})
onUnmounted(() => scoreChart?.dispose())
</script>

<style scoped>
.report-page { display: flex; flex-direction: column; gap: 20px; }

/* 操作栏 */
.action-bar { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.period-tabs { display: flex; background: var(--bg-deep); border-radius: 8px; padding: 3px; }
.period-tabs button {
  padding: 6px 16px; border: none; border-radius: 6px; background: none;
  color: var(--text-muted); font-size: 13px; cursor: pointer; transition: all 0.2s;
}
.period-tabs button.active { background: var(--primary); color: white; font-weight: 600; }
.action-btns { display: flex; gap: 10px; align-items: center; }

.btn-download {
  display: flex; align-items: center; gap: 6px;
  padding: 9px 16px;
  background: rgba(255,71,87,0.1); border: 1px solid var(--danger); border-radius: 10px;
  color: var(--danger); text-decoration: none; font-size: 13px; font-weight: 600;
  transition: background 0.2s;
}
.btn-download:hover { background: rgba(255,71,87,0.2); }

/* 总览行 */
.overview-row { display: grid; grid-template-columns: 1fr 240px; gap: 16px; }
.flex-grow { flex: 1; }
.echart-area { height: 260px; }

/* 总评卡 */
.summary-body { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 8px 0; }
.big-score { font-size: 48px; font-weight: 800; line-height: 1; }
.score-ring-outer { width: 80px; height: 80px; position: relative; margin-top: -60px; opacity: 0.3; }
.score-ring-outer svg { width: 100%; height: 100%; }
.summary-items { width: 100%; display: flex; flex-direction: column; gap: 8px; }
.sum-item { display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0; border-bottom: 1px solid var(--border-color); }
.sum-item span:first-child { color: var(--text-muted); }
.up   { color: var(--success); font-weight: 600; }
.down { color: var(--danger);  font-weight: 600; }
.risk-低风险 { color: var(--success); font-weight: 600; }
.risk-中风险 { color: var(--warning); font-weight: 600; }
.risk-高风险 { color: var(--danger);  font-weight: 600; }

/* 干预方案 */
.intervention-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.plan-badge {
  font-size: 11px; padding: 2px 8px;
  background: rgba(13,132,255,0.15); color: var(--primary);
  border-radius: 12px;
}
.plan-content { font-size: 13px; color: var(--text-secondary); line-height: 1.8; max-height: 220px; overflow-y: auto; }

/* 报告表格 */
.report-table { display: flex; flex-direction: column; gap: 6px; }
.rt-header {
  display: grid; grid-template-columns: 120px 80px 80px 1fr;
  padding: 8px 12px; background: var(--bg-deep); border-radius: 6px;
  font-size: 11px; color: var(--text-muted); font-weight: 600;
}
.rt-row {
  display: grid; grid-template-columns: 120px 80px 80px 1fr;
  padding: 10px 12px; border: 1px solid var(--border-color); border-radius: 8px;
  font-size: 13px; align-items: center;
  transition: background 0.2s;
}
.rt-row:hover { background: rgba(13,132,255,0.04); }
.score-val { font-weight: 700; }
.advice-excerpt { color: var(--text-muted); font-size: 12px; }

.empty-hint { display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--text-muted); padding: 32px; }
.empty-hint i { font-size: 32px; opacity: 0.3; }
.empty-hint p { font-size: 13px; }

.slide-up-enter-active, .slide-up-leave-active { transition: opacity 0.4s, transform 0.4s; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(16px); }
</style>

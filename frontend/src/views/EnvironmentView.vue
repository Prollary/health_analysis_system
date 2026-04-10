<template>
  <div class="page env-page">
    <div class="page-header">
      <h1 class="page-title"><i class="fa-solid fa-house-signal"></i> 环境-健康联动分析</h1>
    </div>

    <!-- 行1：环境 KPI -->
    <div class="kpi-row">
      <KpiCard icon="fa-temperature-half" label="卧室温度" :value="envKpi.temp"     unit="℃"   :sub="envKpi.tempSub"     :subClass="envKpi.tempClass"     accent="orange" :loading="loading" />
      <KpiCard icon="fa-droplet"          label="相对湿度" :value="envKpi.humidity" unit="%"   :sub="envKpi.humiditySub" :subClass="envKpi.humidityClass" accent="blue"   :loading="loading" />
      <KpiCard icon="fa-wind"             label="CO₂ 浓度" :value="envKpi.co2"      unit="ppm" :sub="envKpi.co2Sub"      :subClass="envKpi.co2Class"      accent="green"  :loading="loading" />
    </div>

    <!-- 行2：散点图 + 双折线图 -->
    <div class="chart-row">
      <div class="card">
        <div class="card-header">
          <h2><i class="fa-solid fa-circle-dot"></i> 室温 vs 睡眠时长（散点图）</h2>
        </div>
        <div ref="scatterEl" class="echart-area"></div>
        <p class="chart-hint">每个点代表一天的数据，红色趋势线揭示相关性</p>
      </div>
      <div class="card">
        <div class="card-header">
          <h2><i class="fa-solid fa-chart-line"></i> 7日环境趋势（双Y轴）</h2>
        </div>
        <div ref="envTrendEl" class="echart-area"></div>
      </div>
    </div>

    <!-- 行3：预警面板 + AI建议 -->
    <div class="alert-row">
      <!-- 久坐+CO2 联动预警 -->
      <div class="card alert-panel">
        <div class="card-header">
          <h2><i class="fa-solid fa-triangle-exclamation"></i> 联动预警状态</h2>
        </div>
        <div class="traffic-lights">
          <div class="traffic-item" :class="alerts.sedentary ? 'active-warn' : 'normal'">
            <div class="light-dot"></div>
            <div class="traffic-info">
              <strong>久坐检测</strong>
              <span>{{ alerts.sedentary ? '已连续久坐 2h+，建议起身活动' : '活动正常' }}</span>
            </div>
          </div>
          <div class="traffic-item" :class="alerts.co2High ? 'active-danger' : 'normal'">
            <div class="light-dot"></div>
            <div class="traffic-info">
              <strong>CO₂ 浓度</strong>
              <span>{{ alerts.co2High ? `${envKpi.co2} ppm 偏高，建议开窗通风` : '空气质量良好' }}</span>
            </div>
          </div>
          <div class="traffic-item" :class="alerts.tempBad ? 'active-warn' : 'normal'">
            <div class="light-dot"></div>
            <div class="traffic-info">
              <strong>睡眠温度</strong>
              <span>{{ alerts.tempBad ? `室温 ${envKpi.temp}℃ 不利睡眠，建议 20-24℃` : '温度适宜' }}</span>
            </div>
          </div>
        </div>

        <!-- 综合预警触发时显示 -->
        <Transition name="fade">
          <div v-if="alerts.sedentary && alerts.co2High" class="compound-alert">
            <i class="fa-solid fa-radiation"></i>
            <div>
              <strong>疲劳风险预警</strong>
              <p>检测到久坐 + CO₂ 偏高同时触发，存在疲劳积累风险。<br>建议立即开窗通风并起身活动 5 分钟。</p>
            </div>
          </div>
        </Transition>
      </div>

      <!-- AI 环境建议 -->
      <div class="card ai-env-advice">
        <div class="card-header">
          <h2><i class="fa-solid fa-robot"></i> AI 环境健康建议</h2>
        </div>
        <div class="advice-list">
          <div v-for="(tip, i) in envTips" :key="i" class="advice-item" :class="tip.level">
            <i :class="`fa-solid ${tip.icon}`"></i>
            <p>{{ tip.text }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import KpiCard from '@/components/common/KpiCard.vue'
import { healthApi } from '@/api'

const loading = ref(true)
const scatterEl = ref(null)
const envTrendEl = ref(null)
let scatterChart = null
let envTrendChart = null
const historyData = ref([])

const envKpi = computed(() => {
  if (!historyData.value.length) return { temp: '--', humidity: '--', co2: '--', tempSub: '', humiditySub: '', co2Sub: '', tempClass: '', humidityClass: '', co2Class: '' }

  // 从尾部向前找第一条各字段不为 null 的记录（兼容旧数据库记录）
  const arr = [...historyData.value].reverse()
  const tempVal = (arr.find(d => d.room_temp  != null)?.room_temp  != null) ? parseFloat(arr.find(d => d.room_temp  != null).room_temp)  : null
  const humVal  = (arr.find(d => d.humidity   != null)?.humidity   != null) ? parseFloat(arr.find(d => d.humidity   != null).humidity)   : null
  const co2Val  = (arr.find(d => d.co2_level  != null)?.co2_level  != null) ? parseInt(arr.find(d  => d.co2_level  != null).co2_level)   : null

  // 显示用字符串
  const temp = tempVal != null ? tempVal.toFixed(1) : '--'
  const hum  = humVal  != null ? humVal.toFixed(0)  : '--'
  const co2  = co2Val  != null ? co2Val              : '--'

  return {
    temp, humidity: hum, co2,
    // 全部用数值变量比较，避免字符串比较陷阱
    tempSub:      tempVal == null ? '' : tempVal > 26 ? '偏高，影响睡眠 ⚠' : tempVal < 18 ? '偏低 ⚠' : '舒适范围',
    tempClass:    tempVal == null ? '' : (tempVal > 26 || tempVal < 18) ? 'warn' : 'ok',
    humiditySub:  humVal  == null ? '' : (humVal >= 40 && humVal <= 65) ? '湿度适宜' : '湿度异常 ⚠',
    humidityClass:humVal  == null ? '' : (humVal >= 40 && humVal <= 65) ? 'ok' : 'warn',
    co2Sub:       co2Val  == null ? '' : co2Val > 1000 ? '严重偏高 ⚠' : co2Val > 800 ? '偏高，建议通风' : '空气质量良好',
    co2Class:     co2Val  == null ? '' : co2Val > 1000 ? 'danger' : co2Val > 800 ? 'warn' : 'ok'
  }
})

const alerts = computed(() => {
  if (!historyData.value.length) return {}
  const arr = [...historyData.value].reverse()
  const latest   = historyData.value[historyData.value.length - 1]
  const co2Val   = arr.find(d => d.co2_level != null)?.co2_level
  const tempVal  = arr.find(d => d.room_temp != null)?.room_temp
  return {
    sedentary: latest.steps != null && latest.steps < 200,
    co2High:   co2Val  != null && co2Val  > 800,
    tempBad:   tempVal != null && (tempVal > 26 || tempVal < 18)
  }
})

const envTips = computed(() => {
  const tips = []
  const a = alerts.value
  const k = envKpi.value
  if (a.tempBad) tips.push({ icon: 'fa-temperature-half', level: 'warn', text: `AI 检测到室温 ${k.temp}℃，当室温高于 26℃ 时睡眠质量明显下降，建议今晚开启空调睡眠模式（设定 22-24℃）。` })
  else tips.push({ icon: 'fa-check-circle', level: 'ok', text: `当前室温 ${k.temp}℃，处于最佳睡眠温度区间（20-24℃），有利于深度睡眠。` })
  if (a.co2High) tips.push({ icon: 'fa-wind', level: 'warn', text: `室内 CO₂ 浓度 ${k.co2} ppm 超标，长时间处于高 CO₂ 环境会导致注意力下降和疲劳感，请立即开窗通风 15 分钟。` })
  else tips.push({ icon: 'fa-leaf', level: 'ok', text: '室内空气质量良好，CO₂ 浓度在正常范围内（400-800 ppm），可正常活动。' })
  if (a.sedentary) tips.push({ icon: 'fa-person-walking', level: 'danger', text: '检测到今日活动量极低，可能存在长时间久坐。建议每 45 分钟起身活动 5 分钟，有助于促进血液循环。' })
  return tips
})

async function loadData() {
  loading.value = true
  try {
    const res = await healthApi.getHistory()
    historyData.value = res
    await renderCharts(res)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function renderCharts(data) {
  await new Promise(r => setTimeout(r, 100))
  renderScatter(data)
  renderEnvTrend(data)
}

function renderScatter(data) {
  if (!scatterChart) return
  const points = data.map(d => [d.room_temp, d.sleep_hours])
  scatterChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { formatter: p => `室温: ${p.data[0]}℃<br>睡眠: ${p.data[1]}h` },
    grid: { left: 40, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: 'value', name: '卧室温度(℃)', nameLocation: 'middle', nameGap: 28, min: 14, max: 32,
      axisLabel: { color: '#64748b' }, axisLine: { lineStyle: { color: '#2d3748' } }, splitLine: { lineStyle: { color: '#1e2535' } } },
    yAxis: { type: 'value', name: '睡眠(h)', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#1e2535' } } },
    series: [
      { type: 'scatter', data: points, symbolSize: 10, itemStyle: { color: '#0d84ff', opacity: 0.8 } },
      // 标注最佳区间
      { type: 'line', markArea: {
          itemStyle: { color: 'rgba(0,210,168,0.07)' },
          data: [[{ xAxis: 20 }, { xAxis: 24 }]]
        },
        data: [], silent: true
      }
    ]
  })
}

function renderEnvTrend(data) {
  if (!envTrendChart) return
  const dates = data.map(d => d.timestamp?.slice(5, 10) || '')
  scatterChart?.resize()
  envTrendChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#1e2535', borderColor: '#2d3748', textStyle: { color: '#e2e8f0' } },
    legend: { data: ['室温', 'CO₂'], textStyle: { color: '#94a3b8' }, top: 0 },
    grid: { left: 40, right: 60, top: 36, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: dates, axisLabel: { color: '#64748b' }, axisLine: { lineStyle: { color: '#2d3748' } } },
    yAxis: [
      { type: 'value', name: '℃', min: 10, max: 40, axisLabel: { color: '#64748b', formatter: '{value}℃' }, splitLine: { lineStyle: { color: '#1e2535' } } },
      { type: 'value', name: 'ppm', axisLabel: { color: '#64748b' }, splitLine: { show: false } }
    ],
    series: [
      { name: '室温', type: 'line', smooth: true, yAxisIndex: 0,
        data: data.map(d => d.room_temp?.toFixed(1)),
        lineStyle: { color: '#ffa726', width: 2 }, itemStyle: { color: '#ffa726' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(255,167,38,0.3)' }, { offset: 1, color: 'transparent' }] } },
        // 标注危险线
        markLine: { data: [{ yAxis: 26, lineStyle: { color: '#ff4757', type: 'dashed' }, label: { formatter: '26℃警戒' } }], silent: true }
      },
      { name: 'CO₂', type: 'line', smooth: true, yAxisIndex: 1,
        data: data.map(d => d.co2_level),
        lineStyle: { color: '#00d2a8', width: 2 }, itemStyle: { color: '#00d2a8' },
        markLine: { data: [{ yAxis: 800, lineStyle: { color: '#ffa726', type: 'dashed' }, label: { formatter: '800ppm警戒' } }], silent: true }
      }
    ]
  })
}

let pollTimer = null

onMounted(async () => {
  scatterChart  = echarts.init(scatterEl.value)
  envTrendChart = echarts.init(envTrendEl.value)
  window.addEventListener('resize', handleResize)
  await loadData()
  pollTimer = setInterval(loadData, 5000)
})
onUnmounted(() => {
  clearInterval(pollTimer)
  window.removeEventListener('resize', handleResize)
  scatterChart?.dispose()
  envTrendChart?.dispose()
})
function handleResize() { scatterChart?.resize(); envTrendChart?.resize() }
</script>

<style scoped>
.env-page { display: flex; flex-direction: column; gap: 20px; }
.kpi-row   { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.alert-row { display: grid; grid-template-columns: 5fr 7fr; gap: 16px; }
.echart-area { height: 250px; }
.chart-hint { font-size: 11px; color: var(--text-muted); text-align: center; margin-top: 6px; }

/* 交通灯预警 */
.traffic-lights { display: flex; flex-direction: column; gap: 12px; }
.traffic-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid transparent;
  transition: all 0.3s;
}
.traffic-item.normal       { background: rgba(0,210,168,0.06);  border-color: rgba(0,210,168,0.2);  }
.traffic-item.active-warn  { background: rgba(255,167,38,0.1);  border-color: rgba(255,167,38,0.4); }
.traffic-item.active-danger{ background: rgba(255,71,87,0.1);   border-color: rgba(255,71,87,0.4);  }

.light-dot {
  width: 12px; height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}
.normal .light-dot        { background: var(--success); box-shadow: 0 0 6px var(--success); }
.active-warn .light-dot   { background: var(--warning); box-shadow: 0 0 6px var(--warning); animation: blink 1s infinite; }
.active-danger .light-dot { background: var(--danger);  box-shadow: 0 0 6px var(--danger);  animation: blink 0.6s infinite; }
@keyframes blink { 0%,100% { opacity:1 } 50% { opacity:0.3 } }

.traffic-info strong { display: block; font-size: 13px; color: var(--text-primary); }
.traffic-info span   { font-size: 12px; color: var(--text-muted); }

/* 综合预警 */
.compound-alert {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-top: 14px;
  padding: 14px;
  background: rgba(255,71,87,0.1);
  border: 1px solid var(--danger);
  border-radius: 10px;
  color: var(--danger);
  animation: sos-flash 1.5s infinite;
}
@keyframes sos-flash { 0%,100%{border-color:var(--danger)} 50%{border-color:transparent} }
.compound-alert i { font-size: 20px; margin-top: 2px; flex-shrink: 0; }
.compound-alert strong { display: block; font-size: 14px; margin-bottom: 4px; }
.compound-alert p { font-size: 12px; line-height: 1.6; color: var(--text-secondary); }

/* AI 建议 */
.advice-list { display: flex; flex-direction: column; gap: 10px; }
.advice-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 14px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.6;
}
.advice-item i { font-size: 16px; margin-top: 2px; flex-shrink: 0; }
.advice-item.ok     { background: rgba(0,210,168,0.06);  border-left: 3px solid var(--success); }
.advice-item.ok i   { color: var(--success); }
.advice-item.warn   { background: rgba(255,167,38,0.08); border-left: 3px solid var(--warning); }
.advice-item.warn i { color: var(--warning); }
.advice-item.danger { background: rgba(255,71,87,0.08);  border-left: 3px solid var(--danger); }
.advice-item.danger i { color: var(--danger); }
.advice-item p { color: var(--text-secondary); margin: 0; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s, transform 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(6px); }
</style>

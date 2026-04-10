<template>
  <div class="page care-page">
    <div class="page-header">
      <h1 class="page-title"><i class="fa-solid fa-heart-circle-check"></i> 居家看护中心</h1>
    </div>

    <!-- 家庭成员选择条 -->
    <div class="card member-bar">
      <div class="bar-label"><i class="fa-solid fa-users"></i> 家庭成员</div>
      <div class="member-list">
        <div
          class="member-chip"
          :class="{ selected: selectedId === authStore.userId }"
          @click="selectMember(authStore.userId, authStore.username)"
        >
          <img :src="`https://api.dicebear.com/7.x/notionists/svg?seed=${authStore.username}`" class="chip-avatar" />
          <span>{{ authStore.username }}（我）</span>
        </div>
        <div
          v-for="m in familyStore.members"
          :key="m.id"
          class="member-chip"
          :class="{ selected: selectedId === m.id }"
          @click="selectMember(m.id, m.name)"
        >
          <img :src="`https://api.dicebear.com/7.x/notionists/svg?seed=${m.name}`" class="chip-avatar" />
          <span>{{ m.name }}</span>
        </div>
      </div>
    </div>

    <!-- 成员信息 + 心率趋势 -->
    <div class="monitor-row">
      <div class="card member-profile">
        <div class="profile-avatar">
          <img :src="`https://api.dicebear.com/7.x/notionists/svg?seed=${selectedName}`" />
        </div>
        <h3 class="profile-name">{{ selectedName }}</h3>
        <div class="profile-items">
          <div class="profile-item">
            <span class="pi-label">当前心率</span>
            <span class="pi-val red">{{ latestData && latestData.heart_rate || '--' }} bpm</span>
          </div>
          <div class="profile-item">
            <span class="pi-label">昨晚睡眠</span>
            <span class="pi-val">{{ latestData && latestData.sleep_hours && latestData.sleep_hours.toFixed(1) || '--' }} h</span>
          </div>
          <div class="profile-item">
            <span class="pi-label">今日步数</span>
            <span class="pi-val">{{ formatSteps(latestData) }}</span>
          </div>
          <div class="profile-item">
            <span class="pi-label">风险等级</span>
            <span class="pi-val" :class="`risk-${latestData && latestData.risk_level}`">{{ latestData && latestData.risk_level || '--' }}</span>
          </div>
        </div>
        <div class="sos-status" :class="sosStore.triggered ? 'danger' : 'safe'">
          <i :class="sosStore.triggered ? 'fa-solid fa-siren-on' : 'fa-solid fa-shield-heart'"></i>
          {{ sosStore.triggered ? '当前有未处理告警' : '生命体征正常' }}
        </div>
      </div>

      <!-- 24h 心率趋势图（带阈值线） -->
      <div class="card flex-grow">
        <div class="card-header">
          <h2><i class="fa-solid fa-chart-line"></i> 近期心率监控（含 SOS 阈值）</h2>
        </div>
        <div ref="careChartEl" class="echart-area"></div>
      </div>
    </div>

    <!-- 告警历史 + SOS设置 -->
    <div class="bottom-row">
      <div class="card">
        <div class="card-header">
          <h2><i class="fa-solid fa-bell"></i> 告警历史记录</h2>
        </div>
        <div v-if="sosStore.alertHistory.length" class="alert-table">
          <div class="alert-row-header">
            <span>时间</span><span>告警内容</span>
          </div>
          <div v-for="a in sosStore.alertHistory" :key="a.id" class="alert-row-item">
            <span class="alert-time">{{ a.time }}</span>
            <span class="alert-msg">{{ a.msg }}</span>
          </div>
        </div>
        <div v-else class="empty-hint">
          <i class="fa-solid fa-circle-check"></i>
          <p>暂无告警记录，一切正常</p>
        </div>
      </div>

      <!-- SOS 设置 -->
      <div class="card sos-settings">
        <div class="card-header">
          <h2><i class="fa-solid fa-gear"></i> SOS 紧急联系设置</h2>
        </div>
        <div class="settings-form">
          <div class="field-group">
            <label><i class="fa-solid fa-envelope"></i> 家属告警邮箱</label>
            <input v-model="settings.email" type="email" placeholder="family@example.com" />
          </div>
          <div class="field-row">
            <div class="field-group">
              <label><i class="fa-solid fa-arrow-up"></i> 心率上限（bpm）</label>
              <input v-model.number="settings.hrMax" type="number" min="80" max="200" placeholder="130" />
            </div>
            <div class="field-group">
              <label><i class="fa-solid fa-arrow-down"></i> 心率下限（bpm）</label>
              <input v-model.number="settings.hrMin" type="number" min="20" max="80" placeholder="40" />
            </div>
          </div>
          <button class="btn-primary" @click="saveSettings">
            <i class="fa-solid fa-floppy-disk"></i> 保存设置
          </button>
          <p v-if="settingsSaved" class="save-ok">✓ 设置已保存</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'
import { useSosStore } from '@/stores/sos'
import { healthApi } from '@/api'

const authStore  = useAuthStore()
const familyStore = useFamilyStore()
const sosStore   = useSosStore()

const selectedId   = ref(authStore.userId)
const selectedName = ref(authStore.username)
const historyData  = ref([])
const latestData   = ref(null)
const careChartEl  = ref(null)
let careChart = null

const settings = ref({ email: '', hrMax: 130, hrMin: 40 })
const settingsSaved = ref(false)

function selectMember(id, name) {
  selectedId.value = id
  selectedName.value = name
  loadData()
}

function formatSteps(data) {
  if (!data?.steps) return '--'
  return data.steps.toLocaleString()
}

async function loadData() {
  try {
    const res = await healthApi.getHistory()
    historyData.value = res
    latestData.value = res[res.length - 1] || null
    renderCareChart(res)
  } catch (e) { console.error(e) }
}

function renderCareChart(data) {
  if (!careChart) return
  const labels = data.map((_, i) => `记录${i + 1}`)
  const hrs = data.map(d => d.heart_rate)
  careChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#1e2535', borderColor: '#2d3748', textStyle: { color: '#e2e8f0' } },
    grid: { left: 40, right: 20, top: 40, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: labels, axisLabel: { color: '#64748b' }, axisLine: { lineStyle: { color: '#2d3748' } } },
    yAxis: { type: 'value', name: 'bpm', min: 30, axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#1e2535' } } },
    series: [
      { type: 'line', data: hrs, smooth: true, symbol: 'circle', symbolSize: 7,
        lineStyle: { color: '#0d84ff', width: 2 }, itemStyle: { color: '#0d84ff' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(13,132,255,0.3)' }, { offset: 1, color: 'transparent' }] } },
        markLine: {
          silent: true,
          data: [
            { yAxis: 130, lineStyle: { color: '#ff4757', type: 'dashed', width: 2 }, label: { formatter: 'SOS上限 130bpm', color: '#ff4757' } },
            { yAxis: 40,  lineStyle: { color: '#ff4757', type: 'dashed', width: 2 }, label: { formatter: 'SOS下限 40bpm', color: '#ff4757' } }
          ]
        },
        markPoint: {
          data: hrs.map((v, i) => v > 130 || v < 40 ? { coord: [i, v], itemStyle: { color: '#ff4757' }, symbol: 'pin', symbolSize: 40, label: { formatter: '⚠SOS' } } : null).filter(Boolean)
        }
      }
    ]
  })
}

function saveSettings() {
  settingsSaved.value = true
  setTimeout(() => settingsSaved.value = false, 2000)
}

onMounted(async () => {
  await loadData()
  careChart = echarts.init(careChartEl.value)
  if (historyData.value.length) renderCareChart(historyData.value)
  window.addEventListener('resize', () => careChart?.resize())
})
onUnmounted(() => careChart?.dispose())
</script>

<style scoped>
.care-page { display: flex; flex-direction: column; gap: 20px; }

/* 成员选择条 */
.member-bar { display: flex; align-items: center; gap: 20px; padding: 16px 20px; }
.bar-label { font-size: 13px; color: var(--text-muted); flex-shrink: 0; }
.member-list { display: flex; gap: 12px; flex-wrap: wrap; }
.member-chip {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 14px;
  border: 1px solid var(--border-color);
  border-radius: 24px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-muted);
  transition: all 0.2s;
}
.member-chip:hover { border-color: var(--primary); color: var(--primary); }
.member-chip.selected { border-color: var(--primary); color: var(--primary); background: rgba(13,132,255,0.1); }
.chip-avatar { width: 24px; height: 24px; border-radius: 50%; }

/* 监控行 */
.monitor-row { display: grid; grid-template-columns: 220px 1fr; gap: 16px; }
.flex-grow { flex: 1; }
.echart-area { height: 260px; }

/* 成员档案 */
.member-profile { display: flex; flex-direction: column; align-items: center; padding: 20px; gap: 10px; }
.profile-avatar img { width: 80px; height: 80px; border-radius: 50%; border: 3px solid var(--primary); }
.profile-name { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.profile-items { width: 100%; display: flex; flex-direction: column; gap: 8px; }
.profile-item { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border-color); font-size: 13px; }
.pi-label { color: var(--text-muted); }
.pi-val { font-weight: 600; color: var(--text-primary); }
.pi-val.red { color: var(--danger); }
.risk-低风险 { color: var(--success); }
.risk-中风险 { color: var(--warning); }
.risk-高风险 { color: var(--danger); }

.sos-status {
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.sos-status.safe   { background: rgba(0,210,168,0.1);  color: var(--success); }
.sos-status.danger { background: rgba(255,71,87,0.1);  color: var(--danger); animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }

/* 底部行 */
.bottom-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

/* 告警表格 */
.alert-table { display: flex; flex-direction: column; gap: 4px; }
.alert-row-header {
  display: grid; grid-template-columns: 160px 1fr;
  padding: 8px 12px; background: var(--bg-deep); border-radius: 6px;
  font-size: 11px; color: var(--text-muted); font-weight: 600;
}
.alert-row-item {
  display: grid; grid-template-columns: 160px 1fr;
  padding: 10px 12px; border: 1px solid rgba(255,71,87,0.2); border-radius: 8px;
  background: rgba(255,71,87,0.04); font-size: 13px;
}
.alert-time { color: var(--text-muted); }
.alert-msg  { color: var(--danger); }

/* 设置表单 */
.settings-form { display: flex; flex-direction: column; gap: 14px; }
.field-group { display: flex; flex-direction: column; gap: 6px; }
.field-group label { font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; }
.field-group input {
  background: var(--bg-deep); border: 1px solid var(--border-color);
  border-radius: 8px; padding: 9px 12px; color: var(--text-primary);
  font-size: 14px; outline: none; transition: border-color 0.2s;
}
.field-group input:focus { border-color: var(--primary); }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.save-ok { color: var(--success); font-size: 13px; text-align: center; margin: 0; }

.empty-hint { display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--text-muted); padding: 30px; }
.empty-hint i { font-size: 28px; color: var(--success); opacity: 0.6; }
.empty-hint p { font-size: 13px; }
</style>

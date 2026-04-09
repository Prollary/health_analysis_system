<template>
  <div class="page diary-page">
    <div class="page-header">
      <h1 class="page-title"><i class="fa-solid fa-book-medical"></i> 健康日记 · 智能解析</h1>
    </div>

    <!-- 输入区 -->
    <div class="card input-card">
      <div class="card-header">
        <h2><i class="fa-solid fa-pen-to-square"></i> 用大白话告诉我今天的感受</h2>
      </div>
      <textarea
        v-model="diaryText"
        class="diary-textarea"
        placeholder="例如：今天早上起来头有点晕，胸口发闷，吃饭没什么胃口，下午休息了一会儿好一些了..."
        rows="5"
      ></textarea>
      <div class="input-footer">
        <span class="char-count">{{ diaryText.length }} 字</span>
        <button class="btn-primary" @click="submitDiary" :disabled="loading || !diaryText.trim()">
          <LoadingSpinner v-if="loading" height="20px" text="" />
          <span v-else><i class="fa-solid fa-wand-magic-sparkles"></i> AI 智能解析</span>
        </button>
      </div>
    </div>

    <!-- 解析结果（提交后显示） -->
    <Transition name="slide-up">
      <div v-if="parseResult" class="result-row">
        <!-- 症状标签 -->
        <div class="card symptoms-card">
          <div class="card-header">
            <h2><i class="fa-solid fa-tag"></i> 症状提取</h2>
          </div>
          <div v-if="symptoms.length" class="symptom-tags">
            <span v-for="s in symptoms" :key="s" class="symptom-tag">{{ s }}</span>
          </div>
          <p v-else class="no-symptom">未检测到明确症状</p>

          <div class="severity-bar">
            <span class="sb-label">关注程度</span>
            <div class="sb-track">
              <div class="sb-fill" :style="{ width: severityPct + '%', background: severityColor }"></div>
            </div>
            <span class="sb-value" :style="{ color: severityColor }">{{ severityText }}</span>
          </div>
        </div>

        <!-- AI 就医建议 -->
        <div class="card advice-card">
          <div class="card-header">
            <h2><i class="fa-solid fa-stethoscope"></i> AI 初步建议</h2>
          </div>
          <div class="advice-content" v-html="formattedAdvice"></div>
          <div class="advice-disclaimer">
            <i class="fa-solid fa-circle-info"></i>
            以上建议仅供参考，不构成医疗诊断。如症状持续或加重，请及时就医。
          </div>
        </div>
      </div>
    </Transition>

    <!-- 历史日记时间线 -->
    <div class="card timeline-card">
      <div class="card-header">
        <h2><i class="fa-solid fa-timeline"></i> 健康日记历史</h2>
      </div>
      <div v-if="diaryHistory.length" class="timeline">
        <div v-for="item in diaryHistory" :key="item.id" class="timeline-item">
          <div class="tl-dot"></div>
          <div class="tl-body">
            <div class="tl-header">
              <span class="tl-date">{{ formatDate(item.timestamp) }}</span>
              <div class="tl-tags">
                <span v-for="s in parseSymptoms(item.extracted_symptoms)" :key="s" class="symptom-tag sm">{{ s }}</span>
                <span v-if="!parseSymptoms(item.extracted_symptoms).length" class="tag-ok">状态良好</span>
              </div>
            </div>
            <p class="tl-content">{{ item.raw_content }}</p>
            <p v-if="item.ai_advice" class="tl-advice">💡 {{ item.ai_advice?.slice(0, 80) }}...</p>
          </div>
        </div>
      </div>
      <div v-else class="empty-hint">
        <i class="fa-solid fa-book-open"></i>
        <p>暂无日记记录，写下今天的第一篇健康日记吧</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { diaryApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const diaryText   = ref('')
const loading     = ref(false)
const parseResult = ref(null)
const diaryHistory = ref([])

const symptoms = computed(() => parseSymptoms(parseResult.value?.symptoms))

const severityPct = computed(() => symptoms.value.length > 3 ? 80 : symptoms.value.length > 1 ? 55 : symptoms.value.length > 0 ? 30 : 10)
const severityColor = computed(() => severityPct.value >= 70 ? '#ff4757' : severityPct.value >= 50 ? '#ffa726' : '#00d2a8')
const severityText  = computed(() => severityPct.value >= 70 ? '高度关注' : severityPct.value >= 50 ? '中度关注' : '轻度关注')

const formattedAdvice = computed(() =>
  (parseResult.value?.advice || '').replace(/\n/g, '<br>').replace(/(\d+\.)(\s)/g, '<br>$1$2')
)

function parseSymptoms(raw) {
  if (!raw) return []
  return raw.split(/[,，、;；\s]+/).map(s => s.trim()).filter(Boolean)
}

function formatDate(ts) {
  if (!ts) return ''
  return ts.slice(0, 16).replace('T', ' ')
}

async function submitDiary() {
  loading.value = true
  try {
    const res = await diaryApi.submit({ user_id: authStore.userId, content: diaryText.value })
    if (res.code === 200) {
      parseResult.value = res.data
      diaryHistory.value.unshift({
        id: Date.now(),
        timestamp: new Date().toISOString(),
        raw_content: diaryText.value,
        extracted_symptoms: res.data.symptoms,
        ai_advice: res.data.advice
      })
      diaryText.value = ''
    }
  } catch (e) {
    alert('解析失败，请检查网络')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 加载历史（此处使用本地缓存，实际可对接后端分页接口）
})
</script>

<style scoped>
.diary-page { display: flex; flex-direction: column; gap: 20px; }

/* 输入卡 */
.diary-textarea {
  width: 100%;
  background: var(--bg-deep);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.8;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
  box-sizing: border-box;
}
.diary-textarea:focus { border-color: var(--primary); }
.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}
.char-count { font-size: 12px; color: var(--text-muted); }

/* 结果行 */
.result-row { display: grid; grid-template-columns: 1fr 1.5fr; gap: 16px; }

/* 症状标签 */
.symptom-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.symptom-tag {
  padding: 5px 12px;
  background: rgba(255,71,87,0.12);
  border: 1px solid rgba(255,71,87,0.3);
  border-radius: 20px;
  font-size: 13px;
  color: var(--danger);
  font-weight: 600;
}
.symptom-tag.sm { padding: 3px 8px; font-size: 11px; }
.no-symptom { color: var(--text-muted); font-size: 13px; margin-bottom: 16px; }

/* 严重程度进度条 */
.severity-bar { display: flex; align-items: center; gap: 10px; }
.sb-label { font-size: 12px; color: var(--text-muted); white-space: nowrap; }
.sb-track { flex: 1; height: 6px; background: var(--bg-deep); border-radius: 3px; overflow: hidden; }
.sb-fill  { height: 100%; border-radius: 3px; transition: width 0.6s, background 0.3s; }
.sb-value { font-size: 12px; font-weight: 600; white-space: nowrap; }

/* AI 建议内容 */
.advice-content {
  font-size: 14px; color: var(--text-secondary); line-height: 1.8;
  max-height: 200px; overflow-y: auto; padding-right: 4px;
}
.advice-disclaimer {
  display: flex; align-items: center; gap: 8px;
  margin-top: 12px; padding: 10px 12px;
  background: rgba(255,167,38,0.08);
  border: 1px solid rgba(255,167,38,0.2);
  border-radius: 8px;
  font-size: 11px; color: var(--text-muted);
}
.advice-disclaimer i { color: var(--warning); flex-shrink: 0; }

/* 时间线 */
.timeline { display: flex; flex-direction: column; position: relative; padding-left: 24px; }
.timeline::before {
  content: '';
  position: absolute;
  left: 6px; top: 8px; bottom: 8px;
  width: 2px;
  background: var(--border-color);
}
.timeline-item { position: relative; margin-bottom: 20px; }
.tl-dot {
  position: absolute;
  left: -22px; top: 6px;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--primary);
  border: 2px solid var(--bg-card);
  box-shadow: 0 0 0 2px var(--primary);
}
.tl-body { padding-left: 4px; }
.tl-header { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
.tl-date { font-size: 12px; color: var(--text-muted); }
.tl-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag-ok {
  padding: 2px 8px;
  background: rgba(0,210,168,0.1);
  border: 1px solid var(--success);
  border-radius: 12px;
  font-size: 11px;
  color: var(--success);
}
.tl-content { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin: 0 0 4px; }
.tl-advice  { font-size: 12px; color: var(--primary); margin: 0; }

.empty-hint { display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--text-muted); padding: 32px; }
.empty-hint i { font-size: 32px; opacity: 0.3; }
.empty-hint p { font-size: 13px; }

.slide-up-enter-active, .slide-up-leave-active { transition: opacity 0.4s, transform 0.4s; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(16px); }
</style>

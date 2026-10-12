<template>
  <div class="kpi-card" :class="`accent-${accent}`">
    <div class="kpi-icon">
      <i :class="`fa-solid ${icon}`"></i>
    </div>
    <div class="kpi-body">
      <p class="kpi-label">{{ label }}</p>
      <p class="kpi-value">
        <span v-if="loading" class="loading-dots">···</span>
        <template v-else>
          {{ value }}<em v-if="unit">{{ unit }}</em>
        </template>
      </p>
      <p v-if="sub" class="kpi-sub" :class="subClass">{{ sub }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  icon:     { type: String, required: true },
  label:    { type: String, required: true },
  value:    { type: [String, Number], default: '--' },
  unit:     { type: String, default: '' },
  sub:      { type: String, default: '' },
  subClass: { type: String, default: '' },
  accent:   { type: String, default: 'blue' },  // blue | green | orange | red | purple
  loading:  { type: Boolean, default: false }
})
</script>

<style scoped>
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
}

.kpi-icon {
  width: 52px; height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

/* accent 颜色主题 */
.accent-blue .kpi-icon  { background: rgba(13,132,255,0.15); color: var(--primary); }
.accent-green .kpi-icon { background: rgba(0,210,168,0.15);  color: var(--success); }
.accent-orange .kpi-icon{ background: rgba(255,167,38,0.15); color: var(--warning); }
.accent-red .kpi-icon   { background: rgba(255,71,87,0.15);  color: var(--danger);  }
.accent-purple .kpi-icon{ background: rgba(156,39,176,0.15); color: #ab47bc;        }

.kpi-body { flex: 1; min-width: 0; }
.kpi-label { font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.kpi-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}
.kpi-value em { font-size: 13px; font-style: normal; color: var(--text-muted); margin-left: 3px; }
.kpi-sub { font-size: 11px; margin-top: 4px; color: var(--text-muted); }
.kpi-sub.ok    { color: var(--success); }
.kpi-sub.warn  { color: var(--warning); }
.kpi-sub.danger{ color: var(--danger);  }

.loading-dots { color: var(--text-muted); font-size: 20px; letter-spacing: 2px; }
</style>

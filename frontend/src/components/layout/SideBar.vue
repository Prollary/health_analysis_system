<template>
  <aside class="sidebar" :class="{ collapsed }">
    <!-- 折叠按钮 -->
    <button class="collapse-btn" @click="collapsed = !collapsed">
      <i :class="collapsed ? 'fa-solid fa-angles-right' : 'fa-solid fa-angles-left'"></i>
    </button>

    <nav class="sidebar-nav">
      <RouterLink
        v-for="item in navItems"
        :key="item.name"
        :to="item.path"
        class="nav-item"
        :title="collapsed ? item.label : ''"
      >
        <i :class="`fa-solid ${item.icon} nav-icon`"></i>
        <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
        <span v-if="!collapsed && item.badge" class="nav-badge">{{ item.badge }}</span>
      </RouterLink>
    </nav>

    <!-- 底部版本号 -->
    <div v-if="!collapsed" class="sidebar-footer">
      <span>v1.0 · 智慧健康系统</span>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

const collapsed = ref(false)

const navItems = [
  { name: 'Dashboard',   path: '/app/dashboard',   icon: 'fa-gauge-high',         label: '健康大屏总览' },
  { name: 'Environment', path: '/app/environment',  icon: 'fa-house-signal',       label: '环境联动分析' },
  { name: 'Care',        path: '/app/care',         icon: 'fa-heart-circle-check', label: '居家看护中心' },
  { name: 'Mirror',      path: '/app/mirror',       icon: 'fa-camera',             label: '智能镜子'    },
  { name: 'Diary',       path: '/app/diary',        icon: 'fa-book-medical',       label: '健康日记'    },
  { name: 'Report',      path: '/app/report',       icon: 'fa-file-waveform',      label: '健康报告中心' }
]
</script>

<style scoped>
.sidebar {
  width: 220px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
  flex-shrink: 0;
  position: relative;
}
.sidebar.collapsed { width: 64px; }

.collapse-btn {
  position: absolute;
  top: 20px;
  right: -14px;
  width: 28px; height: 28px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  z-index: 10;
  transition: color 0.2s, border-color 0.2s;
}
.collapse-btn:hover { color: var(--primary); border-color: var(--primary); }

.sidebar-nav {
  padding: 56px 8px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 14px;
  transition: background 0.2s, color 0.2s;
  white-space: nowrap;
  overflow: hidden;
}
.nav-item:hover { background: rgba(13, 132, 255, 0.08); color: var(--text-primary); }
.nav-item.router-link-active {
  background: rgba(13, 132, 255, 0.15);
  color: var(--primary);
  font-weight: 600;
}
.nav-icon { font-size: 16px; min-width: 20px; text-align: center; }
.nav-label { flex: 1; }
.nav-badge {
  background: var(--danger);
  color: white;
  font-size: 10px;
  border-radius: 10px;
  padding: 1px 6px;
}

.sidebar-footer {
  padding: 16px 12px;
  font-size: 11px;
  color: var(--text-muted);
  border-top: 1px solid var(--border-color);
  text-align: center;
}
</style>

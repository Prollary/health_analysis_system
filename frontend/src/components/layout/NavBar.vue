<template>
  <header class="navbar">
    <!-- 左：Logo -->
    <div class="navbar-left">
      <div class="logo">
        <i class="fa-solid fa-heart-pulse logo-icon"></i>
        <span class="logo-text">HealthAI <em>智慧舱</em></span>
      </div>
    </div>

    <!-- 中：SOS 告警指示器 -->
    <div class="navbar-center">
      <div class="sos-indicator" :class="{ active: sosStore.triggered }" @click="sosStore.triggered && sosStore.dismissSos()">
        <span class="sos-dot"></span>
        <span class="sos-label">{{ sosStore.triggered ? '⚠ 紧急告警 — 点击确认' : '系统正常' }}</span>
      </div>
    </div>

    <!-- 右：家庭切换 + 用户信息 -->
    <div class="navbar-right">
      <!-- 管理员才显示成员切换 -->
      <div v-if="authStore.isAdmin" class="member-switcher" @click="toggleDropdown">
        <i class="fa-solid fa-users-between-lines"></i>
        <span>{{ familyStore.currentMemberName || '自己' }}</span>
        <i class="fa-solid fa-chevron-down"></i>
        <!-- 下拉菜单 -->
        <div v-if="showDropdown" class="dropdown-menu" @click.stop>
          <div class="dropdown-item" @click="selectSelf">
            <i class="fa-solid fa-user-check"></i> 查看自己
          </div>
          <div
            v-for="m in familyStore.members"
            :key="m.id"
            class="dropdown-item"
            :class="{ selected: familyStore.currentMemberId === m.id }"
            @click="selectMember(m)"
          >
            <i class="fa-solid fa-person-cane"></i> {{ m.name }}
          </div>
        </div>
      </div>

      <div class="user-info">
        <img :src="`https://api.dicebear.com/7.x/notionists/svg?seed=${authStore.username}`" class="avatar" alt="avatar" />
        <div class="user-detail">
          <span class="user-name">{{ authStore.username }}</span>
          <span class="user-role">{{ authStore.role === 'admin' ? '管理员' : '成员' }}</span>
        </div>
        <button class="logout-btn" @click="handleLogout" title="退出登录">
          <i class="fa-solid fa-right-from-bracket"></i>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'
import { useSosStore } from '@/stores/sos'

const authStore = useAuthStore()
const familyStore = useFamilyStore()
const sosStore = useSosStore()
const router = useRouter()
const showDropdown = ref(false)

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

function selectSelf() {
  familyStore.resetToSelf()
  showDropdown.value = false
}

function selectMember(m) {
  familyStore.switchMember(m.id, m.name)
  showDropdown.value = false
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  height: 64px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 16px;
  flex-shrink: 0;
  position: relative;
  z-index: 100;
}

.navbar-left { flex: 1; }
.navbar-center { flex: 1; display: flex; justify-content: center; }
.navbar-right { flex: 1; display: flex; align-items: center; justify-content: flex-end; gap: 16px; }

/* Logo */
.logo { display: flex; align-items: center; gap: 10px; cursor: default; }
.logo-icon { font-size: 24px; color: var(--primary); animation: pulse 2s infinite; }
.logo-text { font-size: 18px; font-weight: 700; color: var(--text-primary); letter-spacing: 1px; }
.logo-text em { color: var(--primary); font-style: normal; }

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

/* SOS 指示器 */
.sos-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-radius: 20px;
  background: rgba(0, 210, 168, 0.1);
  border: 1px solid var(--success);
  cursor: default;
  transition: all 0.3s;
}
.sos-indicator.active {
  background: rgba(255, 71, 87, 0.15);
  border-color: var(--danger);
  cursor: pointer;
  animation: sos-flash 0.8s infinite;
}
@keyframes sos-flash {
  0%, 100% { box-shadow: 0 0 8px rgba(255, 71, 87, 0.5); }
  50% { box-shadow: 0 0 20px rgba(255, 71, 87, 0.9); }
}
.sos-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--success);
  .sos-indicator.active & { background: var(--danger); animation: dot-blink 0.5s infinite; }
}
.sos-indicator.active .sos-dot { background: var(--danger); animation: dot-blink 0.5s infinite; }
@keyframes dot-blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.sos-label { font-size: 13px; color: var(--text-secondary); }
.sos-indicator.active .sos-label { color: var(--danger); font-weight: 600; }

/* 成员切换 */
.member-switcher {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  background: var(--bg-deep);
  border: 1px solid var(--border-color);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  position: relative;
  user-select: none;
}
.member-switcher:hover { border-color: var(--primary); color: var(--primary); }

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 180px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  overflow: hidden;
  z-index: 200;
}
.dropdown-item {
  padding: 10px 16px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}
.dropdown-item:hover { background: rgba(13, 132, 255, 0.1); color: var(--primary); }
.dropdown-item.selected { color: var(--primary); background: rgba(13, 132, 255, 0.08); }

/* 用户信息 */
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  border: 2px solid var(--primary);
}
.user-detail { display: flex; flex-direction: column; }
.user-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.user-role { font-size: 11px; color: var(--text-muted); }
.logout-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  font-size: 14px;
  transition: color 0.2s;
}
.logout-btn:hover { color: var(--danger); }
</style>

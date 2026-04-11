<template>
  <div class="app-shell">
    <NavBar />
    <div class="shell-body">
      <SideBar />
      <main class="main-content">
        <RouterView />
      </main>
    </div>
    <!-- 全局 SOS 告警弹窗 -->
    <SosAlert />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import NavBar from './NavBar.vue'
import SideBar from './SideBar.vue'
import SosAlert from '@/components/common/SosAlert.vue'
import { useFamilyStore } from '@/stores/family'
import { useAuthStore } from '@/stores/auth'
import { familyApi } from '@/api'

const familyStore = useFamilyStore()
const authStore = useAuthStore()

// 如果是管理员，进入应用时预加载家庭成员列表
onMounted(async () => {
  if (authStore.isAdmin) {
    try {
      const res = await familyApi.getGroup()
      if (res.code === 200 && res.data && res.data.members) {
        // 过滤掉自己，只保留真正的被监护家庭成员，并映射为 Navbar 需要的 id 和 name
        const mappedMembers = res.data.members
          .filter(m => !m.is_self)
          .map(m => ({ id: m.user_id, name: m.username }))
        familyStore.setMembers(mappedMembers)
      }
    } catch (e) {
      // 非关键流程，静默失败
      console.warn('获取家庭群组失败', e)
    }
  }
})
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-deep);
}
.shell-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>

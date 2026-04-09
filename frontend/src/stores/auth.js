import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 从 localStorage 恢复登录状态（页面刷新后保持登录）
  const token = ref(localStorage.getItem('health_token') || '')
  const userId = ref(Number(localStorage.getItem('health_user_id')) || null)
  const username = ref(localStorage.getItem('health_username') || '')
  const role = ref(localStorage.getItem('health_role') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')

  function login(data) {
    token.value = data.access_token
    userId.value = data.user_id
    username.value = data.username
    role.value = data.role
    localStorage.setItem('health_token', data.access_token)
    localStorage.setItem('health_user_id', data.user_id)
    localStorage.setItem('health_username', data.username)
    localStorage.setItem('health_role', data.role)
  }

  function logout() {
    token.value = ''
    userId.value = null
    username.value = ''
    role.value = ''
    localStorage.removeItem('health_token')
    localStorage.removeItem('health_user_id')
    localStorage.removeItem('health_username')
    localStorage.removeItem('health_role')
  }

  return { token, userId, username, role, isLoggedIn, isAdmin, login, logout }
})

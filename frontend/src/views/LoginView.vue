<template>
  <div class="login-page">
    <!-- 背景粒子装饰 -->
    <div class="bg-circles">
      <div v-for="i in 6" :key="i" class="circle" :style="circleStyle(i)"></div>
    </div>

    <div class="login-card">
      <!-- Logo -->
      <div class="login-logo">
        <i class="fa-solid fa-heart-pulse"></i>
        <h1>HealthAI <span>智慧舱</span></h1>
        <p>智慧家居 · 健康守护平台</p>
      </div>

      <!-- Tab 切换 -->
      <div class="tab-bar">
        <button :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <!-- 登录表单 -->
      <form v-if="mode === 'login'" class="auth-form" @submit.prevent="handleLogin">
        <div class="field">
          <i class="fa-solid fa-user field-icon"></i>
          <input v-model="form.username" type="text" placeholder="用户名" required autocomplete="username" />
        </div>
        <div class="field">
          <i class="fa-solid fa-lock field-icon"></i>
          <input v-model="form.password" type="password" placeholder="密码" required autocomplete="current-password" />
        </div>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        <button type="submit" class="submit-btn" :disabled="loading">
          <LoadingSpinner v-if="loading" height="20px" text="" />
          <span v-else><i class="fa-solid fa-right-to-bracket"></i> 立即登录</span>
        </button>
      </form>

      <!-- 注册表单 -->
      <form v-else class="auth-form" @submit.prevent="handleRegister">
        <div class="field">
          <i class="fa-solid fa-user field-icon"></i>
          <input v-model="form.username" type="text" placeholder="设置用户名" required />
        </div>
        <div class="field">
          <i class="fa-solid fa-lock field-icon"></i>
          <input v-model="form.password" type="password" placeholder="设置密码" required />
        </div>
        <div class="role-group">
          <label>账户角色</label>
          <div class="role-options">
            <label class="role-opt" :class="{ active: form.role === 'admin' }">
              <input v-model="form.role" type="radio" value="admin" hidden />
              <i class="fa-solid fa-user-shield"></i> 管理员（子女）
            </label>
            <label class="role-opt" :class="{ active: form.role === 'member' }">
              <input v-model="form.role" type="radio" value="member" hidden />
              <i class="fa-solid fa-person-cane"></i> 成员（老人）
            </label>
          </div>
        </div>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        <p v-if="successMsg" class="success-msg">{{ successMsg }}</p>
        <button type="submit" class="submit-btn" :disabled="loading">
          <LoadingSpinner v-if="loading" height="20px" text="" />
          <span v-else><i class="fa-solid fa-user-plus"></i> 注册账户</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const mode = ref('login')
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const form = reactive({ username: '', password: '', role: 'member' })

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    const res = await authApi.login({ username: form.username, password: form.password })
    if (res.code === 200) {
      authStore.login(res.data)
      router.push('/app/dashboard')
    } else {
      errorMsg.value = res.msg || '登录失败'
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.msg || '服务器连接失败'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  errorMsg.value = ''
  successMsg.value = ''
  loading.value = true
  try {
    const res = await authApi.register({ username: form.username, password: form.password, role: form.role })
    if (res.code === 200) {
      successMsg.value = '注册成功！请登录'
      mode.value = 'login'
    } else {
      errorMsg.value = res.msg || '注册失败'
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.msg || '服务器连接失败'
  } finally {
    loading.value = false
  }
}

function circleStyle(i) {
  const sizes = [300, 200, 150, 400, 250, 180]
  const positions = [
    { top: '-80px', left: '-80px' },
    { top: '20%', right: '-60px' },
    { bottom: '10%', left: '5%' },
    { bottom: '-100px', right: '-100px' },
    { top: '50%', left: '10%' },
    { top: '15%', left: '40%' }
  ]
  const size = sizes[i - 1]
  return {
    width: size + 'px',
    height: size + 'px',
    ...positions[i - 1],
    animationDelay: (i * 0.7) + 's'
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--bg-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

/* 背景装饰圆 */
.bg-circles { position: absolute; inset: 0; pointer-events: none; }
.circle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(13,132,255,0.08), transparent 70%);
  animation: float 8s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50%       { transform: translateY(-20px) scale(1.05); }
}

/* 卡片 */
.login-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 40px 48px;
  width: 420px;
  position: relative;
  z-index: 1;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}

/* Logo 区 */
.login-logo {
  text-align: center;
  margin-bottom: 28px;
}
.login-logo i {
  font-size: 42px;
  color: var(--primary);
  animation: pulse 2s infinite;
}
.login-logo h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 8px 0 4px;
}
.login-logo h1 span { color: var(--primary); }
.login-logo p { font-size: 13px; color: var(--text-muted); }

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

/* Tab */
.tab-bar {
  display: flex;
  background: var(--bg-deep);
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 24px;
}
.tab-bar button {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 8px;
  background: none;
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.tab-bar button.active {
  background: var(--primary);
  color: white;
  font-weight: 600;
}

/* 表单 */
.auth-form { display: flex; flex-direction: column; gap: 14px; }
.field {
  display: flex;
  align-items: center;
  background: var(--bg-deep);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 0 14px;
  transition: border-color 0.2s;
}
.field:focus-within { border-color: var(--primary); }
.field-icon { color: var(--text-muted); font-size: 14px; width: 20px; }
.field input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  padding: 12px 10px;
  color: var(--text-primary);
  font-size: 14px;
}

/* 角色选择 */
.role-group label:first-child { font-size: 13px; color: var(--text-muted); }
.role-options { display: flex; gap: 10px; margin-top: 8px; }
.role-opt {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  text-align: center;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-muted);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.role-opt.active { border-color: var(--primary); color: var(--primary); background: rgba(13,132,255,0.08); }

.error-msg   { color: var(--danger);  font-size: 13px; text-align: center; }
.success-msg { color: var(--success); font-size: 13px; text-align: center; }

.submit-btn {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 10px;
  padding: 13px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
  transition: opacity 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.submit-btn:hover:not(:disabled) { opacity: 0.88; }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>

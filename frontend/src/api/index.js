import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器：自动附加 JWT Token
http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// 响应拦截器：Token 失效时自动登出
http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (err.response?.status === 401) {
      const auth = useAuthStore()
      auth.logout()
      router.push('/login')
    }
    return Promise.reject(err)
  }
)

// ==================== 认证模块 ====================
export const authApi = {
  login: (data) => http.post('/auth/login', data),
  register: (data) => http.post('/auth/register', data)
}

// ==================== 健康数据模块 ====================
export const healthApi = {
  // 获取历史体征数据（JWT保护，自动从Token读取user_id）
  getHistory: () => http.get('/health/history'),

  // 触发AI分析
  analyze: (userId) => http.post(`/analyze/${userId}`),

  // 生成完整干预方案
  generateReport: (userId) => http.get(`/health/report/generate/${userId}`),

  // 下载PDF报告（直接链接）
  getPdfUrl: (userId) => `/api/health/report/download/${userId}`
}

// ==================== 传感器上传模块 ====================
export const sensorApi = {
  upload: (data) => http.post('/sensor/upload', data)
}

// ==================== 家庭成员模块 ====================
export const familyApi = {
  getMembers: () => http.get('/family/members'),
  monitorMember: (memberId) => http.get(`/family/monitor/${memberId}`)
}

// ==================== 健康日记模块 ====================
export const diaryApi = {
  submit: (data) => http.post('/diary/submit', data)
}

// ==================== 智能镜子模块 ====================
export const mirrorApi = {
  analyze: (data) => http.post('/vision/smart_mirror', data)
}

export default http

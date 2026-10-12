import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/app',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/app/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '健康大屏总览', icon: 'fa-gauge-high' }
      },
      {
        path: 'environment',
        name: 'Environment',
        component: () => import('@/views/EnvironmentView.vue'),
        meta: { title: '环境联动分析', icon: 'fa-house-signal' }
      },
      {
        path: 'care',
        name: 'Care',
        component: () => import('@/views/CareView.vue'),
        meta: { title: '居家看护中心', icon: 'fa-heart-circle-check' }
      },
      {
        path: 'mirror',
        name: 'Mirror',
        component: () => import('@/views/MirrorView.vue'),
        meta: { title: '智能镜子', icon: 'fa-camera' }
      },
      {
        path: 'diary',
        name: 'Diary',
        component: () => import('@/views/DiaryView.vue'),
        meta: { title: '健康日记', icon: 'fa-book-medical' }
      },
      {
        path: 'report',
        name: 'Report',
        component: () => import('@/views/ReportView.vue'),
        meta: { title: '健康报告中心', icon: 'fa-file-waveform' }
      }
    ]
  },
  {
    path: '/',
    redirect: '/app/dashboard'
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/app/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：未登录跳转到登录页
router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth !== false && !authStore.isLoggedIn) {
    return { name: 'Login' }
  }
  if (to.name === 'Login' && authStore.isLoggedIn) {
    return { name: 'Dashboard' }
  }
})

export default router

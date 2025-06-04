import { createRouter, createWebHistory } from 'vue-router'
import IndexView from '../views/IndexView.vue'
import LoginView from '../views/LoginView.vue'
import ServerManageView from '../views/ServerManageView.vue'
import DashboardView from '../views/DashboardView.vue'
import EmailManageView from '../views/EmailManageView.vue'
import UserManageView from '../views/UserManageView.vue'
import ApiKeyManageView from '../views/ApiKeyManageView.vue'
import EvalLogsView from '../views/EvalLogsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: IndexView,
      redirect: '/dashboard',
      children: [
        {
          path: '/dashboard',
          name: 'dashboard',
          component: DashboardView,
          meta: { requiresAuth: true }
        },
        {
          path: '/servers',
          name: 'servers',
          component: ServerManageView,
          meta: { requiresAuth: true }
        },
        {
          path: '/emails',
          name: 'emails',
          component: EmailManageView,
          meta: { requiresAuth: true }
        },
        {
          path: '/users',
          name: 'users',
          component: UserManageView,
          meta: { requiresAuth: true }
        },
        {
          path: '/api-keys',
          name: 'api-keys',
          component: ApiKeyManageView,
          meta: { requiresAuth: true }
        },
        {
          path: '/eval-logs',
          name: 'eval-logs',
          component: EvalLogsView,
          meta: { requiresAuth: true }
        },
      ],
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
  ],
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('accessToken')
  
  // 检查路由是否需要认证
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 需要认证但没有token
    if (!token) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    } else {
      next()
    }
  } else {
    // 不需要认证的路由
    if (token && to.path === '/login') {
      // 已登录用户访问登录页，重定向到首页
      next({ path: '/dashboard' })
    } else {
      next()
    }
  }
})

export default router

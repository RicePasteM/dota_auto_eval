<template>
  <div class="dashboard">
    <header class="header">
      <div class="header-left">
        <h1>DOTA Auto Eval 管理系统</h1>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>
            {{ getBreadcrumbTitle(currentRoute.name) }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <button @click="handleLogout" class="logout-btn">退出登录</button>
    </header>
    
    <nav class="sidebar">
      <ul>
        <li>
          <router-link to="/dashboard" active-class="active">仪表盘</router-link>
        </li>
        <li>
          <router-link to="/servers" active-class="active">服务器管理</router-link>
        </li>
        <li>
          <router-link to="/emails" active-class="active">邮箱管理</router-link>
        </li>
        <li>
          <router-link to="/users" active-class="active">用户管理</router-link>
        </li>
        <li>
          <router-link to="/api-keys" active-class="active">API Key管理</router-link>
        </li>
        <li>
          <router-link to="/eval-logs" active-class="active">评估日志</router-link>
        </li>
      </ul>
    </nav>

    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const currentRoute = computed(() => route)

// 面包屑标题映射
const routeTitles = {
  dashboard: '仪表盘',
  servers: '服务器管理',
  emails: '邮箱管理',
  users: '用户管理',
  'api-keys': 'API Key管理',
  'eval-logs': '评估日志'
}

const getBreadcrumbTitle = (routeName) => {
  return routeTitles[routeName] || routeName
}

const handleLogout = () => {
  localStorage.removeItem('accessToken')
  router.push('/login')
}
</script>

<style scoped>
.dashboard {
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar main";
  grid-template-columns: 200px 1fr;
  grid-template-rows: 60px 1fr;
  height: 100vh;
}

.header {
  grid-area: header;
  background-color: #1890ff;
  color: white;
  padding: 0 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.header h1 {
  font-size: 1.2rem;
  margin: 0;
  white-space: nowrap;
}

:deep(.el-breadcrumb) {
  --el-text-color-regular: rgba(255, 255, 255, 0.85);
  --el-text-color-primary: white;
}

:deep(.el-breadcrumb__separator) {
  color: rgba(255, 255, 255, 0.85);
}

:deep(.el-breadcrumb__inner a) {
  color: rgba(255, 255, 255, 0.85) !important;
  font-weight: normal;
}

:deep(.el-breadcrumb__inner a:hover) {
  color: white !important;
}

:deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: white;
  font-weight: 600;
}

.logout-btn {
  background: none;
  border: 1px solid white;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.sidebar {
  grid-area: sidebar;
  background-color: #001529;
  padding: 1rem 0;
}

.sidebar ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar a {
  display: block;
  padding: 0.75rem 1rem;
  color: #fff;
  text-decoration: none;
  transition: background-color 0.3s;
}

.sidebar a:hover,
.sidebar a.active {
  background-color: #1890ff;
}

.main-content {
  grid-area: main;
  padding: 1.5rem;
  background-color: #f0f2f5;
  overflow-y: auto;
}
</style> 
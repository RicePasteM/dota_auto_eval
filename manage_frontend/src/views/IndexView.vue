<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="menu-container">
      <div class="logo-container">
        <h2>DOTA 管理系统</h2>
      </div>
      <el-menu
        router
        :default-active="activeIndex"
        class="el-menu-vertical"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        
        <el-menu-item index="/servers">
          <el-icon><Connection /></el-icon>
          <span>评估服务器管理</span>
        </el-menu-item>
        
        <el-menu-item index="/emails">
          <el-icon><Message /></el-icon>
          <span>邮箱管理</span>
        </el-menu-item>
        
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        
        <el-menu-item index="/eval-logs">
          <el-icon><Document /></el-icon>
          <span>评估日志</span>
        </el-menu-item>
        
        <el-menu-item index="/training">
          <el-icon><List /></el-icon>
          <span>训练任务管理</span>
        </el-menu-item>
        
        <el-menu-item index="/api-keys">
          <el-icon><Key /></el-icon>
          <span>API密钥</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container class="content-container">
      <el-header class="header-container">
        <div class="header-left">
          <el-icon class="toggle-icon" @click="toggleCollapse"><Expand /></el-icon>
        </div>
        <div class="header-right">
          <el-dropdown>
            <span class="el-dropdown-link">
              管理员
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-container">
        <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()

const activeIndex = computed(() => route.path)
const isCollapse = ref(false)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    localStorage.removeItem('accessToken')
    router.push('/login')
  }).catch(() => {})
}
</script>

<style scoped>
.layout-container {
  height: 100%;
}

.menu-container {
  background-color: #304156;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  overflow-y: auto;
}

.logo-container {
  height: 60px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #2b3649;
}

.logo-container h2 {
  color: #fff;
  font-size: 18px;
  margin: 0;
}

.el-menu-vertical {
  border-right: none;
}

.content-container {
  margin-left: 220px;
}

.header-container {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
}

.toggle-icon {
  font-size: 20px;
  cursor: pointer;
  margin-right: 15px;
}

.header-right {
  display: flex;
  align-items: center;
}

.el-dropdown-link {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: #606266;
}

.main-container {
  padding: 0;
  height: calc(100vh - 60px);
  overflow-y: auto;
  background-color: #f0f2f5;
}
</style> 
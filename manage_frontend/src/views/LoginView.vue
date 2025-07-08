<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-content">
        <div class="login-header">
          <h1>DOTA Auto Eval</h1>
          <p class="subtitle">请登录以继续</p>
        </div>
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-group">
            <label for="username">用户名</label>
            <input 
              type="text" 
              id="username" 
              v-model="form.username" 
              required 
              placeholder="请输入用户名"
              :disabled="loading"
            />
          </div>
          <div class="form-group">
            <label for="password">密码</label>
            <input 
              type="password" 
              id="password" 
              v-model="form.password" 
              required 
              placeholder="请输入密码"
              :disabled="loading"
            />
          </div>
          <button 
            type="submit" 
            class="login-btn" 
            :disabled="loading"
          >
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import axios from 'axios';

const router = useRouter();
const route = useRoute();

const loading = ref(false);
const form = reactive({
  username: '',
  password: ''
});

const handleLogin = async () => {
  if (!form.username || !form.password) {
    return ElMessage.error('请输入用户名和密码')
  }
  
  try {
    loading.value = true
    const response = await axios.post('/api/login', {
      username: form.username,
      password: form.password
    })
    
    const token = response.data.access_token
    localStorage.setItem('accessToken', token)
    
    // 重定向到之前尝试访问的页面，或者默认到首页
    const redirectPath = route.query.redirect || '/dashboard'
    router.push(redirectPath)
    
  } catch (error) {
    console.error('登录失败:', error)
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}

.login-box {
  width: 400px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.login-content {
  padding: 30px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  margin: 0;
  font-size: 24px;
  color: #409eff;
}

.subtitle {
  margin-top: 10px;
  color: #909399;
}

.login-form {
  margin-top: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #606266;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: #409eff;
}

.login-btn {
  width: 100%;
  padding: 12px;
  background-color: #409eff;
  border: none;
  border-radius: 4px;
  color: white;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.login-btn:hover {
  background-color: #66b1ff;
}

.login-btn:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.error-message {
  color: #f56c6c;
  font-size: 14px;
  margin-top: 10px;
  text-align: center;
}

.success-message {
  color: #67c23a;
  font-size: 14px;
  margin-top: 10px;
  text-align: center;
}
</style>
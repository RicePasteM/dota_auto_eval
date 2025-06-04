<template>
  <div class="login-container">
    <div class="login-page">
      <div class="login-header">
        <h1>DOTA AUTO EVAL</h1>
        <p class="subtitle">请登录以继续</p>
      </div>
      <form @submit.prevent="login" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-wrapper">
            <input 
              type="text" 
              id="username" 
              v-model="username" 
              required
              :disabled="loading"
              placeholder="请输入用户名"
            >
          </div>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <div class="input-wrapper">
            <input 
              type="password" 
              id="password" 
              v-model="password" 
              required
              :disabled="loading"
              placeholder="请输入密码"
            >
          </div>
        </div>
        <button type="submit" :disabled="loading" class="login-button">
          <span class="button-content">
            <span v-if="!loading">登录</span>
            <span v-else class="loading-spinner"></span>
          </span>
        </button>
      </form>
      <transition name="fade">
        <p v-if="errorMessage" class="error-message">
          <el-icon size="20">
            <Close />
          </el-icon>
          {{ errorMessage }}
        </p>
      </transition>
      <transition name="fade">
        <p v-if="successMessage" class="success-message">
          <el-icon size="20">
            <Check />
          </el-icon>
          {{ successMessage }}
        </p>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const router = useRouter();
const login = async () => {
  loading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    const response = await fetch(`${window.BASE_URL}/api/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw { 
        response: {
          status: response.status,
          data: data
        }
      };
    }

    if (data && data.access_token) {
      localStorage.setItem('accessToken', data.access_token);
      successMessage.value = '登录成功！正在跳转...';
      router.push('/dashboard');
    } else {
      errorMessage.value = '登录失败，请重试。';
    }

  } catch (error) {
    if (error.response) {
      if (error.response.data && error.response.data.msg) {
        errorMessage.value = `登录失败: ${error.response.data.msg}`;
      } else if (error.response.status === 401) {
        errorMessage.value = '登录失败: 用户名或密码错误。';
      } else {
        errorMessage.value = `登录失败: 服务器错误 (${error.response.status})。`;
      }
    } else {
      errorMessage.value = '登录失败: 无法连接到服务器，请检查网络或后端服务是否运行。';
    }
    console.error('Login error:', error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

.login-page {
  width: 100%;
  max-width: 400px;
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.login-page:hover {
  transform: translateY(-2px);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-header h1 {
  color: #2c3e50;
  font-size: 1.8rem;
  margin: 0;
  font-weight: 600;
}

.subtitle {
  color: #7f8c8d;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #34495e;
  font-size: 0.9rem;
  font-weight: 500;
}

.input-wrapper {
  position: relative;
}

input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: #f8f9fa;
  color: #2c3e50;
  box-sizing: border-box;
}

input:focus {
  border-color: #3498db;
  background: white;
  outline: none;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

input:disabled {
  background: #f5f6f7;
  cursor: not-allowed;
}

.login-button {
  width: 100%;
  padding: 0.75rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.login-button:hover:not(:disabled) {
  background: #2980b9;
  transform: translateY(-1px);
}

.login-button:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 24px;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message,
.success-message {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.error-message {
  background: #fee2e2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.success-message {
  background: #dcfce7;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.error-icon,
.success-icon {
  font-size: 1.1rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 480px) {
  .login-page {
    padding: 1.5rem;
  }

  .login-header h1 {
    font-size: 1.5rem;
  }
}
</style>
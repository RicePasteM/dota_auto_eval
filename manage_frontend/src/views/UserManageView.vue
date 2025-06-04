<template>
  <div class="user-manage">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="success" @click="showAutoSignupDialog" style="margin-left: 10px;">
        <el-icon><Plus /></el-icon>自动批量注册用户
      </el-button>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-container">
      <el-form :inline="true">
        <el-form-item label="所属服务器">
          <el-select v-model="filterForm.server_id" placeholder="选择服务器" clearable @change="handleFilter" style="width: 200px;">
            <el-option v-for="server in servers" :key="server.server_id" :label="server.server_name" :value="server.server_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="用户名/邮箱"
            clearable
            @keyup.enter="handleFilter"
            @clear="handleFilter"
            style="width: 300px;"
          >
            <template #append>
              <el-button :icon="Search" @click="handleFilter" />
            </template>
          </el-input>
        </el-form-item>
      </el-form>
    </div>

    <!-- 用户列表表格 -->
    <el-table
      v-loading="loading"
      :data="users"
      style="width: 100%"
      border
    >
      <el-table-column prop="user_id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="password" label="密码" />
      <el-table-column prop="server_name" label="所属服务器" />
      <el-table-column prop="email" label="关联邮箱" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
          <el-button-group>
            <el-button
              size="small"
              type="primary"
              @click="handleEdit(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(scope.row)"
            >
              删除
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 自动批量注册用户Dialog -->
    <el-dialog
      v-model="autoSignupDialogVisible"
      title="自动批量注册用户"
      width="1200px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <el-form label-width="100px">
        <el-form-item label="服务器">
          <el-select v-model="selectedServerId" placeholder="请选择服务器" @change="fetchUnregisteredEmails">
            <el-option v-for="server in servers" :key="server.server_id" :label="server.server_name" :value="server.server_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-select v-model="selectedEmailIds" multiple placeholder="请选择邮箱" :disabled="!selectedServerId">
            <el-option v-for="email in unregisteredEmails" :key="email.email_id" :label="email.email" :value="email.email_id" />
          </el-select>
          <div style="margin-top: 8px;">
            <el-button size="small" @click="toggleSelectAllEmails" :disabled="unregisteredEmails.length === 0">
              {{ isAllEmailsSelected ? '取消全部' : '全部选择' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <el-input type="textarea" :rows="10" v-model="signupLog" readonly style="margin-top: 10px;" />
      <template #footer>
        <el-button @click="autoSignupDialogVisible=false" :disabled="signupLoading && !signupComplete">取消</el-button>
        <el-button type="primary" @click="startAutoSignup" :loading="signupLoading" :disabled="!selectedServerId || selectedEmailIds.length===0 || signupLoading">开始注册</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'

const loading = ref(false)
const submitting = ref(false)
const users = ref([])
const servers = ref([])
const emails = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const dialogType = ref('add')
const userFormRef = ref(null)
const autoSignupDialogVisible = ref(false)
const selectedServerId = ref(null)
const unregisteredEmails = ref([])
const selectedEmailIds = ref([])
const signupLog = ref('')
const signupLoading = ref(false)
const signupComplete = ref(false)

const userForm = ref({
  username: '',
  password: '',
  server_id: '',
  email_id: ''
})

const filterForm = ref({
  server_id: null,
  search: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  server_id: [
    { required: true, message: '请选择服务器', trigger: 'change' }
  ],
  email_id: [
    { required: true, message: '请选择邮箱', trigger: 'change' }
  ]
}

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('accessToken')
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      per_page: pageSize.value.toString()
    })
    
    // 添加筛选参数
    if (filterForm.value.server_id) {
      params.append('server_id', filterForm.value.server_id)
    }
    if (filterForm.value.search) {
      params.append('search', filterForm.value.search)
    }
    
    const response = await fetch(
      `${window.BASE_URL}/api/server_users?${params.toString()}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取用户列表失败')
    
    users.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

// 获取服务器列表
const fetchServers = async () => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(
      `${window.BASE_URL}/api/servers?page=1&per_page=100`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取服务器列表失败')
    
    servers.value = data.items
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 获取邮箱列表
const fetchEmails = async () => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(
      `${window.BASE_URL}/api/emails?page=1&per_page=100`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取邮箱列表失败')
    
    emails.value = data.items
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 显示添加对话框
const showAddDialog = () => {
  dialogType.value = 'add'
  userForm.value = {
    username: '',
    password: '',
    server_id: '',
    email_id: ''
  }
  dialogVisible.value = true
}

// 显示编辑对话框
const handleEdit = (row) => {
  dialogType.value = 'edit'
  userForm.value = {
    ...row,
    password: '' // 编辑时不显示原密码
  }
  dialogVisible.value = true
}

// 处理删除
const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除用户 "${row.username}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const token = localStorage.getItem('accessToken')
      const response = await fetch(`${window.BASE_URL}/api/server_users/${row.user_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.msg || '删除失败')
      
      ElMessage.success('删除成功')
      fetchUsers()
    } catch (error) {
      ElMessage.error(error.message)
    }
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!userFormRef.value) return
  
  await userFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const token = localStorage.getItem('accessToken')
        const url = dialogType.value === 'add' 
          ? `${window.BASE_URL}/api/server_users`
          : `${window.BASE_URL}/api/server_users/${userForm.value.user_id}`
        
        const response = await fetch(url, {
          method: dialogType.value === 'add' ? 'POST' : 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(userForm.value)
        })
        
        const data = await response.json()
        if (!response.ok) throw new Error(data.msg || '操作失败')
        
        ElMessage.success(dialogType.value === 'add' ? '添加成功' : '更新成功')
        dialogVisible.value = false
        fetchUsers()
      } catch (error) {
        ElMessage.error(error.message)
      } finally {
        submitting.value = false
      }
    }
  })
}

// 处理分页
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchUsers()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchUsers()
}

const showAutoSignupDialog = () => {
  autoSignupDialogVisible.value = true
  selectedServerId.value = null
  unregisteredEmails.value = []
  selectedEmailIds.value = []
  signupLog.value = ''
  signupComplete.value = false
}

const fetchUnregisteredEmails = async () => {
  if (!selectedServerId.value) return
  unregisteredEmails.value = []
  selectedEmailIds.value = []
  signupLog.value = '正在获取未注册邮箱...\n'
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(`${window.BASE_URL}/api/server_users/unregistered_emails?server_id=${selectedServerId.value}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取未注册邮箱失败')
    unregisteredEmails.value = data
    signupLog.value += `共获取到${data.length}个未注册邮箱。\n`
  } catch (error) {
    signupLog.value += `获取未注册邮箱失败: ${error.message}\n`
    ElMessage.error(error.message)
  }
}

const startAutoSignup = async () => {
  signupLoading.value = true
  signupComplete.value = false
  signupLog.value = ''
  let successCount = 0
  let failCount = 0
  for (let i = 0; i < selectedEmailIds.value.length; i++) {
    const emailId = selectedEmailIds.value[i]
    const emailObj = unregisteredEmails.value.find(e => e.email_id === emailId)
    signupLog.value += `【${i+1}/${selectedEmailIds.value.length}】正在注册邮箱: ${emailObj?.email || emailId} ...\n`
    try {
      const token = localStorage.getItem('accessToken')
      const response = await fetch(`${window.BASE_URL}/api/server_users/auto_signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ server_id: selectedServerId.value, email_id: emailId })
      })
      const data = await response.json()
      if (data.result === 'success') {
        signupLog.value += `✅ 注册成功：用户名：${data.username}，密码：${data.password}，邮箱：${data.email}\n`
        successCount++
      } else {
        signupLog.value += `❌ 注册失败：${data.msg || '未知错误'}\n`
        failCount++
      }
    } catch (error) {
      signupLog.value += `❌ 注册异常：${error.message}\n`
      failCount++
    }
  }
  signupLog.value += `\n批量注册完成，成功：${successCount}，失败：${failCount}\n`
  signupLoading.value = false
  signupComplete.value = true
  fetchUsers() // 注册后刷新用户列表
}

const isAllEmailsSelected = computed(() =>
  selectedEmailIds.value.length === unregisteredEmails.value.length && unregisteredEmails.value.length > 0
)
const toggleSelectAllEmails = () => {
  if (isAllEmailsSelected.value) {
    selectedEmailIds.value = []
  } else {
    selectedEmailIds.value = unregisteredEmails.value.map(e => e.email_id)
  }
}

// 处理筛选
const handleFilter = () => {
  currentPage.value = 1 // 重置页码
  fetchUsers()
}

// 页面加载时获取数据
onMounted(() => {
  fetchUsers()
  fetchServers()
  fetchEmails()
})
</script>

<style scoped>
.user-manage {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #2c3e50;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-dialog__body) {
  padding-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 
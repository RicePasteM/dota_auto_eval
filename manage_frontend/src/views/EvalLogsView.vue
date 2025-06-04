<template>
  <div class="eval-logs-container">
    <el-card class="submit-card">
      <template #header>
        <div class="card-header">
          <span>提交评估</span>
        </div>
      </template>
      <el-form :model="submitForm" label-width="120px">
        <el-form-item label="选择服务器">
          <el-select v-model="submitForm.server_id" placeholder="请选择服务器" @change="handleServerChange">
            <el-option
              v-for="server in servers"
              :key="server.server_id"
              :label="server.server_name"
              :value="server.server_id"
            />
          </el-select>
          <span v-if="remainingCounts !== null" class="remaining-counts">
            剩余验证次数：{{ remainingCounts }}
          </span>
        </el-form-item>
        <el-form-item label="评估文件">
          <el-upload
            ref="uploadRef"
            :action="null"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
          >
            <template #trigger>
              <el-button type="primary">选择文件</el-button>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submitEval" :loading="submitting">
            提交评估
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 进度消息框 -->
      <div v-if="progressMessages.length > 0" class="progress-messages">
        <div
          v-for="(msg, index) in progressMessages"
          :key="index"
          class="progress-message"
          :class="msg.type"
        >
          {{ msg.message }}
        </div>
      </div>
    </el-card>

    <el-card class="logs-card">
      <template #header>
        <div class="card-header">
          <span>评估日志</span>
          <el-button type="primary" @click="refreshLogs">刷新</el-button>
        </div>
      </template>
      
      <!-- 筛选区域 -->
      <div class="filter-container">
        <el-form :inline="true">
          <el-form-item label="服务器">
            <el-select v-model="filterForm.server_id" placeholder="选择服务器" clearable @change="handleFilter" style="width: 200px;">
              <el-option v-for="server in servers" :key="server.server_id" :label="server.server_name" :value="server.server_id" />
            </el-select>
          </el-form-item>
          <el-form-item label="用户名">
            <el-input
              v-model="filterForm.username"
              placeholder="输入用户名"
              clearable
              @keyup.enter="handleFilter"
              @clear="handleFilter"
              style="width: 200px;"
            />
          </el-form-item>
          <el-form-item label="创建日期">
            <el-date-picker
              v-model="filterForm.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              @change="handleFilter"
              style="width: 300px;"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleFilter">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetFilter">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <el-table :data="logs" style="width: 100%" v-loading="loading">
        <el-table-column prop="log_id" label="ID" width="80" />
        <el-table-column prop="server_name" label="服务器" width="120" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="create_time" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="eval_result" label="评估结果">
          <template #default="scope">
            <el-tag
              :type="getResultTagType(scope.row.eval_result)"
              size="small"
            >
              {{ getResultText(scope.row.eval_result) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="scope">
            <el-button
              link
              type="primary"
              @click="showResult(scope.row)"
              :disabled="!scope.row.eval_result"
            >
              查看详情
            </el-button>
            <el-button
              link
              type="primary"
              @click="downloadEvalFile(scope.row)"
              :disabled="!scope.row.eval_file_url"
            >
              下载文件
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 结果详情对话框 -->
    <el-dialog
      v-model="resultDialogVisible"
      title="评估结果详情"
      width="50%"
    >
      <pre class="result-detail">{{ selectedResult }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'

const servers = ref([])
const logs = ref([])
const loading = ref(false)
const submitting = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const uploadRef = ref()
const resultDialogVisible = ref(false)
const selectedResult = ref('')
const progressMessages = ref([])
const remainingCounts = ref(null)
let pollInterval = null
let currentTaskId = null

const submitForm = ref({
  server_id: '',
  file: null
})

// 添加筛选表单
const filterForm = ref({
  server_id: null,
  username: '',
  dateRange: []
})

// 获取服务器列表
const getServers = async () => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(`${window.BASE_URL}/api/servers?page=1&per_page=100`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (!response.ok) throw new Error('获取服务器列表失败')
    const data = await response.json()
    servers.value = data.items
  } catch (error) {
    ElMessage.error('获取服务器列表失败')
  }
}

// 获取日志列表
const getLogs = async () => {
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
    if (filterForm.value.username) {
      params.append('username', filterForm.value.username)
    }
    if (filterForm.value.dateRange && filterForm.value.dateRange.length === 2) {
      params.append('start_date', filterForm.value.dateRange[0])
      params.append('end_date', filterForm.value.dateRange[1])
    }

    const response = await fetch(
      `${window.BASE_URL}/api/eval/logs?${params.toString()}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    if (!response.ok) throw new Error('获取日志列表失败')
    const data = await response.json()
    logs.value = data.logs
    total.value = data.total
  } catch (error) {
    ElMessage.error('获取日志列表失败')
  } finally {
    loading.value = false
  }
}

// 处理文件选择
const handleFileChange = (file) => {
  submitForm.value.file = file.raw
}

// 轮询任务状态
const pollTaskStatus = async (taskId) => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(`${window.BASE_URL}/api/eval/task/${taskId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error('获取任务状态失败')
    }
    
    const data = await response.json()
    progressMessages.value = data.messages
    
    // 如果任务完成，停止轮询并刷新日志列表
    if (data.completed) {
      stopPolling()
      getLogs()
    }
  } catch (error) {
    console.error('轮询任务状态失败:', error)
    stopPolling()
  }
}

// 开始轮询
const startPolling = (taskId) => {
  currentTaskId = taskId
  // 立即执行一次
  pollTaskStatus(taskId)
  // 每3秒轮询一次
  pollInterval = setInterval(() => pollTaskStatus(taskId), 3000)
}

// 停止轮询
const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
  currentTaskId = null
}

// 提交评估
const submitEval = async () => {
  if (!submitForm.value.server_id) {
    ElMessage.warning('请选择服务器')
    return
  }
  if (!submitForm.value.file) {
    ElMessage.warning('请选择评估文件')
    return
  }

  submitting.value = true
  progressMessages.value = [] // 清空之前的消息
  
  try {
    const token = localStorage.getItem('accessToken')
    const formData = new FormData()
    formData.append('server_id', submitForm.value.server_id)
    formData.append('eval_file', submitForm.value.file)

    const response = await fetch(`${window.BASE_URL}/api/eval/submit`, {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.msg || '提交失败')
    }

    const data = await response.json()
    ElMessage.success('任务已提交')
    uploadRef.value.clearFiles()
    submitForm.value.file = null
    
    // 开始轮询任务状态
    startPolling(data.task_id)
    
  } catch (error) {
    ElMessage.error(error.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString()
}

// 获取结果标签类型
const getResultTagType = (result) => {
  if (!result) return 'info'
  if (result.includes('失败') || result.includes('异常') || result.includes('超时')) {
    return 'danger'
  }
  return 'success'
}

// 获取结果显示文本
const getResultText = (result) => {
  if (!result) return '等待中'
  if (result.length > 20) {
    return result.substring(0, 20) + '...'
  }
  return result
}

// 显示结果详情
const showResult = (row) => {
  selectedResult.value = row.eval_result
  resultDialogVisible.value = true
}

// 刷新日志
const refreshLogs = () => {
  getLogs()
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  getLogs()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  getLogs()
}

// 处理服务器选择变化
const handleServerChange = async (serverId) => {
  if (!serverId) {
    remainingCounts.value = null
    return
  }
  
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(
      `${window.BASE_URL}/api/eval/remaining_counts/${serverId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    
    if (!response.ok) {
      throw new Error('获取剩余次数失败')
    }
    
    const data = await response.json()
    remainingCounts.value = data.remaining_counts
  } catch (error) {
    ElMessage.error(error.message || '获取剩余次数失败')
    remainingCounts.value = null
  }
}

// 处理筛选
const handleFilter = () => {
  currentPage.value = 1 // 重置页码
  getLogs()
}

// 重置筛选
const resetFilter = () => {
  filterForm.value = {
    server_id: null,
    username: '',
    dateRange: []
  }
  handleFilter()
}

// 下载评估文件
const downloadEvalFile = async (row) => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(
      `${window.BASE_URL}/api/eval/download/${row.log_id}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.msg || '下载失败')
    }
    
    // 创建Blob对象并下载
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = row.eval_file_url.split('/').pop() // 使用原始文件名
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
  } catch (error) {
    ElMessage.error(error.message || '下载失败')
  }
}

onMounted(() => {
  getServers()
  getLogs()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<style scoped>
.eval-logs-container {
  padding: 20px;
}

.submit-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.result-detail {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
}

.progress-messages {
  margin-top: 20px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  background-color: #f5f7fa;
}

.progress-message {
  padding: 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  font-size: 14px;
}

.progress-message.info {
  background-color: #ecf5ff;
  color: #409eff;
}

.progress-message.success {
  background-color: #f0f9eb;
  color: #67c23a;
}

.progress-message.warning {
  background-color: #fdf6ec;
  color: #e6a23c;
}

.progress-message.error {
  background-color: #fef0f0;
  color: #f56c6c;
}

.remaining-counts {
  margin-left: 15px;
  color: #409EFF;
  font-size: 14px;
}
</style> 
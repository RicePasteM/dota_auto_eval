<template>
  <div class="email-manage">
    <div class="page-header">
      <h2>邮箱管理</h2>
      <el-button type="primary" @click="showCreateWizard">
        <el-icon><Plus /></el-icon>批量创建邮箱
      </el-button>
    </div>

    <!-- 邮箱列表表格 -->
    <el-table
      v-loading="loading"
      :data="emails"
      style="width: 100%"
      border
    >
      <el-table-column prop="email_id" label="ID" width="80" />
      <el-table-column prop="email" label="邮箱地址" min-width="200">
        <template #default="{ row }">
          {{ row.email }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
          <el-button
            size="small"
            type="primary"
            @click="handleViewInbox(scope.row)"
          >
            收件箱
          </el-button>
          <el-button
            size="small"
            type="danger"
            @click="handleDelete(scope.row)"
          >
            删除
          </el-button>
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

    <!-- 创建向导对话框 -->
    <el-dialog
      v-model="wizardVisible"
      title="批量创建邮箱"
      width="600px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div v-if="!isCreating">
        <el-form
          ref="createFormRef"
          :model="createForm"
          :rules="rules"
          label-width="120px"
        >
          <el-form-item label="创建数量" prop="count">
            <el-input-number
              v-model="createForm.count"
              :min="1"
              :max="20"
              controls-position="right"
            />
          </el-form-item>
          <el-form-item label="创建延迟 (毫秒)" prop="delay">
            <el-input-number
              v-model="createForm.delay"
              :min="0"
              :step="100"
              controls-position="right"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <div v-else class="creation-progress">
        <el-progress 
          :percentage="creationProgress" 
          :format="progressFormat"
          :status="creationStatus"
        />
        <div class="creation-log">
          <div class="log-content" ref="logContent">
            <p v-for="(log, index) in creationLogs" :key="index" :class="log.type">
              {{ log.message }}
            </p>
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button 
            @click="handleCloseWizard" 
            :disabled="isCreating && !isCreationComplete"
          >
            {{ isCreationComplete ? '关闭' : '取消' }}
          </el-button>
          <el-button 
            type="primary" 
            @click="handleStartCreation" 
            v-if="!isCreating"
            :loading="submitting"
          >
            开始创建
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 收件箱对话框 -->
    <el-dialog
      v-model="inboxVisible"
      :title="`收件箱 - ${currentEmail?.email || ''}`"
      width="800px"
    >
      <div v-loading="loadingInbox">
        <el-empty v-if="!loadingInbox && (!messages || messages.length === 0)" description="暂无邮件" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="msg in messages"
            :key="msg.mid"
            :timestamp="formatEmailDate(msg.textDate)"
            placement="top"
          >
            <el-card>
              <template #header>
                <div class="email-header">
                  <span class="from">发件人：{{ msg.textFrom }}</span>
                  <span class="subject">主题：{{ msg.textSubject }}</span>
                </div>
              </template>
              <div class="email-content">
                <p>收件人：{{ msg.textTo }}</p>
                <el-button 
                  type="primary" 
                  link 
                  @click="handleViewMessage(msg.mid)"
                  :loading="loadingMessage === msg.mid"
                >
                  查看内容
                </el-button>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="inboxVisible = false">关闭</el-button>
          <el-button type="primary" @click="refreshInbox" :loading="loadingInbox">
            刷新
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 邮件内容对话框 -->
    <el-dialog
      v-model="messageVisible"
      :title="'邮件内容'"
      width="800px"
      append-to-body
    >
      <div v-loading="loadingMessageContent">
        <iframe v-if="messageContent" :src="`data:text/html;charset=utf-8,${encodeURIComponent(messageContent)}`" class="message-body"></iframe>
        <el-empty v-else description="无内容" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { ElTimeline, ElTimelineItem } from 'element-plus'

const loading = ref(false)
const submitting = ref(false)
const emails = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 创建向导相关
const wizardVisible = ref(false)
const isCreating = ref(false)
const isCreationComplete = ref(false)
const createFormRef = ref(null)
const createForm = ref({
  count: 1,
  delay: 1000 // 默认延迟1000毫秒
})
const creationLogs = ref([])
const logContent = ref(null)
const createdCount = ref(0)
const totalToCreate = ref(0)

// 收件箱相关
const inboxVisible = ref(false)
const loadingInbox = ref(false)
const messages = ref([])
const currentEmail = ref(null)

// 邮件内容相关
const messageVisible = ref(false)
const loadingMessage = ref(null)
const loadingMessageContent = ref(false)
const messageContent = ref('')

const rules = {
  count: [
    { required: true, message: '请输入创建数量', trigger: 'blur' },
    { type: 'number', min: 1, max: 20, message: '数量必须在1到20之间', trigger: 'blur' }
  ],
  delay: [
    { required: true, message: '请输入创建延迟', trigger: 'blur' },
    { type: 'number', min: 0, message: '延迟必须大于等于0', trigger: 'blur' }
  ]
}

// 计算创建进度
const creationProgress = computed(() => {
  if (totalToCreate.value === 0) return 0
  return Math.round((createdCount.value / totalToCreate.value) * 100)
})

const creationStatus = computed(() => {
  if (creationProgress.value === 100) return 'success'
  return ''
})

const progressFormat = (percentage) => {
  return `${createdCount.value}/${totalToCreate.value}`
}

// 显示创建向导
const showCreateWizard = () => {
  wizardVisible.value = true
  isCreating.value = false
  isCreationComplete.value = false
  createForm.value.count = 1
  createForm.value.delay = 1000 // 重置延迟为默认值
  creationLogs.value = []
  createdCount.value = 0
  totalToCreate.value = 0
}

// 添加日志
const addLog = (message, type = 'info') => {
  creationLogs.value.push({ message, type })
  // 自动滚动到底部
  setTimeout(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  }, 0)
}

// 开始创建邮箱
const handleStartCreation = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      isCreating.value = true
      totalToCreate.value = createForm.value.count
      createdCount.value = 0
      
      addLog(`开始创建 ${totalToCreate.value} 个邮箱，每个延迟 ${createForm.value.delay} 毫秒...`)
      
      for (let i = 0; i < totalToCreate.value; i++) {
        try {
          const token = localStorage.getItem('accessToken')
          const response = await fetch(`${window.BASE_URL}/api/emails`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          const data = await response.json()
          if (!response.ok) {
            const errorDetail = data.detail ? `\n详细信息：${JSON.stringify(data.detail, null, 2)}` : ''
            throw new Error(`${data.msg || '创建失败'}${errorDetail}`)
          }
          
          createdCount.value++
          addLog(`✅ 成功创建邮箱: ${data.email.email}`, 'success')
        } catch (error) {
          const errorMessage = error.message.split('\n')
          // 添加主要错误信息
          addLog(`❌ 创建失败: ${errorMessage[0]}`, 'error')
          // 如果有详细信息，分行添加
          if (errorMessage.length > 1) {
            errorMessage.slice(1).forEach(line => {
              addLog(`   ${line}`, 'error')
            })
          }
        }
        
        // 添加小延迟，避免请求过快
        if (createForm.value.delay > 0 && i < totalToCreate.value - 1) { // 最后一个不需要延迟
          await new Promise(resolve => setTimeout(resolve, createForm.value.delay))
        }
      }
      
      addLog(`批量创建完成，成功创建 ${createdCount.value} 个邮箱`)
      isCreationComplete.value = true
      fetchEmails()
    }
  })
}

// 关闭向导
const handleCloseWizard = () => {
  if (isCreating.value && !isCreationComplete.value) {
    ElMessageBox.confirm(
      '正在创建邮箱，确定要取消吗？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    ).then(() => {
      wizardVisible.value = false
    })
  } else {
    wizardVisible.value = false
  }
}

// 获取邮箱列表
const fetchEmails = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(
      `${window.BASE_URL}/api/emails?page=${currentPage.value}&per_page=${pageSize.value}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取邮箱列表失败')
    
    emails.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

// 处理删除
const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除邮箱 "${row.email}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const token = localStorage.getItem('accessToken')
      const response = await fetch(`${window.BASE_URL}/api/emails/${row.email_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.msg || '删除失败')
      
      ElMessage.success('删除成功')
      fetchEmails()
    } catch (error) {
      ElMessage.error(error.message)
    }
  })
}

// 处理分页
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchEmails()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchEmails()
}

// 查看收件箱
const handleViewInbox = async (row) => {
  currentEmail.value = row
  inboxVisible.value = true
  await refreshInbox()
}

// 刷新收件箱
const refreshInbox = async () => {
  if (!currentEmail.value) return
  
  loadingInbox.value = true
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(
      `${window.BASE_URL}/api/emails/${currentEmail.value.email_id}/inbox`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取收件箱失败')
    
    messages.value = data.messages || []
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loadingInbox.value = false
  }
}

// 格式化邮件日期
const formatEmailDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 查看邮件内容
const handleViewMessage = async (messageId) => {
  if (!currentEmail.value) return
  
  loadingMessage.value = messageId
  loadingMessageContent.value = true
  messageVisible.value = true
  messageContent.value = ''
  
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(
      `${window.BASE_URL}/api/emails/${currentEmail.value.email_id}/messages/${messageId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取邮件内容失败')
    
    messageContent.value = data.body || '无内容'
  } catch (error) {
    ElMessage.error(error.message)
    messageVisible.value = false
  } finally {
    loadingMessage.value = null
    loadingMessageContent.value = false
  }
}

// 页面加载时获取数据
onMounted(() => {
  fetchEmails()
})
</script>

<style scoped>
.email-manage {
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

.payload-text {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: monospace;
}

.creation-progress {
  padding: 20px 0;
}

.creation-log {
  margin-top: 20px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
}

.log-content {
  height: 300px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.5;
  padding: 10px;
  background: #f8f9fa;
}

.log-content p {
  margin: 5px 0;
}

.log-content .error {
  color: #f56c6c;
}

.log-content .success {
  color: #67c23a;
}

.log-content .info {
  color: #909399;
}

:deep(.el-dialog__body) {
  padding-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-tag) {
  font-family: monospace;
}

.email-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.email-header .from,
.email-header .subject {
  font-weight: bold;
}

.email-content {
  margin-top: 10px;
  color: #666;
}

:deep(.el-timeline-item__content) {
  width: 100%;
}

:deep(.el-card__header) {
  padding: 10px 20px;
}

:deep(.el-card__body) {
  padding: 15px 20px;
}

.message-body {
  background: #f8f9fa;
  border-radius: 4px;
  border: 0;
  white-space: pre-wrap;
  font-family: monospace;
  width: 100%;
  height: 700px;
  overflow-y: auto;
}

.message-body :deep(img) {
  max-width: 100%;
  height: auto;
}

.message-body :deep(a) {
  color: #409EFF;
  text-decoration: none;
}

.message-body :deep(a):hover {
  text-decoration: underline;
}
</style> 
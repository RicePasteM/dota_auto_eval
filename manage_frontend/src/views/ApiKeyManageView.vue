<template>
  <div class="api-key-manage">
    <div class="page-header">
      <h2>API Key管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>创建API Key
      </el-button>
    </div>

    <!-- API Key列表表格 -->
    <el-table
      v-loading="loading"
      :data="apiKeys"
      style="width: 100%"
      border
    >
      <el-table-column prop="key_id" label="ID" width="80" />
      <el-table-column prop="api_key" label="API Key" min-width="400">
        <template #default="{ row }">
          <div class="api-key-cell">
            <el-tag 
              class="api-key-tag" 
              type="info"
              :class="{ 'inactive': !row.is_active }"
            >
              {{ row.api_key }}
            </el-tag>
            <el-button
              link
              type="primary"
              v-if="row.api_key"
              @click="copyApiKey(row.api_key)"
            >
              复制
            </el-button>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="last_used_at" label="最后使用" width="180">
        <template #default="{ row }">
          {{ row.last_used_at ? formatDate(row.last_used_at) : '从未使用' }}
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
          <el-button
            size="small"
            :type="scope.row.is_active ? 'warning' : 'success'"
            @click="handleToggle(scope.row)"
          >
            {{ scope.row.is_active ? '禁用' : '启用' }}
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

    <!-- 创建API Key对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建API Key"
      width="500px"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            placeholder="请输入API Key的用途描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCreate" :loading="creating">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 新API Key展示对话框 -->
    <el-dialog
      v-model="showKeyDialogVisible"
      title="API Key创建成功"
      width="600px"
    >
      <div class="new-key-info">
        <div class="key-display">
          <el-tag class="api-key-tag" type="success">{{ newApiKey }}</el-tag>
          <el-button type="primary" @click="copyApiKey(newApiKey)">
            复制
          </el-button>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="showKeyDialogVisible = false">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const creating = ref(false)
const apiKeys = ref([])
const createDialogVisible = ref(false)
const showKeyDialogVisible = ref(false)
const newApiKey = ref('')

const createFormRef = ref(null)
const createForm = ref({
  description: ''
})

const rules = {
  description: [
    { required: true, message: '请输入描述', trigger: 'blur' },
    { min: 1, max: 200, message: '长度在1到200个字符', trigger: 'blur' }
  ]
}

// 获取API Key列表
const fetchApiKeys = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(
      `${window.BASE_URL}/api/api-keys`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取API Key列表失败')
    
    apiKeys.value = data.items
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  createDialogVisible.value = true
  createForm.value.description = ''
}

// 创建API Key
const handleCreate = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      creating.value = true
      try {
        const token = localStorage.getItem('accessToken')
        const response = await fetch(`${window.BASE_URL}/api/api-keys`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(createForm.value)
        })
        
        const data = await response.json()
        if (!response.ok) throw new Error(data.msg || '创建失败')
        
        createDialogVisible.value = false
        newApiKey.value = data.api_key
        showKeyDialogVisible.value = true
        await fetchApiKeys()
      } catch (error) {
        ElMessage.error(error.message)
      } finally {
        creating.value = false
      }
    }
  })
}

// 删除API Key
const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除这个API Key吗？删除后将无法恢复。`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const token = localStorage.getItem('accessToken')
      const response = await fetch(
        `${window.BASE_URL}/api/api-keys/${row.key_id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      const data = await response.json()
      if (!response.ok) throw new Error(data.msg || '删除失败')
      
      ElMessage.success('删除成功')
      await fetchApiKeys()
    } catch (error) {
      ElMessage.error(error.message)
    }
  })
}

// 切换API Key状态
const handleToggle = async (row) => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(
      `${window.BASE_URL}/api/api-keys/${row.key_id}/toggle`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '操作失败')
    
    await fetchApiKeys()
    ElMessage.success(`${data.is_active ? '启用' : '禁用'}成功`)
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 复制API Key
const copyApiKey = async (apiKey) => {
  try {
    await navigator.clipboard.writeText(apiKey)
    ElMessage.success('复制成功')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 格式化日期
const formatDate = (dateStr) => {
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

// 页面加载时获取数据
onMounted(() => {
  fetchApiKeys()
})
</script>

<style scoped>
.api-key-manage {
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

.api-key-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.api-key-tag {
  font-family: monospace;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.api-key-tag.inactive {
  text-decoration: line-through;
  opacity: 0.7;
}

.new-key-info {
  text-align: center;
}

.warning-text {
  color: #e6a23c;
  font-weight: bold;
  margin-bottom: 20px;
}

.key-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin: 20px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 
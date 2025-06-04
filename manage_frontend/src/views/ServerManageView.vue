<template>
  <div class="server-manage">
    <div class="page-header">
      <h2>服务器管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>添加服务器
      </el-button>
    </div>

    <!-- 服务器列表表格 -->
    <el-table
      v-loading="loading"
      :data="servers"
      style="width: 100%"
      border
    >
      <el-table-column prop="server_id" label="ID" width="80" />
      <el-table-column prop="server_name" label="服务器名称" />
      <el-table-column prop="server_url" label="服务器地址" />
      <el-table-column prop="limits_per_day" label="每日限制" width="100" />
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

    <!-- 添加/编辑服务器对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '添加服务器' : '编辑服务器'"
      width="500px"
    >
      <el-form
        ref="serverFormRef"
        :model="serverForm"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="服务器名称" prop="server_name">
          <el-input v-model="serverForm.server_name" />
        </el-form-item>
        <el-form-item label="服务器地址" prop="server_url">
          <el-input v-model="serverForm.server_url" />
        </el-form-item>
        <el-form-item label="每日限制" prop="limits_per_day">
          <el-input-number
            v-model="serverForm.limits_per_day"
            :min="1"
            :max="100"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
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
const submitting = ref(false)
const servers = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const dialogType = ref('add')
const serverFormRef = ref(null)

const serverForm = ref({
  server_name: '',
  server_url: '',
  limits_per_day: 2
})

const rules = {
  server_name: [
    { required: true, message: '请输入服务器名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  server_url: [
    { required: true, message: '请输入服务器地址', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  limits_per_day: [
    { required: true, message: '请输入每日限制次数', trigger: 'blur' },
    { type: 'number', min: 1, message: '必须大于0', trigger: 'blur' }
  ]
}

// 获取服务器列表
const fetchServers = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(
      `${window.BASE_URL}/api/servers?page=${currentPage.value}&per_page=${pageSize.value}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取服务器列表失败')
    
    servers.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

// 显示添加对话框
const showAddDialog = () => {
  dialogType.value = 'add'
  serverForm.value = {
    server_name: '',
    server_url: '',
    limits_per_day: 2
  }
  dialogVisible.value = true
}

// 显示编辑对话框
const handleEdit = (row) => {
  dialogType.value = 'edit'
  serverForm.value = { ...row }
  dialogVisible.value = true
}

// 处理删除
const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除服务器 "${row.server_name}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const token = localStorage.getItem('accessToken')
      const response = await fetch(`${window.BASE_URL}/api/servers/${row.server_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.msg || '删除失败')
      
      ElMessage.success('删除成功')
      fetchServers()
    } catch (error) {
      ElMessage.error(error.message)
    }
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!serverFormRef.value) return
  
  await serverFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const token = localStorage.getItem('accessToken')
        const url = dialogType.value === 'add' 
          ? `${window.BASE_URL}/api/servers`
          : `${window.BASE_URL}/api/servers/${serverForm.value.server_id}`
        
        const response = await fetch(url, {
          method: dialogType.value === 'add' ? 'POST' : 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(serverForm.value)
        })
        
        const data = await response.json()
        if (!response.ok) throw new Error(data.msg || '操作失败')
        
        ElMessage.success(dialogType.value === 'add' ? '添加成功' : '更新成功')
        dialogVisible.value = false
        fetchServers()
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
  fetchServers()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchServers()
}

// 页面加载时获取数据
onMounted(() => {
  fetchServers()
})
</script>

<style scoped>
.server-manage {
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
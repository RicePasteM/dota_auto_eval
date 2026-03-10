<template>
  <div class="training-tasks-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <h3>训练任务管理</h3>
          <el-button type="primary" @click="showAddDialog">添加训练任务</el-button>
        </div>
      </template>

      <!-- 任务列表 -->
      <el-table :data="tableData" style="width: 100%" v-loading="loading">
        <el-table-column prop="task_id" label="ID" width="80" />
        <el-table-column prop="task_name" label="任务名称" />
        <el-table-column prop="server_name" label="服务器" />
        <el-table-column prop="created_at" label="创建时间">
          <template #default="scope">
            {{ new Date(scope.row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320">
          <template #default="scope">
            <el-button size="small" @click="handleViewDetail(scope.row)">详情</el-button>
            <el-button size="small" type="success" @click="handleSubmitEpoch(scope.row)" :disabled="scope.row.status !== 'active'">提交训练结果</el-button>
            <el-dropdown @command="(cmd) => handleCommand(cmd, scope.row)" style="margin-left: 10px;">
              <el-button size="small" type="primary">
                状态 <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :disabled="scope.row.status === 'active'" command="active">激活</el-dropdown-item>
                  <el-dropdown-item :disabled="scope.row.status === 'inactive'" command="inactive">暂停</el-dropdown-item>
                  <el-dropdown-item :disabled="scope.row.status === 'completed'" command="completed">完成</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button size="small" type="danger" @click="handleDeleteTask(scope.row)" style="margin-left: 10px;">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页组件 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 添加训练任务对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加训练任务" width="500px">
      <el-form ref="addFormRef" :model="addForm" label-width="120px" :rules="rules">
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="addForm.task_name" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="addForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="服务器" prop="server_id">
          <el-select v-model="addForm.server_id" placeholder="请选择服务器">
            <el-option
              v-for="server in serverList"
              :key="server.server_id"
              :label="server.server_name"
              :value="server.server_id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleAddTask" :loading="submitting">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 提交训练结果对话框 -->
    <el-dialog v-model="submitDialogVisible" title="提交训练结果" width="500px">
      <el-form ref="submitFormRef" :model="submitForm" label-width="120px" :rules="submitRules">
        <el-form-item label="Epoch" prop="epoch">
          <el-input-number v-model="submitForm.epoch" :min="1" :step="1" />
        </el-form-item>
        <el-form-item label="评估文件">
          <el-upload
            class="upload-demo"
            action="#"
            :http-request="handleUpload"
            :limit="1"
            :on-exceed="handleExceed"
            :on-remove="handleRemove"
            :auto-upload="true"
            :multiple="false"
            accept=".zip"
            ref="uploadRef"
          >
            <template #trigger>
              <el-button type="primary">选择文件</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                只能上传zip文件
              </div>
            </template>
          </el-upload>
          <div v-if="!hasUploadedFile" class="error-tip">请选择评估文件</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="submitDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmitEpochConfirm" :loading="submitting">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

// 表格数据
const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 添加对话框
const addDialogVisible = ref(false)
const addFormRef = ref(null)
const addForm = reactive({
  task_name: '',
  description: '',
  server_id: ''
})

// 提交对话框
const submitDialogVisible = ref(false)
const submitFormRef = ref(null)
const uploadRef = ref(null)
const submitForm = reactive({
  epoch: 1,
  task_id: null,
  server_id: null,
  eval_file: null
})

// 其它数据
const serverList = ref([])
const submitting = ref(false)
const hasUploadedFile = ref(false)

// 表单验证规则
const rules = {
  task_name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度应为2-50个字符', trigger: 'blur' }
  ],
  server_id: [
    { required: true, message: '请选择服务器', trigger: 'change' }
  ]
}

const submitRules = {
  epoch: [
    { required: true, message: '请输入Epoch数值', trigger: 'blur' }
  ]
}

// 生命周期钩子
onMounted(() => {
  const savedPage = sessionStorage.getItem('trainingListPage')
  if (savedPage) {
    currentPage.value = parseInt(savedPage)
    sessionStorage.removeItem('trainingListPage')
  }
  fetchTrainingTasks()
  fetchServers()
})

// 方法
const fetchTrainingTasks = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/training', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value
      }
    })
    tableData.value = response.data.tasks
    total.value = response.data.total
  } catch (error) {
    console.error('获取训练任务失败:', error)
    ElMessage.error('获取训练任务失败')
  } finally {
    loading.value = false
  }
}

const fetchServers = async () => {
  try {
    const response = await axios.get('/api/servers')
    serverList.value = response.data.items
  } catch (error) {
    console.error('获取服务器列表失败:', error)
    ElMessage.error('获取服务器列表失败')
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  fetchTrainingTasks()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchTrainingTasks()
}

const showAddDialog = () => {
  addDialogVisible.value = true
  // 重置表单
  if (addFormRef.value) {
    addFormRef.value.resetFields()
  }
}

const handleAddTask = async () => {
  if (!addFormRef.value) return

  await addFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const response = await axios.post('/api/training', addForm)
      ElMessage.success('添加训练任务成功')
      addDialogVisible.value = false
      fetchTrainingTasks()
    } catch (error) {
      console.error('添加训练任务失败:', error)
      ElMessage.error('添加训练任务失败')
    } finally {
      submitting.value = false
    }
  })
}

const getStatusType = (status) => {
  switch (status) {
    case 'active': return 'success'
    case 'inactive': return 'info'
    case 'completed': return 'warning'
    default: return 'info'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'active': return '激活'
    case 'inactive': return '暂停'
    case 'completed': return '已完成'
    default: return '未知'
  }
}

const handleViewDetail = (row) => {
  sessionStorage.setItem('trainingListPage', currentPage.value)
  router.push(`/training/${row.task_id}`)
}

const handleSubmitEpoch = (row) => {
  submitDialogVisible.value = true
  submitForm.task_id = row.task_id
  submitForm.server_id = row.server_id
  submitForm.epoch = 1
  submitForm.eval_file = null
  hasUploadedFile.value = false
  
  // 重置上传组件
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const handleUpload = (options) => {
  submitForm.eval_file = options.file
  hasUploadedFile.value = true
}

const handleRemove = () => {
  submitForm.eval_file = null
  hasUploadedFile.value = false
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const handleSubmitEpochConfirm = async () => {
  if (!submitFormRef.value) return
  
  await submitFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    if (!hasUploadedFile.value) {
      ElMessage.warning('请选择评估文件')
      return
    }
    
    submitting.value = true
    try {
      const formData = new FormData()
      formData.append('epoch', submitForm.epoch)
      formData.append('eval_file', submitForm.eval_file)
      
      const response = await axios.post(`/api/training/${submitForm.task_id}/epoch`, formData)
      ElMessage.success('提交训练结果成功')
      submitDialogVisible.value = false
    } catch (error) {
      console.error('提交训练结果失败:', error)
      ElMessage.error('提交训练结果失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleCommand = async (command, row) => {
  try {
    const response = await axios.put(`/api/training/${row.task_id}/status`, {
      status: command
    })
    ElMessage.success('状态更新成功')
    fetchTrainingTasks()
  } catch (error) {
    console.error('更新状态失败:', error)
    ElMessage.error('更新状态失败')
  }
}

const handleDeleteTask = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除训练任务"${row.task_name}"吗？此操作将同时删除该任务下的所有评测结果，且不可恢复。`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await axios.delete(`/api/training/${row.task_id}`)
    ElMessage.success('删除成功')
    fetchTrainingTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.msg || '删除失败')
    }
  }
}
</script>

<style scoped>
.training-tasks-container {
  padding: 20px;
}

.box-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.upload-demo {
  width: 100%;
}

.error-tip {
  color: red;
  margin-top: 10px;
}
</style> 
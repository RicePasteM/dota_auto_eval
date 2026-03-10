<template>
  <div class="training-detail-container">
    <el-card class="box-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button @click="goBack" icon="ArrowLeft">返回</el-button>
            <h3>训练任务详情</h3>
          </div>
          <div class="header-right" v-if="taskDetail">
            <el-button type="success" @click="handleSubmitEpoch" :disabled="taskDetail.status !== 'active'">提交训练结果</el-button>
            <el-button type="primary" @click="exportToHtml">导出</el-button>
            <el-tag :type="getStatusType(taskDetail.status)">{{ getStatusText(taskDetail.status) }}</el-tag>
          </div>
        </div>
      </template>

      <!-- 任务详情 -->
      <div v-if="taskDetail" class="task-info">
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="任务ID">{{ taskDetail.task_id }}</el-descriptions-item>
          <el-descriptions-item label="任务名称">{{ taskDetail.task_name }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ new Date(taskDetail.created_at).toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="服务器">{{ taskDetail.server_name }}</el-descriptions-item>
          <el-descriptions-item label="API密钥ID" v-if="taskDetail.api_key_id">{{ taskDetail.api_key_id }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ taskDetail.description || '无' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 结果列表 -->
      <div v-if="taskDetail && taskDetail.results" class="results-section">
        <h4 class="section-title">训练结果列表</h4>

        <el-table :data="taskDetail.results" style="width: 100%">
          <el-table-column prop="result_id" label="ID" width="80" />
          <el-table-column prop="epoch" label="Epoch" width="80" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getResultStatusType(scope.row.status)">{{ getResultStatusText(scope.row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="VOC mAP" width="100">
            <template #default="scope">
              <span v-if="scope.row.status === 'completed'">
                {{ getParsedMetric(scope.row.result_id, 'mAP') }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="COCO AP50" width="100">
            <template #default="scope">
              <span v-if="scope.row.status === 'completed'">
                {{ getParsedMetric(scope.row.result_id, 'AP50') }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="COCO AP75" width="100">
            <template #default="scope">
              <span v-if="scope.row.status === 'completed'">
                {{ getParsedMetric(scope.row.result_id, 'AP75') }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="COCO mAP" width="100">
            <template #default="scope">
              <span v-if="scope.row.status === 'completed'">
                {{ getParsedMetric(scope.row.result_id, 'cocoMAP') }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="submitted_at" label="提交时间" width="180">
            <template #default="scope">
              {{ new Date(scope.row.submitted_at).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column prop="completed_at" label="完成时间" width="180">
            <template #default="scope">
              {{ scope.row.completed_at ? new Date(scope.row.completed_at).toLocaleString() : '未完成' }}
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="scope">
              <el-button 
                size="small" 
                type="primary" 
                @click="showResultDetail(scope.row)" 
                :disabled="scope.row.status !== 'completed'"
              >
                查看结果
              </el-button>
              <el-button 
                size="small" 
                :type="['pending', 'processing', 'retrying'].includes(scope.row.status) ? 'warning' : 'info'"
                @click="showProgressOutput(scope.row)"
              >
                处理进度
              </el-button>
              <el-button 
                size="small" 
                type="success"
                @click="rerunEvaluation(scope.row)"
                :disabled="scope.row.status === 'processing' || rerunningResultId === scope.row.result_id"
                :loading="rerunningResultId === scope.row.result_id"
              >
                重新评测
              </el-button>
              <el-button 
                size="small" 
                type="danger"
                @click="deleteResult(scope.row)"
                :disabled="deletingResultId === scope.row.result_id"
                :loading="deletingResultId === scope.row.result_id"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 训练进度可视化 -->
      <div v-if="parsedResults.length > 0" class="results-section">
        <h4 class="section-title">训练进度可视化</h4>
        
        <!-- 四个独立的指标图表 -->
        <h4 class="subsection-title">评估指标趋势</h4>
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="chart-container">
              <h5 class="chart-title">VOC mAP</h5>
              <div ref="vocMapChartRef" class="chart"></div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="chart-container">
              <h5 class="chart-title">COCO AP50</h5>
              <div ref="ap50ChartRef" class="chart"></div>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" class="chart-row">
          <el-col :span="12">
            <div class="chart-container">
              <h5 class="chart-title">COCO AP75</h5>
              <div ref="ap75ChartRef" class="chart"></div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="chart-container">
              <h5 class="chart-title">COCO mAP</h5>
              <div ref="cocoMapChartRef" class="chart"></div>
            </div>
          </el-col>
        </el-row>
        
        <!-- 类别AP变化图表 -->
        <h4 class="subsection-title">各类别AP值变化趋势</h4>
        <div class="class-charts-container">
          <el-row :gutter="20">
            <template v-if="latestResult && latestResult.classAps.length > 0">
              <el-col :span="12" v-for="(classItem, index) in latestResult.classAps" :key="classItem.class">
                <div class="chart-container">
                  <h5 class="chart-title">{{ classItem.class }}</h5>
                  <div :ref="el => classChartRefs[index] = el" class="chart class-chart"></div>
                </div>
              </el-col>
            </template>
          </el-row>
        </div>
      </div>
    </el-card>

    <!-- 结果详情对话框 -->
    <el-dialog v-model="resultDialogVisible" title="评估结果详情" width="80%">
      <div v-if="selectedResult">
        <h4>Epoch {{ selectedResult.epoch }} 评估结果</h4>
        
        <div v-if="selectedParsedResult" class="parsed-result">
          <el-tabs>
            <el-tab-pane label="解析结果">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-card class="metric-card">
                    <template #header>
                      <div class="metric-header">
                        <span>VOC 指标</span>
                      </div>
                    </template>
                    <div class="metric-content">
                      <div class="metric-item">
                        <span class="metric-label">mAP:</span>
                        <span class="metric-value">{{ selectedParsedResult.metrics.mAP.toFixed(4) }}</span>
                      </div>
                    </div>
                  </el-card>
                </el-col>
                
                <el-col :span="12">
                  <el-card class="metric-card">
                    <template #header>
                      <div class="metric-header">
                        <span>COCO 指标</span>
                      </div>
                    </template>
                    <div class="metric-content">
                      <div class="metric-item">
                        <span class="metric-label">AP50:</span>
                        <span class="metric-value">{{ selectedParsedResult.metrics.AP50.toFixed(4) }}</span>
                      </div>
                      <div class="metric-item">
                        <span class="metric-label">AP75:</span>
                        <span class="metric-value">{{ selectedParsedResult.metrics.AP75.toFixed(4) }}</span>
                      </div>
                      <div class="metric-item">
                        <span class="metric-label">mAP:</span>
                        <span class="metric-value">{{ selectedParsedResult.metrics.cocoMAP.toFixed(4) }}</span>
                      </div>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
              
              <h4 class="subsection-title">各类别AP值</h4>
              <el-table :data="selectedParsedResult.classAps" style="width: 100%">
                <el-table-column prop="class" label="类别" />
                <el-table-column prop="ap" label="AP">
                  <template #default="scope">
                    {{ scope.row.ap.toFixed(4) }}
                  </template>
                </el-table-column>
                <el-table-column label="可视化">
                  <template #default="scope">
                    <div class="ap-bar-container">
                      <div class="ap-bar" :style="{ width: `${scope.row.ap * 100}%` }"></div>
                      <span class="ap-value">{{ (scope.row.ap * 100).toFixed(1) }}%</span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              
              <h4 class="subsection-title">提交信息</h4>
              <el-descriptions border>
                <el-descriptions-item v-for="(value, key) in selectedParsedResult.submissionInfo" 
                  :key="key" :label="key">{{ value }}</el-descriptions-item>
              </el-descriptions>
            </el-tab-pane>
            <el-tab-pane label="原始结果">
              <pre class="result-detail-text">{{ selectedResult.eval_result }}</pre>
            </el-tab-pane>
          </el-tabs>
        </div>
        <div v-else>
          <pre class="result-detail-text">{{ selectedResult.eval_result }}</pre>
        </div>
      </div>
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

    <!-- 处理进度对话框 -->
    <el-dialog v-model="progressDialogVisible" title="处理进度详情" width="70%">
      <div class="progress-header">
        <span v-if="isProcessing" class="processing-tag">处理中</span>
        <el-button size="small" type="primary" @click="manualRefreshProgress" :loading="refreshing">
          刷新
        </el-button>
      </div>
      <div v-if="selectedProgressOutput && selectedProgressOutput.length > 0">
        <el-timeline>
          <el-timeline-item
            v-for="(item, index) in selectedProgressOutput"
            :key="index"
            :type="getProgressItemType(item.type)"
            :timestamp="item.timestamp ? new Date(item.timestamp).toLocaleString() : ''"
            :hollow="item.type === 'info'"
          >
            <div class="progress-message" :class="'progress-' + item.type">
              {{ item.message }}
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
      <div v-else class="empty-progress">
        <el-empty description="暂无处理进度信息"></el-empty>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import * as echarts from 'echarts'

const router = useRouter()
const route = useRoute()
const taskId = ref(route.params.id)

// 数据
const loading = ref(false)
const taskDetail = ref(null)
const resultDialogVisible = ref(false)
const selectedResult = ref(null)
const parsedResults = ref([])
const selectedParsedResult = ref(null)
const progressDialogVisible = ref(false)
const selectedProgressOutput = ref([])
const refreshTimer = ref(null)
const currentResultId = ref(null)
const isProcessing = ref(false)
const refreshing = ref(false)
const rerunningResultId = ref(null)
const deletingResultId = ref(null)
const submitDialogVisible = ref(false)
const submitFormRef = ref(null)
const uploadRef = ref(null)
const submitForm = reactive({
  epoch: 1
})
const submitting = ref(false)
const hasUploadedFile = ref(false)

const submitRules = {
  epoch: [
    { required: true, message: '请输入Epoch数值', trigger: 'blur' }
  ]
}

// 图表引用
const vocMapChartRef = ref(null)
const ap50ChartRef = ref(null)
const ap75ChartRef = ref(null)
const cocoMapChartRef = ref(null)
const classChartRefs = ref([])
let vocMapChart = null
let ap50Chart = null
let ap75Chart = null
let cocoMapChart = null
let classCharts = []

// 添加刷新整个页面的方法和定时器
const pageRefreshTimer = ref(null)

// 计算属性
const completedResults = computed(() => {
  if (!taskDetail.value || !taskDetail.value.results) return []
  return taskDetail.value.results
    .filter(result => result.status === 'completed')
    .sort((a, b) => a.epoch - b.epoch)
})

const latestResult = computed(() => {
  if (parsedResults.value.length === 0) return null
  return parsedResults.value[parsedResults.value.length - 1]
})

// 生命周期钩子
onMounted(() => {
  fetchTaskDetail()
  window.addEventListener('resize', handleResize)
  
  // 设置页面自动刷新（每30秒）
  pageRefreshTimer.value = setInterval(fetchTaskDetail, 30000)
})

// 在组件卸载时移除事件监听和清除定时器
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
  }
  if (pageRefreshTimer.value) {
    clearInterval(pageRefreshTimer.value)
  }
})

watch(completedResults, (newVal) => {
  if (newVal.length > 0) {
    parseResults()
  }
}, { deep: true })

watch(parsedResults, (newVal) => {
  if (newVal.length > 0) {
    nextTick(() => {
      initCharts()
    })
  }
}, { deep: true })

// 方法
const fetchTaskDetail = async () => {
  loading.value = true
  try {
    const response = await axios.get(`/api/training/${taskId.value}`)
    taskDetail.value = response.data
    
    // 确保进度输出字段是数组
    if (taskDetail.value && taskDetail.value.results) {
      taskDetail.value.results = taskDetail.value.results.map(result => {
        // 如果progress_output是字符串（JSON字符串），则解析它
        if (result.progress_output && typeof result.progress_output === 'string') {
          try {
            result.progress_output = JSON.parse(result.progress_output)
          } catch (e) {
            console.error('解析进度输出失败:', e)
            result.progress_output = []
          }
        } else if (!Array.isArray(result.progress_output)) {
          result.progress_output = []
        }
        return result
      })
    }
    
    if (taskDetail.value.results && taskDetail.value.results.length > 0) {
      parseResults()
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
  } finally {
    loading.value = false
  }
}

const getParsedMetric = (resultId, metricName) => {
  const result = parsedResults.value.find(r => r.result_id === resultId)
  if (!result) return '-'
  
  const value = result.metrics[metricName]
  return value ? value.toFixed(4) : '-'
}

const parseResults = () => {
  parsedResults.value = []
  
  completedResults.value.forEach(result => {
    const parsedResult = parseEvaluationResult(result.eval_result, result.epoch)
    if (parsedResult) {
      parsedResults.value.push({
        ...parsedResult,
        epoch: result.epoch,
        result_id: result.result_id,
        completed_at: result.completed_at
      })
    }
  })
  
  // 按epoch排序
  parsedResults.value.sort((a, b) => a.epoch - b.epoch)
}

const parseEvaluationResult = (resultText, epoch) => {
  if (!resultText) return null
  
  try {
    const result = {
      metrics: {
        mAP: 0,
        AP50: 0,
        AP75: 0,
        cocoMAP: 0
      },
      classAps: [],
      submissionInfo: {},
      epoch
    }
    
    // 查找COCO部分，将结果文本分为两部分：VOC和COCO
    const cocoSectionMatch = resultText.match(/<p>COCO style result:<\/p>\s*<ul>(.*?)<\/ul>/s)
    
    // 解析VOC mAP
    const vocMapMatch = resultText.match(/<li><b>mAP<\/b>:\s*([\d.]+)<\/li>/i)
    if (vocMapMatch) {
      result.metrics.mAP = parseFloat(vocMapMatch[1])
    }
    
    // 解析类别AP
    const classApMatch = resultText.match(/ap of each class.*?:(.*?)(?=<\/li>|\n)/is)
    if (classApMatch) {
      const classApText = classApMatch[1].trim()
      const classApPairs = classApText.split(',')
      
      classApPairs.forEach(pair => {
        const [className, apValue] = pair.trim().split(':')
        if (className && apValue) {
          result.classAps.push({
            class: className.trim(),
            ap: parseFloat(apValue)
          })
        }
      })
    }
    
    // 解析COCO指标
    if (cocoSectionMatch) {
      const cocoSection = cocoSectionMatch[1]
      
      const ap50Match = cocoSection.match(/<li><b>AP50<\/b>:\s*([\d.]+)<\/li>/i)
      const ap75Match = cocoSection.match(/<li><b>AP75<\/b>:\s*([\d.]+)<\/li>/i)
      const cocoMapMatch = cocoSection.match(/<li><b>mAP<\/b>:\s*([\d.]+)<\/li>/i)
      
      if (ap50Match) result.metrics.AP50 = parseFloat(ap50Match[1])
      if (ap75Match) result.metrics.AP75 = parseFloat(ap75Match[1])
      if (cocoMapMatch) result.metrics.cocoMAP = parseFloat(cocoMapMatch[1])
    }
    
    // 解析提交信息
    const submissionInfoSection = resultText.match(/The submitted information is.*?<\/ul>/is)
    if (submissionInfoSection) {
      const infoItems = submissionInfoSection[0].match(/<li>(.*?):(.*?)<\/li>/g)
      if (infoItems) {
        infoItems.forEach(item => {
          const match = item.match(/<li>(.*?):(.*?)<\/li>/)
          if (match) {
            const key = match[1].trim()
            const value = match[2].trim()
            result.submissionInfo[key] = value
          }
        })
      }
    }
    
    return result
  } catch (error) {
    console.error('解析评估结果失败:', error)
    return null
  }
}

const initCharts = () => {
  if (parsedResults.value.length === 0) return
  
  // 初始化四个独立的指标图表
  initVocMapChart()
  initAp50Chart()
  initAp75Chart()
  initCocoMapChart()
  
  // 初始化类别AP图表
  if (latestResult.value && latestResult.value.classAps.length > 0) {
    // 确保在DOM更新后调用
    nextTick(() => {
      initClassCharts()
    })
  }
}

const initVocMapChart = () => {
  if (!vocMapChartRef.value) return
  
  if (vocMapChart) {
    vocMapChart.dispose()
  }
  
  vocMapChart = echarts.init(vocMapChartRef.value)
  
  const epochs = parsedResults.value.map(r => r.epoch)
  const values = parsedResults.value.map(r => r.metrics.mAP)
  
  const option = createSingleMetricChartOption('VOC mAP', epochs, values)
  vocMapChart.setOption(option)
}

const initAp50Chart = () => {
  if (!ap50ChartRef.value) return
  
  if (ap50Chart) {
    ap50Chart.dispose()
  }
  
  ap50Chart = echarts.init(ap50ChartRef.value)
  
  const epochs = parsedResults.value.map(r => r.epoch)
  const values = parsedResults.value.map(r => r.metrics.AP50)
  
  const option = createSingleMetricChartOption('COCO AP50', epochs, values)
  ap50Chart.setOption(option)
}

const initAp75Chart = () => {
  if (!ap75ChartRef.value) return
  
  if (ap75Chart) {
    ap75Chart.dispose()
  }
  
  ap75Chart = echarts.init(ap75ChartRef.value)
  
  const epochs = parsedResults.value.map(r => r.epoch)
  const values = parsedResults.value.map(r => r.metrics.AP75)
  
  const option = createSingleMetricChartOption('COCO AP75', epochs, values)
  ap75Chart.setOption(option)
}

const initCocoMapChart = () => {
  if (!cocoMapChartRef.value) return
  
  if (cocoMapChart) {
    cocoMapChart.dispose()
  }
  
  cocoMapChart = echarts.init(cocoMapChartRef.value)
  
  const epochs = parsedResults.value.map(r => r.epoch)
  const values = parsedResults.value.map(r => r.metrics.cocoMAP)
  
  const option = createSingleMetricChartOption('COCO mAP', epochs, values)
  cocoMapChart.setOption(option)
}

const createSingleMetricChartOption = (title, epochs, values) => {
  return {
    title: {
      text: title,
      left: 'center',
      show: false // 隐藏标题，因为我们已经在外部添加了标题
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        return `Epoch ${params[0].axisValue}<br/>${title}: ${params[0].value.toFixed(4)}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      name: 'Epoch',
      data: epochs
    },
    yAxis: {
      type: 'value',
      name: '',
      min: 0,
      max: 1
    },
    series: [
      {
        name: title,
        type: 'line',
        data: values,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          width: 2
        },
        itemStyle: {
          color: '#5470c6'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0, color: 'rgba(84, 112, 198, 0.5)'
            }, {
              offset: 1, color: 'rgba(84, 112, 198, 0.1)'
            }]
          }
        }
      }
    ]
  }
}

const initClassCharts = () => {
  // 清除之前的图表
  classCharts.forEach(chart => chart && chart.dispose())
  classCharts = []
  
  if (!latestResult.value) return
  
  const classNames = latestResult.value.classAps.map(item => item.class)
  
  // 为每个类别创建一个图表
  classNames.forEach((className, index) => {
    if (!classChartRefs.value[index]) return
    
    const chart = echarts.init(classChartRefs.value[index])
    
    // 获取这个类别在不同epoch的AP值
    const epochs = parsedResults.value.map(r => r.epoch)
    const values = parsedResults.value.map(r => {
      const classAp = r.classAps.find(c => c.class === className)
      return classAp ? classAp.ap : 0
    })
    
    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          return `Epoch ${params[0].axisValue}<br/>${className}: ${params[0].value.toFixed(4)}`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        name: 'Epoch',
        data: epochs
      },
      yAxis: {
        type: 'value',
        name: '',
        min: 0,
        max: 1
      },
      series: [
        {
          name: className,
          type: 'line',
          data: values,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            width: 2
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0, color: 'rgba(128, 128, 255, 0.5)'
              }, {
                offset: 1, color: 'rgba(128, 128, 255, 0.1)'
              }]
            }
          }
        }
      ]
    }
    
    chart.setOption(option)
    classCharts.push(chart)
  })
}

const handleResize = () => {
  vocMapChart && vocMapChart.resize()
  ap50Chart && ap50Chart.resize()
  ap75Chart && ap75Chart.resize()
  cocoMapChart && cocoMapChart.resize()
  classCharts.forEach(chart => chart && chart.resize())
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

const getResultStatusType = (status) => {
  switch (status) {
    case 'pending': return 'info'
    case 'processing': return 'warning'
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'retrying': return 'warning'
    case 'error': return 'danger'
    default: return 'info'
  }
}

const getResultStatusText = (status) => {
  switch (status) {
    case 'pending': return '待处理'
    case 'processing': return '处理中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'retrying': return '重试中'
    case 'error': return '错误'
    default: return '未知'
  }
}

const showResultDetail = (result) => {
  // 如果任务仍在处理中，显示处理进度而不是结果
  if (['pending', 'processing', 'retrying'].includes(result.status)) {
    ElMessage.info('任务仍在处理中，显示处理进度')
    showProgressOutput(result)
    return
  }

  selectedResult.value = result
  selectedParsedResult.value = parsedResults.value.find(r => r.result_id === result.result_id)
  resultDialogVisible.value = true
}

const showProgressOutput = (result) => {
  progressDialogVisible.value = true
  currentResultId.value = result.result_id
  
  // 检查任务是否正在处理中
  isProcessing.value = ['pending', 'processing', 'retrying'].includes(result.status)
  
  if (result.progress_output && Array.isArray(result.progress_output)) {
    selectedProgressOutput.value = result.progress_output
  } else {
    // 如果需要从服务器获取最新进度，可以在这里发起请求
    fetchProgressOutput(result.result_id)
  }
  
  // 如果任务正在处理中，启动自动刷新
  if (isProcessing.value) {
    startAutoRefresh()
  }
}

const fetchProgressOutput = async (resultId) => {
  try {
    const response = await axios.get(`/api/training/result/${resultId}`)
    if (response.data) {
      if (response.data.progress_output) {
        // 处理可能的字符串形式
        if (typeof response.data.progress_output === 'string') {
          try {
            selectedProgressOutput.value = JSON.parse(response.data.progress_output)
          } catch (e) {
            console.error('解析进度输出失败:', e)
            selectedProgressOutput.value = []
          }
        } else if (Array.isArray(response.data.progress_output)) {
          selectedProgressOutput.value = response.data.progress_output
        } else {
          selectedProgressOutput.value = []
        }
      } else {
        selectedProgressOutput.value = []
      }
      
      // 更新任务状态
      isProcessing.value = ['pending', 'processing', 'retrying'].includes(response.data.status)
      
      // 如果任务已经完成，停止自动刷新
      if (!isProcessing.value && refreshTimer.value) {
        clearInterval(refreshTimer.value)
        refreshTimer.value = null
      }
      
      // 更新本地任务详情中的状态
      if (taskDetail.value && taskDetail.value.results) {
        const resultIndex = taskDetail.value.results.findIndex(r => r.result_id === resultId)
        if (resultIndex !== -1) {
          taskDetail.value.results[resultIndex].status = response.data.status
          taskDetail.value.results[resultIndex].progress_output = selectedProgressOutput.value
          if (response.data.eval_result) {
            taskDetail.value.results[resultIndex].eval_result = response.data.eval_result
          }
          if (response.data.status === 'completed' && response.data.eval_result) {
            parseResults() // 重新解析结果
            initCharts()   // 更新图表
          }
        }
      }
    }
  } catch (error) {
    console.error('获取处理进度失败:', error)
    ElMessage.error('获取处理进度失败')
    selectedProgressOutput.value = []
  }
}

const startAutoRefresh = () => {
  // 先清除可能存在的定时器
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
  }
  
  // 设置5秒自动刷新
  refreshTimer.value = setInterval(() => {
    if (currentResultId.value && isProcessing.value) {
      fetchProgressOutput(currentResultId.value)
    } else {
      // 如果不再处理或没有当前结果ID，停止刷新
      clearInterval(refreshTimer.value)
      refreshTimer.value = null
    }
  }, 5000)
}

// 监听对话框关闭事件，停止自动刷新
watch(progressDialogVisible, (isVisible) => {
  if (!isVisible && refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
    currentResultId.value = null
  }
})

const getProgressItemType = (type) => {
  switch (type) {
    case 'success':
      return 'success'
    case 'warning':
      return 'warning'
    case 'error':
      return 'danger'
    case 'info':
    default:
      return 'primary'
  }
}

const manualRefreshProgress = () => {
  if (currentResultId.value) {
    refreshing.value = true
    fetchProgressOutput(currentResultId.value).finally(() => {
      refreshing.value = false
    })
  }
}

const rerunEvaluation = async (result) => {
  try {
    rerunningResultId.value = result.result_id
    await axios.post(`/api/training/result/${result.result_id}/rerun`)
    ElMessage.success('已提交重新评测请求')
    fetchTaskDetail()
  } catch (error) {
    console.error('重新评测失败:', error)
    ElMessage.error(error.response?.data?.msg || '重新评测失败')
  } finally {
    rerunningResultId.value = null
  }
}

const deleteResult = async (result) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条评测结果吗？此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    deletingResultId.value = result.result_id
    await axios.delete(`/api/training/result/${result.result_id}`)
    ElMessage.success('删除成功')
    fetchTaskDetail()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.msg || '删除失败')
    }
  } finally {
    deletingResultId.value = null
  }
}

const handleSubmitEpoch = () => {
  submitDialogVisible.value = true
  submitForm.epoch = 1
  submitForm.eval_file = null
  hasUploadedFile.value = false
  
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
      
      await axios.post(`/api/training/${taskId.value}/epoch`, formData)
      ElMessage.success('提交训练结果成功')
      submitDialogVisible.value = false
      fetchTaskDetail()
    } catch (error) {
      console.error('提交训练结果失败:', error)
      ElMessage.error(error.response?.data?.msg || '提交训练结果失败')
    } finally {
      submitting.value = false
    }
  })
}

const exportToHtml = () => {
  if (!taskDetail.value) return
  
  const task = taskDetail.value
  const results = task.results || []
  const parsed = parsedResults.value
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString()
  }
  
  const getStatusText = (status) => {
    switch (status) {
      case 'pending': return '待处理'
      case 'processing': return '处理中'
      case 'completed': return '已完成'
      case 'failed': return '失败'
      case 'retrying': return '重试中'
      default: return status
    }
  }
  
  const getStatusType = (status) => {
    switch (status) {
      case 'pending': return 'info'
      case 'processing': return 'warning'
      case 'completed': return 'success'
      case 'failed': return 'danger'
      case 'retrying': return 'warning'
      default: return 'info'
    }
  }
  
  const rowsHtml = results.map((r, idx) => {
    const parsedResult = parsed.find(p => p.result_id === r.result_id)
    const classApHtml = parsedResult && parsedResult.classAps && parsedResult.classAps.length > 0 ? `
      <tr class="class-ap-row">
        <td colspan="10">
          <div class="result-detail" id="detail-${idx}" style="display: none;">
            <h4>Epoch ${r.epoch} 各类别AP值</h4>
            <table class="detail-table">
              <thead>
                <tr><th>类别</th><th>AP</th><th>可视化</th></tr>
              </thead>
              <tbody>
                ${parsedResult.classAps.map(c => `
                  <tr>
                    <td>${c.class}</td>
                    <td>${c.ap.toFixed(4)}</td>
                    <td><div class="ap-bar"><div class="ap-bar-fill" style="width: ${c.ap * 100}%"></div></div></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </td>
      </tr>
    ` : ''
    return `
      <tr>
        <td>${r.result_id}</td>
        <td>
          <button class="toggle-btn" onclick="toggleDetail(${idx})">${parsedResult && parsedResult.classAps && parsedResult.classAps.length > 0 ? '📋' : '-'}</button>
        </td>
        <td>${r.epoch}</td>
        <td><span class="status-${getStatusType(r.status)}">${getStatusText(r.status)}</span></td>
        <td>${r.status === 'completed' && parsedResult ? parsedResult.metrics.mAP.toFixed(4) : '-'}</td>
        <td>${r.status === 'completed' && parsedResult ? parsedResult.metrics.AP50.toFixed(4) : '-'}</td>
        <td>${r.status === 'completed' && parsedResult ? parsedResult.metrics.AP75.toFixed(4) : '-'}</td>
        <td>${r.status === 'completed' && parsedResult ? parsedResult.metrics.cocoMAP.toFixed(4) : '-'}</td>
        <td>${formatDate(r.submitted_at)}</td>
        <td>${formatDate(r.completed_at)}</td>
      </tr>
      ${classApHtml}
    `
  }).join('')
  
  const epochs = parsed.map(p => p.epoch)
  const vocMapData = parsed.map(p => p.metrics.mAP)
  const ap50Data = parsed.map(p => p.metrics.AP50)
  const ap75Data = parsed.map(p => p.metrics.AP75)
  const cocoMapData = parsed.map(p => p.metrics.cocoMAP)
  
  const chartImagesHtml = parsed.length > 0 ? `
    <div class="card">
      <h2>训练进度可视化</h2>
      <h3>评估指标趋势</h3>
      <div class="chart-row">
        <div class="chart-container">
          <h4>VOC mAP</h4>
          <div id="vocMapChart" style="width: 100%; height: 300px;"></div>
        </div>
        <div class="chart-container">
          <h4>COCO AP50</h4>
          <div id="ap50Chart" style="width: 100%; height: 300px;"></div>
        </div>
      </div>
      <div class="chart-row">
        <div class="chart-container">
          <h4>COCO AP75</h4>
          <div id="ap75Chart" style="width: 100%; height: 300px;"></div>
        </div>
        <div class="chart-container">
          <h4>COCO mAP</h4>
          <div id="cocoMapChart" style="width: 100%; height: 300px;"></div>
        </div>
      </div>
    </div>
  ` : ''
  
  const classApDataJson = JSON.stringify(parsed.map(p => p.classAps))
  
  const htmlContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>训练任务详情 - ${task.task_name}</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"><\/script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; padding: 20px; background: #f5f7fa; color: #333; }
    .container { max-width: 1200px; margin: 0 auto; }
    h1 { margin-bottom: 20px; color: #303133; }
    h2 { margin: 30px 0 15px; color: #303133; font-size: 18px; }
    h3 { margin: 20px 0 10px; color: #606266; font-size: 16px; }
    h4 { margin: 15px 0 10px; color: #606266; font-size: 14px; }
    .card { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .header h1 { margin-bottom: 0; }
    .status-tag { display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 14px; }
    .status-success { background: #f0f9eb; color: #67c23a; border: 1px solid #e1f3d8; }
    .status-warning { background: #fdf6ec; color: #e6a23c; border: 1px solid #faecd8; }
    .status-danger { background: #fef0f0; color: #f56c6c; border: 1px solid #fde2e2; }
    .status-info { background: #f4f4f5; color: #909399; border: 1px solid #e9e9eb; }
    table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ebeef5; }
    th { background: #f5f7fa; color: #606266; font-weight: 600; }
    tr:hover { background: #fafafa; }
    .descriptions { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
    .descriptions .item { padding: 10px; }
    .descriptions .label { color: #909399; font-size: 14px; margin-bottom: 5px; }
    .descriptions .value { color: #303133; font-size: 14px; }
    .chart-row { display: flex; flex-wrap: wrap; gap: 20px; margin: 15px 0; }
    .chart-container { flex: 1; min-width: 300px; }
    .view-class-btn { background: #409eff; color: #fff; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 14px; margin-top: 10px; }
    .view-class-btn:hover { background: #66b1ff; }
    .dialog-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; justify-content: center; align-items: center; }
    .dialog-content { background: #fff; border-radius: 8px; width: 90%; max-width: 1200px; max-height: 90vh; overflow: auto; }
    .dialog-header { display: flex; justify-content: space-between; align-items: center; padding: 20px; border-bottom: 1px solid #ebeef5; }
    .dialog-header h3 { margin: 0; }
    .close-btn { background: none; border: none; font-size: 24px; cursor: pointer; color: #909399; }
    .dialog-body { padding: 20px; }
    .class-charts-row { display: flex; flex-wrap: wrap; gap: 20px; }
    .toggle-btn { background: #409eff; color: #fff; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px; }
    .toggle-btn:hover { background: #66b1ff; }
    .class-ap-row { background: #f9f9f9; }
    .result-detail { padding: 15px; }
    .result-detail h4 { margin: 0 0 10px; color: #409eff; }
    .detail-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .detail-table th, .detail-table td { padding: 8px; text-align: left; border-bottom: 1px solid #ebeef5; }
    .detail-table th { background: #f5f7fa; color: #606266; }
    .ap-bar { width: 100px; height: 16px; background: #e4e7ed; border-radius: 3px; overflow: hidden; }
    .ap-bar-fill { height: 100%; background: #409eff; }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <div class="header">
        <h1>训练任务详情</h1>
        <span class="status-tag status-${getStatusType(task.status)}">${getStatusText(task.status)}</span>
      </div>
      
      <h2>基本信息</h2>
      <div class="descriptions">
        <div class="item">
          <div class="label">任务ID</div>
          <div class="value">${task.task_id}</div>
        </div>
        <div class="item">
          <div class="label">任务名称</div>
          <div class="value">${task.task_name}</div>
        </div>
        <div class="item">
          <div class="label">创建时间</div>
          <div class="value">${formatDate(task.created_at)}</div>
        </div>
        <div class="item">
          <div class="label">服务器</div>
          <div class="value">${task.server_name}</div>
        </div>
        ${task.api_key_id ? `
        <div class="item">
          <div class="label">API密钥ID</div>
          <div class="value">${task.api_key_id}</div>
        </div>
        ` : ''}
        <div class="item" style="grid-column: span 2;">
          <div class="label">描述</div>
          <div class="value">${task.description || '无'}</div>
        </div>
      </div>
    </div>
    
    <div class="card">
      <h2>训练结果列表</h2>
      <table>
        <thead>
          <tr>
            <th></th>
            <th>ID</th>
            <th>Epoch</th>
            <th>状态</th>
            <th>VOC mAP</th>
            <th>COCO AP50</th>
            <th>COCO AP75</th>
            <th>COCO mAP</th>
            <th>提交时间</th>
            <th>完成时间</th>
          </tr>
        </thead>
        <tbody>
          ${rowsHtml}
        </tbody>
      </table>
    </div>
    
    ${chartImagesHtml}
    
  </div>
  
  <script>
    const epochs = ${JSON.stringify(epochs)};
    const vocMapData = ${JSON.stringify(vocMapData)};
    const ap50Data = ${JSON.stringify(ap50Data)};
    const ap75Data = ${JSON.stringify(ap75Data)};
    const cocoMapData = ${JSON.stringify(cocoMapData)};
    const classApData = ${classApDataJson};
    
    function createLineChart(chartId, title, xData, yData) {
      const chart = echarts.init(document.getElementById(chartId));
      const option = {
        title: { text: title, left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: xData },
        yAxis: { type: 'value' },
        series: [{
          data: yData,
          type: 'line',
          smooth: true,
          areaStyle: { opacity: 0.3 }
        }]
      };
      chart.setOption(option);
      return chart;
    }
    
    function toggleDetail(idx) {
      const detail = document.getElementById('detail-' + idx);
      if (detail.style.display === 'none') {
        detail.style.display = 'block';
      } else {
        detail.style.display = 'none';
      }
    }
    
    window.addEventListener('load', function() {
      if (document.getElementById('vocMapChart')) {
        createLineChart('vocMapChart', 'VOC mAP', epochs, vocMapData);
      }
      if (document.getElementById('ap50Chart')) {
        createLineChart('ap50Chart', 'COCO AP50', epochs, ap50Data);
      }
      if (document.getElementById('ap75Chart')) {
        createLineChart('ap75Chart', 'COCO AP75', epochs, ap75Data);
      }
      if (document.getElementById('cocoMapChart')) {
        createLineChart('cocoMapChart', 'COCO mAP', epochs, cocoMapData);
      }
    });
    
    window.addEventListener('resize', function() {
      const charts = document.querySelectorAll('[id^="vocMapChart"], [id^="ap50Chart"], [id^="ap75Chart"], [id^="cocoMapChart"], [id^="classChart"]');
      charts.forEach(el => {
        const chart = echarts.getInstanceByDom(el);
        if (chart) chart.resize();
      });
    });
  <\/script>
</body>
</html>`
  
  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `训练任务详情_${task.task_name}_${new Date().toISOString().slice(0,10)}.html`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(link.href)
  
  ElMessage.success('导出成功')
}

const goBack = () => {
  router.push('/training')
}
</script>

<style scoped>
.training-detail-container {
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

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-info {
  margin-bottom: 30px;
}

.section-title {
  margin: 20px 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.subsection-title {
  margin: 20px 0 10px 0;
  padding-bottom: 5px;
  border-bottom: 1px dashed #ebeef5;
}

.chart-title {
  text-align: center;
  margin-bottom: 5px;
  font-weight: bold;
}

.results-section {
  margin-top: 30px;
}

.chart-container {
  margin-bottom: 20px;
}

.chart-row {
  margin-top: 20px;
}

.chart {
  height: 300px;
  width: 100%;
}

.class-chart {
  height: 250px;
}

.class-charts-container {
  margin-top: 20px;
}

.metric-card {
  margin-bottom: 20px;
  height: 100%;
}

.metric-header {
  font-weight: bold;
}

.metric-content {
  padding: 10px 0;
}

.metric-item {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.metric-label {
  font-weight: bold;
  margin-right: 10px;
  width: 80px;
}

.metric-value {
  font-size: 18px;
  color: #409EFF;
}

.ap-bar-container {
  width: 100%;
  height: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
  position: relative;
}

.ap-bar {
  height: 100%;
  background-color: #409EFF;
  border-radius: 4px;
}

.ap-value {
  position: absolute;
  right: 10px;
  top: 0;
  line-height: 20px;
  color: #333;
  font-size: 12px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 14px;
  margin: 0;
  padding: 8px;
  background-color: #f8f8f8;
  border-radius: 4px;
}

.result-detail-text {
  max-height: 60vh;
  overflow-y: auto;
}

/* 处理进度样式 */
.progress-message {
  padding: 8px 12px;
  border-radius: 4px;
  background-color: #f8f9fa;
  font-family: 'Courier New', monospace;
}

.progress-info {
  color: #606266;
}

.progress-success {
  color: #67c23a;
  font-weight: bold;
}

.progress-warning {
  color: #e6a23c;
}

.progress-error {
  color: #f56c6c;
  font-weight: bold;
}

.empty-progress {
  padding: 30px;
  text-align: center;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.processing-tag {
  background-color: #e6a23c;
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
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
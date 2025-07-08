<template>
  <div class="training-detail-container">
    <el-card class="box-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button @click="goBack" icon="ArrowLeft">返回</el-button>
            <h3>训练任务详情</h3>
          </div>
          <div v-if="taskDetail">
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
import { ElMessage } from 'element-plus'
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
</style> 
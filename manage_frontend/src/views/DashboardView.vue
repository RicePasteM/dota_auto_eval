<template>
  <div class="dashboard-container">
    <!-- 系统概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="4" :xs="12" :sm="8" :md="6" :lg="4" v-for="(stat, index) in overviewStats" :key="index">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 评估趋势和分布 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16" :xs="24" :sm="24" :md="16" class="chart-col">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>评估趋势(最近7天)</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="evalTrendOption" autoresize />
          </div>
        </el-card>
      </el-col>
      <el-col :span="8" :xs="24" :sm="24" :md="8" class="chart-col">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>服务器评估分布</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="evalDistributionOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 服务器状态和活跃用户 -->
    <el-row :gutter="20" class="data-row">
      <el-col :span="12">
        <el-card class="data-card">
          <template #header>
            <div class="card-header">
              <span>服务器状态</span>
              <el-button type="primary" link @click="refreshServerStats">
                刷新
              </el-button>
            </div>
          </template>
          <el-table :data="serverStats" style="width: 100%" size="small">
            <el-table-column prop="server_name" label="服务器" />
            <el-table-column prop="total_limit" label="总限制" width="100" />
            <el-table-column prop="used_count" label="已使用" width="100" />
            <el-table-column prop="remaining" label="剩余" width="100">
              <template #default="{ row }">
                <el-tag :type="getRemainningTagType(row.remaining)">
                  {{ row.remaining }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="data-card">
          <template #header>
            <div class="card-header">
              <span>最活跃用户</span>
            </div>
          </template>
          <el-table :data="activeUsers" style="width: 100%" size="small">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="server_name" label="服务器" />
            <el-table-column prop="eval_count" label="评估次数" width="100">
              <template #default="{ row }">
                <el-tag type="success">{{ row.eval_count }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近评估和API使用情况 -->
    <el-row :gutter="20" class="data-row">
      <el-col :span="14">
        <el-card class="data-card">
          <template #header>
            <div class="card-header">
              <span>最近评估记录</span>
            </div>
          </template>
          <el-table :data="recentEvals" style="width: 100%" size="small">
            <el-table-column prop="create_time" label="时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.create_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="server_name" label="服务器" width="120" />
            <el-table-column prop="username" label="用户" width="120" />
            <el-table-column prop="eval_result" label="结果">
              <template #default="{ row }">
                <el-tag :type="getResultTagType(row.eval_result)">
                  {{ getResultText(row.eval_result) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card class="data-card">
          <template #header>
            <div class="card-header">
              <span>API使用情况</span>
            </div>
          </template>
          <div class="api-stats">
            <div class="api-stat-item">
              <div class="stat-label">API Key总数</div>
              <div class="stat-value">{{ apiStats.total_keys }}</div>
            </div>
            <div class="api-stat-item">
              <div class="stat-label">活跃Key数</div>
              <div class="stat-value">{{ apiStats.active_keys }}</div>
            </div>
          </div>
          <div class="api-recent-logs">
            <div class="section-title">最近API调用</div>
            <el-timeline>
              <el-timeline-item
                v-for="log in apiStats.recent_logs"
                :key="log.log_id"
                :timestamp="formatDate(log.create_time)"
                :type="getTimelineItemType(log.eval_result)"
              >
                {{ getResultText(log.eval_result) }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 统计卡片部分 -->
    <el-row :gutter="20" class="stat-cards-row">
      <el-col :span="4" :xs="12" :sm="8" :md="6" :lg="4" class="stat-col">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-card-value">{{ overview.server_count }}</div>
            <div class="stat-card-title">服务器总数</div>
          </div>
          <div class="stat-card-icon">
            <el-icon><Connection /></el-icon>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4" :xs="12" :sm="8" :md="6" :lg="4" class="stat-col">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-card-value">{{ overview.user_count }}</div>
            <div class="stat-card-title">用户总数</div>
          </div>
          <div class="stat-card-icon">
            <el-icon><User /></el-icon>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4" :xs="12" :sm="8" :md="6" :lg="4" class="stat-col">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-card-value">{{ overview.email_count }}</div>
            <div class="stat-card-title">邮箱总数</div>
          </div>
          <div class="stat-card-icon">
            <el-icon><Message /></el-icon>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4" :xs="12" :sm="8" :md="6" :lg="4" class="stat-col">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-card-value">{{ overview.today_eval_count }}</div>
            <div class="stat-card-title">今日评估次数</div>
          </div>
          <div class="stat-card-icon">
            <el-icon><DataAnalysis /></el-icon>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="4" :xs="12" :sm="8" :md="6" :lg="4" class="stat-col">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-card-value">{{ trainingStats.total || 0 }}</div>
            <div class="stat-card-title">训练任务总数</div>
          </div>
          <div class="stat-card-icon">
            <el-icon><List /></el-icon>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="4" :xs="12" :sm="8" :md="6" :lg="4" class="stat-col">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-content">
            <div class="stat-card-value">{{ trainingStats.active || 0 }}</div>
            <div class="stat-card-title">活跃训练任务</div>
          </div>
          <div class="stat-card-icon">
            <el-icon><Loading /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { 
  Connection, 
  User, 
  Message, 
  DataAnalysis, 
  List, 
  Loading 
} from '@element-plus/icons-vue'

// 注册必需的 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
])

// 数据响应式定义
const overviewStats = ref([])
const evalTrendOption = ref({
  title: {
    text: '评估趋势(最近7天)',
    left: 'center',
    textStyle: {
      fontSize: 16
    }
  },
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: []
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '评估次数',
      type: 'line',
      smooth: true,
      data: []
    }
  ]
})

const evalDistributionOption = ref({
  title: {
    text: '服务器评估分布',
    left: 'center',
    textStyle: {
      fontSize: 16
    }
  },
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  graphic: {
    type: 'text',
    left: 'center',
    top: 'middle',
    style: {
      text: '加载中...',
      fontSize: 16,
      fill: '#999'
    }
  }
})

const serverStats = ref([])
const activeUsers = ref([])
const recentEvals = ref([])
const apiStats = ref({
  total_keys: 0,
  active_keys: 0,
  recent_logs: []
})

const overview = ref({
  server_count: 0,
  user_count: 0,
  email_count: 0,
  today_eval_count: 0
})

const evalTrend = ref({})
const serverDistribution = ref([])
const serverRemaining = ref([])
const apiUsage = ref({})
const trainingStats = ref({
  total: 0,
  active: 0,
  completed: 0
})

// 获取系统概览数据
const fetchOverviewStats = async () => {
  try {
    const response = await axios.get('/api/stats/overview')
    overview.value = response.data
    overviewStats.value = [
      { label: '服务器数量', value: response.data.server_count },
      { label: '用户数量', value: response.data.user_count },
      { label: '邮箱数量', value: response.data.email_count },
      { label: '活跃API Key', value: response.data.active_api_key_count },
      { label: '今日评估', value: response.data.today_eval_count }
    ]
  } catch (error) {
    console.error('Error fetching overview stats:', error)
    ElMessage.error('获取概览统计数据失败')
  }
}

// 更新趋势图
const updateEvalTrendChart = () => {
  if (!evalTrend.value || !evalTrend.value.dates) return
  
  evalTrendOption.value = {
    title: {
      text: '评估趋势(最近7天)',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: evalTrend.value.dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '评估次数',
        type: 'line',
        smooth: true,
        data: evalTrend.value.counts
      }
    ]
  }
}

// 更新分布图
const updateDistributionChart = () => {
  if (!serverDistribution.value) return
  
  const pieData = []
  for (const key in serverDistribution.value) {
    if (serverDistribution.value[key] > 0) {
      pieData.push({
        name: key,
        value: serverDistribution.value[key]
      })
    }
  }
  
  // 如果没有数据，显示空状态
  if (pieData.length === 0) {
    evalDistributionOption.value = {
      title: {
        text: '服务器分布',
        left: 'center'
      },
      graphic: {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: '暂无数据',
          fontSize: 16,
          fill: '#999'
        }
      }
    }
    return
  }
  
  evalDistributionOption.value = {
    title: {
      text: '服务器评估分布',
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      bottom: 10,
      data: Object.keys(serverDistribution.value).filter(key => serverDistribution.value[key] > 0)
    },
    series: [
      {
        name: '服务器评估',
        type: 'pie',
        radius: ['35%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 1
        },
        label: {
          show: true,
          formatter: '{b}: {c}'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: pieData
      }
    ]
  }
}

// 获取评估趋势数据
const fetchEvalTrend = async () => {
  try {
    // 设置加载中状态
    evalTrendOption.value = {
      ...evalTrendOption.value,
      graphic: {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: '数据加载中...',
          fontSize: 16,
          fill: '#999'
        }
      }
    };
    
    const response = await axios.get('/api/stats/eval_trend')
    // 转换数据格式
    const trendData = response.data
    const dates = Object.keys(trendData).sort()
    const counts = dates.map(date => trendData[date])
    
    evalTrend.value = {
      dates,
      counts
    }
    
    // 如果没有数据，显示空状态
    if (dates.length === 0) {
      evalTrendOption.value = {
        title: {
          text: '评估趋势(最近7天)',
          left: 'center',
          textStyle: {
            fontSize: 16
          }
        },
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: '暂无评估数据',
            fontSize: 16,
            fill: '#999'
          }
        }
      }
    } else {
      updateEvalTrendChart()
    }
  } catch (error) {
    console.error('Error fetching evaluation trend:', error)
    ElMessage.error('获取评估趋势数据失败')
    
    // 显示错误状态
    evalTrendOption.value = {
      title: {
        text: '评估趋势(最近7天)',
        left: 'center',
        textStyle: {
          fontSize: 16
        }
      },
      graphic: {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: '数据加载失败',
          fontSize: 16,
          fill: '#f56c6c'
        }
      }
    }
  }
}

// 获取服务器评估分布数据
const fetchServerDistribution = async () => {
  try {
    // 设置加载中状态
    evalDistributionOption.value = {
      ...evalDistributionOption.value,
      graphic: {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: '数据加载中...',
          fontSize: 16,
          fill: '#999'
        }
      }
    };
    
    const response = await axios.get('/api/stats/server_eval_distribution')
    
    // 确保响应数据格式正确
    if (response.data && typeof response.data === 'object') {
      serverDistribution.value = response.data
      
      // 确保至少有一个数据不为零
      const hasData = Object.values(response.data).some(value => value > 0)
      if (!hasData) {
        console.warn('Server distribution data is all zeros or empty')
        // 显示空数据状态
        evalDistributionOption.value = {
          title: {
            text: '服务器评估分布',
            left: 'center',
            textStyle: {
              fontSize: 16
            }
          },
          graphic: {
            type: 'text',
            left: 'center',
            top: 'middle',
            style: {
              text: '暂无评估数据',
              fontSize: 16,
              fill: '#999'
            }
          }
        }
      } else {
        updateDistributionChart()
      }
    } else {
      console.error('Invalid server distribution data format:', response.data)
      serverDistribution.value = {}
      // 显示格式错误状态
      evalDistributionOption.value = {
        title: {
          text: '服务器评估分布',
          left: 'center',
          textStyle: {
            fontSize: 16
          }
        },
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: '数据格式错误',
            fontSize: 16,
            fill: '#f56c6c'
          }
        }
      }
    }
  } catch (error) {
    console.error('Error fetching server distribution:', error)
    ElMessage.error('获取服务器评估分布数据失败')
    // 设置错误状态
    evalDistributionOption.value = {
      title: {
        text: '服务器评估分布',
        left: 'center',
        textStyle: {
          fontSize: 16
        }
      },
      graphic: {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: '数据加载失败',
          fontSize: 16,
          fill: '#f56c6c'
        }
      }
    }
  }
}

// 获取服务器剩余评估次数
const fetchServerRemaining = async () => {
  try {
    const response = await axios.get('/api/stats/server_remaining')
    serverRemaining.value = response.data
  } catch (error) {
    console.error('Error fetching server remaining:', error)
    ElMessage.error('获取服务器剩余次数数据失败')
  }
}

// 获取服务器状态
const fetchServerStats = async () => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(`${window.BASE_URL}/api/stats/server_remaining`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取服务器状态失败')
    
    serverStats.value = data
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 获取活跃用户
const fetchActiveUsers = async () => {
  try {
    const response = await axios.get('/api/stats/active_users')
    activeUsers.value = response.data
  } catch (error) {
    console.error('Error fetching active users:', error)
    ElMessage.error('获取活跃用户数据失败')
  }
}

// 获取最近评估记录
const fetchRecentEvals = async () => {
  try {
    const response = await axios.get('/api/stats/recent_evals')
    recentEvals.value = response.data
  } catch (error) {
    console.error('Error fetching recent evaluations:', error)
    ElMessage.error('获取最近评估数据失败')
  }
}

// 获取API使用情况
const fetchApiUsage = async () => {
  try {
    const response = await axios.get('/api/stats/api_usage')
    apiUsage.value = response.data
  } catch (error) {
    console.error('Error fetching API usage:', error)
    ElMessage.error('获取API使用情况数据失败')
  }
}

// 获取训练任务统计数据
const fetchTrainingStats = async () => {
  try {
    const response = await axios.get('/api/training', {
      params: { per_page: 1, page: 1 }
    })
    trainingStats.value.total = response.data.total || 0
    
    // 获取活跃任务数量
    const activeResponse = await axios.get('/api/training', {
      params: { status: 'active', per_page: 1, page: 1 }
    })
    trainingStats.value.active = activeResponse.data.total || 0
    
    // 获取完成任务数量
    const completedResponse = await axios.get('/api/training', {
      params: { status: 'completed', per_page: 1, page: 1 }
    })
    trainingStats.value.completed = completedResponse.data.total || 0
  } catch (error) {
    console.error('Error fetching training stats:', error)
  }
}

// 刷新服务器状态
const refreshServerStats = () => {
  fetchServerStats()
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取剩余次数标签类型
const getRemainningTagType = (remaining) => {
  if (remaining <= 0) return 'danger'
  if (remaining < 10) return 'warning'
  return 'success'
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

// 获取时间线项目类型
const getTimelineItemType = (result) => {
  if (!result) return 'info'
  if (result.includes('失败') || result.includes('异常') || result.includes('超时')) {
    return 'danger'
  }
  return 'success'
}

// 添加 watch 以确保数据变化时图表更新
watch(() => evalTrend.value, updateEvalTrendChart, { deep: true })
watch(() => serverDistribution.value, updateDistributionChart, { deep: true })

// 页面加载时获取所有数据
onMounted(() => {
  fetchOverviewStats()
  fetchEvalTrend()
  fetchServerDistribution()
  fetchServerRemaining()
  fetchServerStats()
  fetchActiveUsers()
  fetchRecentEvals()
  fetchApiUsage()
  fetchTrainingStats()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.stats-row {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  height: 100%;
  margin-bottom: 20px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 10px;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.chart-row {
  margin-top: 20px;
  margin-bottom: 20px;
}

.chart-col {
  margin-bottom: 20px;
}

.data-row {
  margin-top: 20px;
  margin-bottom: 20px;
}

.chart-card,
.data-card {
  height: 100%;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 350px;
  width: 100%;
  position: relative;
  min-height: 300px;
}

.chart {
  height: 100%;
  width: 100%;
}

.api-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
  padding: 10px 0;
  border-bottom: 1px solid #EBEEF5;
}

.api-stat-item {
  text-align: center;
}

.api-stat-item .stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.api-stat-item .stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.api-recent-logs {
  padding: 10px;
}

.section-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
  font-weight: bold;
}

:deep(.el-timeline-item__content) {
  color: #606266;
}

:deep(.el-timeline-item__timestamp) {
  font-size: 12px;
}

.stat-cards-row {
  margin-top: 20px;
}

.stat-col {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  height: 100%;
}

.stat-card-content {
  margin-bottom: 10px;
}

.stat-card-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-card-title {
  color: #606266;
  font-size: 14px;
}

.stat-card-icon {
  font-size: 24px;
}

@media (max-width: 992px) {
  .chart-container {
    height: 300px;
  }
}

@media (max-width: 768px) {
  .chart-container {
    height: 250px;
  }
}
</style>
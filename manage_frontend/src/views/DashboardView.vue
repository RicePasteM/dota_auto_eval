<template>
  <div class="dashboard-container">
    <!-- 系统概览 -->
    <el-row :gutter="20">
      <el-col :span="4" v-for="(stat, index) in overviewStats" :key="index">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 评估趋势和分布 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
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
      <el-col :span="8">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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
const evalTrendOption = ref({})
const evalDistributionOption = ref({})
const serverStats = ref([])
const activeUsers = ref([])
const recentEvals = ref([])
const apiStats = ref({
  total_keys: 0,
  active_keys: 0,
  recent_logs: []
})

// 获取系统概览数据
const fetchOverviewStats = async () => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(`${window.BASE_URL}/api/stats/overview`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取概览数据失败')
    
    overviewStats.value = [
      { label: '服务器数量', value: data.server_count },
      { label: '用户数量', value: data.user_count },
      { label: '邮箱数量', value: data.email_count },
      { label: '活跃API Key', value: data.active_api_key_count },
      { label: '今日评估', value: data.today_eval_count }
    ]
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 获取评估趋势数据
const fetchEvalTrend = async () => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(`${window.BASE_URL}/api/stats/eval_trend`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取趋势数据失败')
    
    const dates = Object.keys(data).sort()
    const values = dates.map(date => data[date])
    
    evalTrendOption.value = {
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: {
          formatter: (value) => value.slice(5) // 只显示月-日
        }
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: values,
        type: 'line',
        smooth: true,
        areaStyle: {
          opacity: 0.3
        },
        lineStyle: {
          width: 2
        }
      }]
    }
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 获取服务器评估分布
const fetchEvalDistribution = async () => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(`${window.BASE_URL}/api/stats/server_eval_distribution`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取分布数据失败')
    
    evalDistributionOption.value = {
      tooltip: {
        trigger: 'item'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [{
        type: 'pie',
        radius: '50%',
        data: data.map(item => ({
          name: item.server_name,
          value: item.eval_count
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
  } catch (error) {
    ElMessage.error(error.message)
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
    const token = localStorage.getItem('accessToken')
    const response = await fetch(`${window.BASE_URL}/api/stats/active_users`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取活跃用户失败')
    
    activeUsers.value = data
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 获取最近评估记录
const fetchRecentEvals = async () => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(`${window.BASE_URL}/api/stats/recent_evals`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取最近评估记录失败')
    
    recentEvals.value = data
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 获取API使用情况
const fetchApiUsage = async () => {
  try {
    const token = localStorage.getItem('accessToken')
    const response = await fetch(`${window.BASE_URL}/api/stats/api_usage`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.msg || '获取API使用情况失败')
    
    apiStats.value = data
  } catch (error) {
    ElMessage.error(error.message)
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

// 页面加载时获取所有数据
onMounted(() => {
  fetchOverviewStats()
  fetchEvalTrend()
  fetchEvalDistribution()
  fetchServerStats()
  fetchActiveUsers()
  fetchRecentEvals()
  fetchApiUsage()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
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
}

.data-row {
  margin-top: 20px;
}

.chart-card,
.data-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
}

.chart {
  height: 100%;
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
</style>
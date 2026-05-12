<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card-wrap">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #8B2500, #A9442A);">
              <el-icon :size="28"><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.heritage_count }}</div>
              <div class="stat-label">非遗项目</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card-wrap">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #2D5F4A, #3D8B6A);">
              <el-icon :size="28"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.news_count }}</div>
              <div class="stat-label">新闻资讯</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card-wrap">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #C5963A, #D4AD5E);">
              <el-icon :size="28"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.user_count }}</div>
              <div class="stat-label">注册用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card-wrap">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #2B3A67, #3D5A99);">
              <el-icon :size="28"><ChatDotRound /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.post_count }}</div>
              <div class="stat-label">论坛帖子</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card-wrap">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #6B4C9A, #8B6CB0);">
              <el-icon :size="28"><Picture /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.creation_count }}</div>
              <div class="stat-label">用户创作</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card-wrap">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #D4543A, #E87B64);">
              <el-icon :size="28"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.pending_report_count }}</div>
              <div class="stat-label">待处理举报</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card-wrap">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #3A7D6E, #5AAE9E);">
              <el-icon :size="28"><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.today_user_count }}</div>
              <div class="stat-label">今日新增用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card-wrap">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #7A6B4E, #9E8D6B);">
              <el-icon :size="28"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.week_post_count }}</div>
              <div class="stat-label">本周新帖</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card class="action-card">
          <template #header>
            <div class="card-title">快捷操作</div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/heritage')">
              <el-icon><Collection /></el-icon>非遗管理
            </el-button>
            <el-button color="#2D5F4A" @click="$router.push('/news')">
              <el-icon><Document /></el-icon>资讯管理
            </el-button>
            <el-button color="#C5963A" @click="$router.push('/forum/reports')">
              <el-icon><Warning /></el-icon>处理举报
            </el-button>
            <el-button color="#2B3A67" @click="$router.push('/users')">
              <el-icon><User /></el-icon>用户管理
            </el-button>
            <el-button color="#6B4C9A" @click="$router.push('/creations')">
              <el-icon><Picture /></el-icon>创作管理
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="action-card">
          <template #header>
            <div class="card-title">最近操作</div>
          </template>
          <el-scrollbar class="operation-logs" v-loading="logsLoading">
            <div v-if="operationLogs.length === 0" class="no-logs">暂无操作记录</div>
            <div v-for="log in operationLogs" :key="log.id" class="log-item">
              <div class="log-action">
                <el-tag :type="getActionTagType(log.action)" size="small" effect="dark">
                  {{ log.action_display || log.action }}
                </el-tag>
                <span class="log-resource">{{ log.resource_type }}</span>
                <span class="log-name" v-if="log.resource_name">{{ log.resource_name }}</span>
              </div>
              <div class="log-meta">
                <span class="log-user">{{ log.user }}</span>
                <span class="log-time">{{ formatTime(log.created_at) }}</span>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import adminApi from '@/api/admin'

const stats = ref({
  heritage_count: 0,
  news_count: 0,
  user_count: 0,
  post_count: 0,
  creation_count: 0,
  pending_report_count: 0,
  today_user_count: 0,
  week_post_count: 0,
})

const operationLogs = ref([])
const logsLoading = ref(false)

const getActionTagType = (action) => {
  const map = {
    create: 'success',
    update: 'warning',
    delete: 'danger',
    login: 'info',
    logout: 'info',
  }
  return map[action] || 'info'
}

const formatTime = (isoStr) => {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(async () => {
  try {
    const statsData = await adminApi.getStats()
    stats.value = { ...stats.value, ...statsData }
  } catch {
    // ignore
  }

  logsLoading.value = true
  try {
    const logsData = await adminApi.getOperationLogs({ page: 1, page_size: 10 })
    operationLogs.value = logsData.results || []
  } catch {
    // ignore
  } finally {
    logsLoading.value = false
  }
})
</script>

<style scoped>
.stat-card-wrap {
  border: none;
  border-radius: 12px;
  overflow: hidden;
}

.stat-card-wrap :deep(.el-card__body) {
  padding: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
}

.stat-label {
  font-size: 14px;
  color: #8B9BB4;
  margin-top: 4px;
}

.action-card {
  border-radius: 12px;
  border: none;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  letter-spacing: 1px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-actions .el-button {
  border-radius: 8px;
}

.operation-logs {
  max-height: 320px;
  overflow-y: auto;
}

.no-logs {
  text-align: center;
  color: #8B9BB4;
  padding: 40px 0;
}

.log-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.log-item:last-child {
  border-bottom: none;
}

.log-action {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.log-resource {
  color: #606266;
  font-size: 13px;
  flex-shrink: 0;
}

.log-name {
  color: #303133;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-left: 12px;
}

.log-user {
  color: #909399;
  font-size: 12px;
}

.log-time {
  color: #C0C4CC;
  font-size: 12px;
}
</style>

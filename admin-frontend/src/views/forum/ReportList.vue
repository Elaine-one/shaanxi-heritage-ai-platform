<template>
  <div class="report-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>举报管理</span>
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 120px" @change="loadData">
            <el-option label="待处理" value="pending" />
            <el-option label="已处理" value="resolved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="举报人" width="120">
          <template #default="{ row }">{{ row.reporter_name || row.reporter_id || '-' }}</template>
        </el-table-column>
        <el-table-column label="举报目标" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.post_title">帖子: {{ row.post_title }}</span>
            <span v-else-if="row.post_id">帖子 #{{ row.post_id }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" width="120" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="reportStatusMap[row.status]?.type || 'info'" size="small">
              {{ reportStatusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="success" link size="small" @click="handleReport(row, 'resolved')">通过</el-button>
              <el-button type="danger" link size="small" @click="handleReport(row, 'rejected')">驳回</el-button>
            </template>
            <span v-else class="handled-text">已处理</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="noteDialogVisible" title="处理举报" width="480px">
      <el-form :model="noteForm" label-width="80px">
        <el-form-item label="处理结果">
          <el-tag :type="noteForm.status === 'resolved' ? 'success' : 'danger'">
            {{ noteForm.status === 'resolved' ? '通过' : '驳回' }}
          </el-tag>
        </el-form-item>
        <el-form-item label="处理备注">
          <el-input v-model="noteForm.handler_note" type="textarea" :rows="3" placeholder="可选填写处理备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="noteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitHandle" :loading="submitting">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import adminApi from '@/api/admin'
import { ElMessage } from 'element-plus'

const reportStatusMap = {
  pending: { label: '待处理', type: 'warning' },
  resolved: { label: '已处理', type: 'success' },
  rejected: { label: '已驳回', type: 'info' }
}

const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const statusFilter = ref('')
const noteDialogVisible = ref(false)
const noteForm = ref({ id: null, status: '', handler_note: '' })

async function loadData() {
  loading.value = true
  try {
    const params = {}
    if (statusFilter.value) params.status = statusFilter.value
    const data = await adminApi.getReports(params)
    tableData.value = Array.isArray(data) ? data : data.results || []
  } finally {
    loading.value = false
  }
}

function handleReport(row, status) {
  noteForm.value = { id: row.id, status, handler_note: '' }
  noteDialogVisible.value = true
}

async function submitHandle() {
  submitting.value = true
  try {
    await adminApi.handleReport(noteForm.value.id, {
      status: noteForm.value.status,
      handler_note: noteForm.value.handler_note
    })
    ElMessage.success('处理成功')
    noteDialogVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.handled-text { color: #909399; font-size: 12px; }
</style>

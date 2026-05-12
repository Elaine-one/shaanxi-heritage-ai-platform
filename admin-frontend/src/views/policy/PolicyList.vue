<template>
  <div class="policy-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>政策法规管理</span>
          <el-button type="primary" @click="$router.push('/policy/create')">
            <el-icon><Plus /></el-icon>新增政策
          </el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-input v-model="filters.search" placeholder="搜索标题" clearable style="width: 200px" @clear="loadData" @keyup.enter="loadData" />
        <el-select v-model="filters.policy_type" placeholder="政策类型" clearable style="width: 140px" @change="loadData">
          <el-option v-for="(label, key) in policyTypes" :key="key" :label="label" :value="key" />
        </el-select>
        <el-select v-model="filters.is_active" placeholder="状态" clearable style="width: 120px" @change="loadData">
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
        <el-button type="primary" @click="loadData">搜索</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="policy_number" label="政策编号" width="140" />
        <el-table-column prop="issuing_authority" label="发布机构" width="140" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">{{ policyTypes[row.policy_type] || row.policy_type }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览量" width="80" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="$router.push(`/policy/${row.id}`)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import policyApi from '@/api/policy'
import { ElMessage, ElMessageBox } from 'element-plus'

const policyTypes = {
  law: '法律法规', regulation: '部门规章', notice: '通知公告',
  standard: '标准规范', guidance: '指导意见', plan: '规划计划', other: '其他'
}

const loading = ref(false)
const tableData = ref([])
const filters = ref({ search: '', policy_type: '', is_active: undefined })
const pagination = ref({ page: 1, pageSize: 10, total: 0 })

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      search: filters.value.search || undefined,
      policy_type: filters.value.policy_type || undefined
    }
    if (filters.value.is_active !== undefined && filters.value.is_active !== '') params.is_active = filters.value.is_active
    const data = await policyApi.getList(params)
    tableData.value = data.results || []
    pagination.value.total = data.count || 0
  } finally {
    loading.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定要删除「${row.title}」吗？`, '确认删除', { type: 'warning' })
  await policyApi.delete(row.id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => { loadData() })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

<template>
  <div class="creation-list">
    <el-card>
      <template #header><span>创作管理</span></template>

      <div class="filter-bar">
        <el-input v-model="filters.search" placeholder="搜索标题/作者" clearable style="width: 200px" @clear="loadData" @keyup.enter="loadData" />
        <el-select v-model="filters.type" placeholder="类型" clearable style="width: 120px" @change="loadData">
          <el-option v-for="(label, key) in creationTypes" :key="key" :label="label" :value="key" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px" @change="loadData">
          <el-option v-for="(label, key) in creationStatuses" :key="key" :label="label" :value="key" />
        </el-select>
        <el-button type="primary" @click="loadData">搜索</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="author" label="作者" width="120" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">{{ creationTypes[row.type] || row.type }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="creationStatusType[row.status] || 'info'" size="small">{{ creationStatuses[row.status] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="精选" width="70">
          <template #default="{ row }">
            <el-switch v-model="row.is_featured" @change="toggleFeatured(row)" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="公开" width="70">
          <template #default="{ row }">
            <el-switch v-model="row.is_public" @change="togglePublic(row)" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览" width="70" />
        <el-table-column prop="like_count" label="点赞" width="70" />
        <el-table-column prop="comment_count" label="评论" width="70" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-dropdown trigger="click" @command="(cmd) => handleStatusChange(row, cmd)">
              <el-button type="primary" link size="small">审核<el-icon><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="published" :disabled="row.status === 'published'">通过发布</el-dropdown-item>
                  <el-dropdown-item command="rejected" :disabled="row.status === 'rejected'">拒绝</el-dropdown-item>
                  <el-dropdown-item command="archived" :disabled="row.status === 'archived'">归档</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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
import adminApi from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const creationTypes = { video: '视频', photo: '图片', article: '文章', music: '音乐' }
const creationStatuses = { draft: '草稿', published: '已发布', reviewing: '审核中', rejected: '已拒绝', archived: '已归档' }
const creationStatusType = { draft: 'info', published: 'success', reviewing: 'warning', rejected: 'danger', archived: 'info' }

const loading = ref(false)
const tableData = ref([])
const filters = ref({ search: '', type: '', status: '' })
const pagination = ref({ page: 1, pageSize: 10, total: 0 })

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      search: filters.value.search || undefined,
      type: filters.value.type || undefined,
      status: filters.value.status || undefined
    }
    const data = await adminApi.getCreations(params)
    tableData.value = data.results || []
    pagination.value.total = data.count || 0
  } finally {
    loading.value = false
  }
}

async function toggleFeatured(row) {
  try {
    await adminApi.updateCreation(row.id, { is_featured: row.is_featured })
    ElMessage.success(row.is_featured ? '已设为精选' : '已取消精选')
  } catch {
    row.is_featured = !row.is_featured
  }
}

async function togglePublic(row) {
  try {
    await adminApi.updateCreation(row.id, { is_public: row.is_public })
    ElMessage.success(row.is_public ? '已公开' : '已设为私密')
  } catch {
    row.is_public = !row.is_public
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定要删除「${row.title}」吗？`, '确认删除', { type: 'warning' })
  await adminApi.deleteCreation(row.id)
  ElMessage.success('删除成功')
  loadData()
}

async function handleStatusChange(row, newStatus) {
  try {
    await adminApi.updateCreation(row.id, { status: newStatus })
    ElMessage.success('状态已更新')
    loadData()
  } catch {
    // handled by interceptor
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

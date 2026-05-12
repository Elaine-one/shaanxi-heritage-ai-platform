<template>
  <div class="post-list">
    <el-card>
      <template #header>
        <div class="card-header"><span>帖子管理</span></div>
      </template>

      <div class="filter-bar">
        <el-input v-model="filters.search" placeholder="搜索标题/作者" clearable style="width: 200px" @clear="loadData" @keyup.enter="loadData" />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px" @change="loadData">
          <el-option label="已发布" value="published" />
          <el-option label="已隐藏" value="hidden" />
          <el-option label="草稿" value="draft" />
          <el-option label="已删除" value="deleted" />
        </el-select>
        <el-button type="primary" @click="loadData">搜索</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="author" label="作者" width="120" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">{{ statusMap[row.status]?.label || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置顶" width="70">
          <template #default="{ row }">
            <el-switch v-model="row.is_pinned" @change="togglePin(row)" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="精华" width="70">
          <template #default="{ row }">
            <el-switch v-model="row.is_featured" @change="toggleFeature(row)" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="锁定" width="70">
          <template #default="{ row }">
            <el-switch v-model="row.is_locked" @change="toggleLock(row)" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览" width="70" />
        <el-table-column prop="like_count" label="点赞" width="70" />
        <el-table-column prop="comment_count" label="评论" width="70" />
        <el-table-column label="标签" width="120">
          <template #default="{ row }">
            <el-tag v-for="tag in (row.tags || []).slice(0, 2)" :key="tag" size="small" style="margin: 2px;">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-dropdown trigger="click" @command="(cmd) => handleStatusChange(row, cmd)">
              <el-button type="primary" link size="small">状态<el-icon><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="published" :disabled="row.status === 'published'">发布</el-dropdown-item>
                  <el-dropdown-item command="hidden" :disabled="row.status === 'hidden'">隐藏</el-dropdown-item>
                  <el-dropdown-item command="draft" :disabled="row.status === 'draft'">草稿</el-dropdown-item>
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

const statusMap = {
  published: { label: '已发布', type: 'success' },
  hidden: { label: '已隐藏', type: 'warning' },
  draft: { label: '草稿', type: 'info' },
  deleted: { label: '已删除', type: 'danger' }
}

const loading = ref(false)
const tableData = ref([])
const filters = ref({ search: '', status: '' })
const pagination = ref({ page: 1, pageSize: 10, total: 0 })

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      search: filters.value.search || undefined,
      status: filters.value.status || undefined
    }
    const data = await adminApi.getPosts(params)
    tableData.value = data.results || []
    pagination.value.total = data.count || 0
  } finally {
    loading.value = false
  }
}

async function togglePin(row) {
  try {
    await adminApi.updatePost(row.id, { is_pinned: row.is_pinned })
    ElMessage.success(row.is_pinned ? '已置顶' : '已取消置顶')
  } catch {
    row.is_pinned = !row.is_pinned
  }
}

async function toggleFeature(row) {
  try {
    await adminApi.updatePost(row.id, { is_featured: row.is_featured })
    ElMessage.success(row.is_featured ? '已设为精华' : '已取消精华')
  } catch {
    row.is_featured = !row.is_featured
  }
}

async function toggleLock(row) {
  try {
    await adminApi.updatePost(row.id, { is_locked: row.is_locked })
    ElMessage.success(row.is_locked ? '已锁定' : '已解锁')
  } catch {
    row.is_locked = !row.is_locked
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定要删除「${row.title}」吗？`, '确认删除', { type: 'warning' })
  await adminApi.deletePost(row.id)
  ElMessage.success('删除成功')
  loadData()
}

async function handleStatusChange(row, newStatus) {
  try {
    await adminApi.updatePost(row.id, { status: newStatus })
    ElMessage.success('状态已更新')
    loadData()
  } catch {
    // handled by interceptor
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

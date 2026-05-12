<template>
  <div class="user-list">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>用户管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>新增用户
          </el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-input v-model="filters.search" placeholder="搜索用户名/邮箱" clearable style="width: 240px" @clear="loadData" @keyup.enter="loadData" />
        <el-select v-model="filters.is_active" placeholder="状态" clearable style="width: 120px" @change="loadData">
          <el-option label="活跃" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
        <el-select v-model="filters.is_staff" placeholder="管理员" clearable style="width: 120px" @change="loadData">
          <el-option label="是" :value="true" />
          <el-option label="否" :value="false" />
        </el-select>
        <el-button type="primary" @click="loadData">搜索</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '活跃' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="管理员" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_superuser" type="danger" size="small">超管</el-tag>
            <el-tag v-else-if="row.is_staff" type="warning" size="small">管理员</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="date_joined" label="注册时间" width="170">
          <template #default="{ row }">{{ formatDate(row.date_joined) }}</template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="170">
          <template #default="{ row }">{{ formatDate(row.last_login) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="$router.push(`/users/${row.id}`)">详情</el-button>
            <el-button :type="row.is_active ? 'danger' : 'success'" link size="small" @click="toggleActive(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
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

    <el-dialog v-model="showCreateDialog" title="新增用户" width="480px" @close="resetCreateForm">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="createForm.password" type="password" show-password placeholder="请输入密码（至少6位）" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="createForm.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="createForm.is_staff" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">确认创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import adminApi from '@/api/admin'
import { ElMessage } from 'element-plus'

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

const loading = ref(false)
const tableData = ref([])
const filters = ref({ search: '', is_active: undefined, is_staff: undefined })
const pagination = ref({ page: 1, pageSize: 10, total: 0 })

const showCreateDialog = ref(false)
const createLoading = ref(false)
const createForm = ref({
  username: '',
  password: '',
  email: '',
  is_staff: false,
})

function resetCreateForm() {
  createForm.value = { username: '', password: '', email: '', is_staff: false }
}

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      search: filters.value.search || undefined
    }
    if (filters.value.is_active !== undefined && filters.value.is_active !== '') params.is_active = filters.value.is_active
    if (filters.value.is_staff !== undefined && filters.value.is_staff !== '') params.is_staff = filters.value.is_staff
    const data = await adminApi.getUsers(params)
    tableData.value = data.results || []
    pagination.value.total = data.count || 0
  } finally {
    loading.value = false
  }
}

async function toggleActive(row) {
  try {
    await adminApi.updateUser(row.id, { is_active: !row.is_active })
    ElMessage.success(row.is_active ? '已禁用' : '已启用')
    loadData()
  } catch {
    // handled by interceptor
  }
}

async function handleCreate() {
  if (!createForm.value.username || !createForm.value.password) {
    ElMessage.warning('用户名和密码不能为空')
    return
  }
  if (createForm.value.password.length < 6) {
    ElMessage.warning('密码长度不能少于6位')
    return
  }
  createLoading.value = true
  try {
    await adminApi.createUser(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    loadData()
  } catch {
    // handled by interceptor
  } finally {
    createLoading.value = false
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

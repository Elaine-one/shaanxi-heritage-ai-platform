<template>
  <div class="user-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>用户详情</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <el-descriptions :column="2" border v-if="user">
        <el-descriptions-item label="ID">{{ user.id }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ user.email }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="user.is_active ? 'success' : 'danger'">{{ user.is_active ? '活跃' : '禁用' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="管理员">
          <el-tag v-if="user.is_superuser" type="danger">超级管理员</el-tag>
          <el-tag v-else-if="user.is_staff" type="warning">管理员</el-tag>
          <el-tag v-else type="info">普通用户</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ formatDate(user.date_joined) }}</el-descriptions-item>
        <el-descriptions-item label="最后登录">{{ formatDate(user.last_login) }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px;">
        <el-button :type="user?.is_active ? 'danger' : 'success'" @click="toggleActive">
          {{ user?.is_active ? '禁用账户' : '启用账户' }}
        </el-button>
        <el-button v-if="!user?.is_staff" type="warning" @click="toggleStaff">设为管理员</el-button>
        <el-button v-if="user?.is_staff && !user?.is_superuser" type="info" @click="toggleStaff">取消管理员</el-button>
        <el-button type="primary" @click="showResetDialog = true">重置密码</el-button>
      </div>
    </el-card>

    <el-dialog v-model="showResetDialog" title="重置密码" width="420px" @close="closeResetDialog">
      <el-form :model="resetFormData" label-width="80px">
        <el-form-item label="用户">
          <el-input :model-value="user?.username" disabled />
        </el-form-item>
        <el-form-item label="新密码" required>
          <el-input v-model="resetFormData.new_password" type="password" show-password placeholder="请输入新密码（至少6位）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResetDialog = false">取消</el-button>
        <el-button type="primary" :loading="resetLoading" @click="handleResetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import adminApi from '@/api/admin'
import { ElMessage } from 'element-plus'

const route = useRoute()
const loading = ref(false)
const user = ref(null)

const showResetDialog = ref(false)
const resetLoading = ref(false)
const resetFormData = ref({ new_password: '' })

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

function closeResetDialog() {
  resetFormData.value = { new_password: '' }
}

async function loadDetail() {
  loading.value = true
  try {
    user.value = await adminApi.getUserDetail(route.params.id)
  } finally {
    loading.value = false
  }
}

async function toggleActive() {
  try {
    await adminApi.updateUser(user.value.id, { is_active: !user.value.is_active })
    ElMessage.success(user.value.is_active ? '已禁用' : '已启用')
    loadDetail()
  } catch {
    // handled
  }
}

async function toggleStaff() {
  try {
    await adminApi.updateUser(user.value.id, { is_staff: !user.value.is_staff })
    ElMessage.success(user.value.is_staff ? '已取消管理员' : '已设为管理员')
    loadDetail()
  } catch {
    // handled
  }
}

async function handleResetPassword() {
  if (!resetFormData.value.new_password) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (resetFormData.value.new_password.length < 6) {
    ElMessage.warning('密码长度不能少于6位')
    return
  }
  resetLoading.value = true
  try {
    await adminApi.resetPassword(user.value.id, resetFormData.value)
    ElMessage.success('密码重置成功')
    showResetDialog.value = false
  } catch {
    // handled
  } finally {
    resetLoading.value = false
  }
}

onMounted(() => { loadDetail() })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

<template>
  <div class="announcement-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>公告管理</span>
          <el-button type="primary" size="small" @click="openDialog()">
            <el-icon><Plus /></el-icon>新增公告
          </el-button>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置顶" width="70">
          <template #default="{ row }">
            <el-tag :type="row.is_pinned ? 'warning' : 'info'" size="small">{{ row.is_pinned ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="order" label="排序" width="70" />
        <el-table-column prop="publish_date" label="发布日期" width="120" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingItem ? '编辑公告' : '新增公告'" width="560px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="formData.title" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="formData.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="启用">
              <el-switch v-model="formData.is_active" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="置顶">
              <el-switch v-model="formData.is_pinned" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="排序">
              <el-input-number v-model="formData.order" :min="0" :max="999" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import adminApi from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const editingItem = ref(null)
const formData = ref({ title: '', content: '', is_active: true, is_pinned: false, order: 0 })

async function loadData() {
  loading.value = true
  try {
    const data = await adminApi.getAnnouncements()
    tableData.value = Array.isArray(data) ? data : data.results || []
  } finally {
    loading.value = false
  }
}

function openDialog(item = null) {
  editingItem.value = item
  formData.value = item
    ? { title: item.title, content: item.content || '', is_active: item.is_active, is_pinned: item.is_pinned, order: item.order || 0 }
    : { title: '', content: '', is_active: true, is_pinned: false, order: 0 }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formData.value.title) {
    ElMessage.warning('请输入公告标题')
    return
  }
  submitting.value = true
  try {
    if (editingItem.value) {
      await adminApi.updateAnnouncement(editingItem.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await adminApi.createAnnouncement(formData.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定要删除公告「${row.title}」吗？`, '确认删除', { type: 'warning' })
  await adminApi.deleteAnnouncement(row.id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => { loadData() })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

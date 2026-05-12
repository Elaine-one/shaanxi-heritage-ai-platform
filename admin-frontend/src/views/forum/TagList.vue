<template>
  <div class="tag-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>标签管理</span>
          <el-button type="primary" size="small" @click="openDialog()">
            <el-icon><Plus /></el-icon>新增标签
          </el-button>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="标签名称" min-width="150" />
        <el-table-column label="颜色" width="100">
          <template #default="{ row }">
            <span v-if="row.color" class="color-dot" :style="{ backgroundColor: row.color }"></span>
            {{ row.color || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="post_count" label="帖子数" width="100" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingTag ? '编辑标签' : '新增标签'" width="480px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="formData.color" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" />
        </el-form-item>
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
const editingTag = ref(null)
const formData = ref({ name: '', color: '#8B2500', description: '' })

async function loadData() {
  loading.value = true
  try {
    const data = await adminApi.getTags()
    tableData.value = Array.isArray(data) ? data : data.results || []
  } finally {
    loading.value = false
  }
}

function openDialog(tag = null) {
  editingTag.value = tag
  formData.value = tag
    ? { name: tag.name, color: tag.color || '#8B2500', description: tag.description || '' }
    : { name: '', color: '#8B2500', description: '' }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formData.value.name) {
    ElMessage.warning('请输入标签名称')
    return
  }
  submitting.value = true
  try {
    if (editingTag.value) {
      await adminApi.updateTag(editingTag.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await adminApi.createTag(formData.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定要删除标签「${row.name}」吗？`, '确认删除', { type: 'warning' })
  await adminApi.deleteTag(row.id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => { loadData() })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.color-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  vertical-align: middle;
  margin-right: 6px;
}
</style>

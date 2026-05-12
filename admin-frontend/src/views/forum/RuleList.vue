<template>
  <div class="rule-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>版规管理</span>
          <el-button type="primary" size="small" @click="openDialog()">
            <el-icon><Plus /></el-icon>新增版规
          </el-button>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="content" label="规则内容" min-width="400" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="order" label="排序" width="70" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingItem ? '编辑版规' : '新增版规'" width="560px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="内容" required>
          <el-input v-model="formData.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="启用">
              <el-switch v-model="formData.is_active" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
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
const formData = ref({ content: '', is_active: true, order: 0 })

async function loadData() {
  loading.value = true
  try {
    const data = await adminApi.getRules()
    tableData.value = Array.isArray(data) ? data : data.results || []
  } finally {
    loading.value = false
  }
}

function openDialog(item = null) {
  editingItem.value = item
  formData.value = item
    ? { content: item.content, is_active: item.is_active, order: item.order || 0 }
    : { content: '', is_active: true, order: 0 }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formData.value.content) {
    ElMessage.warning('请输入版规内容')
    return
  }
  submitting.value = true
  try {
    if (editingItem.value) {
      await adminApi.updateRule(editingItem.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await adminApi.createRule(formData.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定要删除此版规吗？', '确认删除', { type: 'warning' })
  await adminApi.deleteRule(row.id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => { loadData() })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

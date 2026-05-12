<template>
  <div class="creation-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>创作详情</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <el-descriptions :column="2" border v-if="creation">
        <el-descriptions-item label="ID">{{ creation.id }}</el-descriptions-item>
        <el-descriptions-item label="标题">{{ creation.title }}</el-descriptions-item>
        <el-descriptions-item label="作者">{{ creation.author_name || creation.author }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ creationTypes[creation.type] || creation.type }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="creationStatusType[creation.status] || 'info'" size="small">{{ creationStatuses[creation.status] || creation.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="精选">
          <el-switch v-model="creation.is_featured" @change="toggleFeatured" size="small" />
        </el-descriptions-item>
        <el-descriptions-item label="浏览量">{{ creation.view_count }}</el-descriptions-item>
        <el-descriptions-item label="点赞数">{{ creation.like_count }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ creation.description }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(creation.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDate(creation.updated_at) }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px;">
        <el-button type="danger" @click="handleDelete">删除创作</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import creationApi from '@/api/creation'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const creation = ref(null)

const creationTypes = { video: '视频', photo: '图片', article: '文章', music: '音乐' }
const creationStatuses = { draft: '草稿', published: '已发布', reviewing: '审核中', rejected: '已拒绝', archived: '已归档' }
const creationStatusType = { draft: 'info', published: 'success', reviewing: 'warning', rejected: 'danger', archived: 'info' }

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

async function loadDetail() {
  loading.value = true
  try {
    creation.value = await creationApi.getDetail(route.params.id)
  } finally {
    loading.value = false
  }
}

async function toggleFeatured() {
  try {
    await creationApi.partialUpdate(creation.value.id, { is_featured: creation.value.is_featured })
    ElMessage.success(creation.value.is_featured ? '已设为精选' : '已取消精选')
  } catch {
    creation.value.is_featured = !creation.value.is_featured
  }
}

async function handleDelete() {
  await ElMessageBox.confirm('确定要删除此创作吗？', '确认删除', { type: 'warning' })
  await creationApi.delete(creation.value.id)
  ElMessage.success('删除成功')
  router.push('/creation')
}

onMounted(() => { loadDetail() })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

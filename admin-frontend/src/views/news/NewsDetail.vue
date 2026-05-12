<template>
  <div class="news-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑资讯' : '新增资讯' }}</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" v-loading="loading">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="作者" prop="author">
              <el-input v-model="form.author" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="来源" prop="source">
              <el-input v-model="form.source" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="来源链接" prop="source_url">
              <el-input v-model="form.source_url" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="摘要" prop="summary">
          <el-input v-model="form.summary" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="8" />
        </el-form-item>
        <el-form-item label="配图URL" prop="image_url">
          <el-input v-model="form.image_url" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="发布时间" prop="publish_date">
              <el-date-picker v-model="form.publish_date" type="datetime" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DDTHH:mm:ss" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="启用" prop="is_active">
              <el-switch v-model="form.is_active" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="精选" prop="is_featured">
              <el-switch v-model="form.is_featured" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="标签" prop="tags">
          <el-input v-model="form.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建资讯' }}
          </el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import newsApi from '@/api/news'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const submitting = ref(false)
const isEdit = computed(() => !!route.params.id)

const form = ref({
  title: '', summary: '', content: '', author: '', source: '', source_url: '',
  image_url: '', publish_date: '', is_active: true, is_featured: false, tags: ''
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
  publish_date: [{ required: true, message: '请选择发布时间', trigger: 'change' }]
}

async function loadDetail() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const data = await newsApi.getDetail(route.params.id)
    form.value = { ...form.value, ...data }
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (isEdit.value) {
      await newsApi.update(route.params.id, form.value)
      ElMessage.success('保存成功')
    } else {
      await newsApi.create(form.value)
      ElMessage.success('创建成功')
    }
    router.push('/news')
  } finally {
    submitting.value = false
  }
}

onMounted(() => { loadDetail() })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

<template>
  <div class="heritage-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑非遗项目' : '新增非遗项目' }}</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" v-loading="loading">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="项目名称" prop="name">
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="拼音名称" prop="pinyin_name">
              <el-input v-model="form.pinyin_name" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="类别" prop="category">
              <el-input v-model="form.category" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="级别" prop="level">
              <el-input v-model="form.level" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="批次" prop="batch">
              <el-input v-model="form.batch" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="地区" prop="region">
              <el-input v-model="form.region" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="纬度" prop="latitude">
              <el-input-number v-model="form.latitude" :precision="6" :controls="false" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="经度" prop="longitude">
              <el-input-number v-model="form.longitude" :precision="6" :controls="false" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="历史渊源" prop="history">
          <el-input v-model="form.history" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="基本内容/特征" prop="features">
          <el-input v-model="form.features" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="重要价值" prop="value">
          <el-input v-model="form.value" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="存续状况" prop="status">
          <el-input v-model="form.status" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="保护措施" prop="protection_measures">
          <el-input v-model="form.protection_measures" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="传承人" prop="inheritors">
          <el-input v-model="form.inheritors" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="相关制品" prop="related_works">
          <el-input v-model="form.related_works" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="主图URL" prop="main_image_url">
          <el-input v-model="form.main_image_url" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建项目' }}
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
import heritageApi from '@/api/heritage'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const submitting = ref(false)

const isEdit = computed(() => !!route.params.id)

const form = ref({
  name: '', pinyin_name: '', category: '', level: '', region: '', batch: '',
  description: '', history: '', features: '', value: '', status: '',
  protection_measures: '', inheritors: '', related_works: '',
  main_image_url: '', gallery_image_urls: [],
  latitude: null, longitude: null
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  category: [{ required: true, message: '请输入类别', trigger: 'blur' }],
  level: [{ required: true, message: '请输入级别', trigger: 'blur' }],
  region: [{ required: true, message: '请输入地区', trigger: 'blur' }],
  description: [{ required: true, message: '请输入描述', trigger: 'blur' }]
}

async function loadDetail() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const data = await heritageApi.getDetail(route.params.id)
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
      await heritageApi.update(route.params.id, form.value)
      ElMessage.success('保存成功')
    } else {
      await heritageApi.create(form.value)
      ElMessage.success('创建成功')
    }
    router.push('/heritage')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

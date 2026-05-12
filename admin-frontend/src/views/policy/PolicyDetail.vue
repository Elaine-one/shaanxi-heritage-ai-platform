<template>
  <div class="policy-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑政策' : '新增政策' }}</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" v-loading="loading">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="政策编号" prop="policy_number">
              <el-input v-model="form.policy_number" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="发布机构" prop="issuing_authority">
              <el-input v-model="form.issuing_authority" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="政策类型" prop="policy_type">
              <el-select v-model="form.policy_type" style="width: 100%">
                <el-option v-for="(label, key) in policyTypes" :key="key" :label="label" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="摘要" prop="summary">
          <el-input v-model="form.summary" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="8" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="发布日期" prop="publish_date">
              <el-date-picker v-model="form.publish_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="生效日期" prop="effective_date">
              <el-date-picker v-model="form.effective_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="启用" prop="is_active">
              <el-switch v-model="form.is_active" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="来源链接" prop="source_url">
          <el-input v-model="form.source_url" />
        </el-form-item>
        <el-form-item label="附件链接" prop="attachment_url">
          <el-input v-model="form.attachment_url" />
        </el-form-item>
        <el-form-item label="标签" prop="tags">
          <el-input v-model="form.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建政策' }}
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
import policyApi from '@/api/policy'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const submitting = ref(false)
const isEdit = computed(() => !!route.params.id)

const policyTypes = {
  law: '法律法规', regulation: '部门规章', notice: '通知公告',
  standard: '标准规范', guidance: '指导意见', plan: '规划计划', other: '其他'
}

const form = ref({
  title: '', summary: '', content: '', policy_number: '', issuing_authority: '',
  policy_type: 'other', publish_date: '', effective_date: '', source_url: '',
  attachment_url: '', tags: '', is_active: true
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
  issuing_authority: [{ required: true, message: '请输入发布机构', trigger: 'blur' }],
  publish_date: [{ required: true, message: '请选择发布日期', trigger: 'change' }]
}

async function loadDetail() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const data = await policyApi.getDetail(route.params.id)
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
      await policyApi.update(route.params.id, form.value)
      ElMessage.success('保存成功')
    } else {
      await policyApi.create(form.value)
      ElMessage.success('创建成功')
    }
    router.push('/policy')
  } finally {
    submitting.value = false
  }
}

onMounted(() => { loadDetail() })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

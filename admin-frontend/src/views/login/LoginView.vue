<template>
  <div class="login-container">
    <div class="login-pattern"></div>
    <div class="login-card">
      <div class="login-header">
        <div class="login-emblem">非遗</div>
        <h1>陕西非遗管理后台</h1>
        <p>非物质文化遗产保护平台</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.remember_me">记住我</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" size="large" style="width: 100%" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <span>陕西非物质文化遗产保护平台</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ensureCsrfToken } from '@/utils/csrf'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const form = ref({
  username: '',
  password: '',
  remember_me: false
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await ensureCsrfToken()
    await authStore.login(form.value)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (error) {
    const message = error.response?.data?.message || '登录失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #1a1a2e 0%, #16213e 30%, #0f3460 60%, #1a1a2e 100%);
  position: relative;
  overflow: hidden;
}

.login-pattern {
  position: absolute;
  inset: 0;
  opacity: 0.06;
  background-image:
    radial-gradient(circle at 20% 80%, #C5963A 1px, transparent 1px),
    radial-gradient(circle at 80% 20%, #C5963A 1px, transparent 1px),
    radial-gradient(circle at 50% 50%, #8B2500 1px, transparent 1px);
  background-size: 60px 60px, 80px 80px, 100px 100px;
}

.login-pattern::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    repeating-linear-gradient(0deg, transparent, transparent 59px, rgba(197, 150, 58, 0.15) 59px, rgba(197, 150, 58, 0.15) 60px),
    repeating-linear-gradient(90deg, transparent, transparent 59px, rgba(197, 150, 58, 0.15) 59px, rgba(197, 150, 58, 0.15) 60px);
}

.login-card {
  width: 440px;
  padding: 48px 40px 36px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  border: 1px solid rgba(197, 150, 58, 0.3);
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(197, 150, 58, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-emblem {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #8B2500, #A9442A);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #C5963A;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
  border: 2px solid #C5963A;
  box-shadow: 0 4px 20px rgba(139, 37, 0, 0.3);
}

.login-header h1 {
  font-size: 26px;
  color: #1a1a2e;
  margin: 0 0 8px;
  font-weight: 700;
  letter-spacing: 4px;
}

.login-header p {
  color: #8B2500;
  font-size: 14px;
  margin: 0;
  letter-spacing: 2px;
}

.login-card :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.login-card :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 1px #8B2500 inset;
}

.login-card :deep(.el-button--primary) {
  background: linear-gradient(135deg, #8B2500, #A9442A);
  border: none;
  border-radius: 8px;
  font-size: 16px;
  letter-spacing: 8px;
  height: 44px;
}

.login-card :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #A9442A, #C16255);
}

.login-card :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #8B2500;
  border-color: #8B2500;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #E8DFD0;
}

.login-footer span {
  color: #999;
  font-size: 12px;
  letter-spacing: 1px;
}
</style>

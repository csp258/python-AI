<template>
  <div class="login-container">
    <div class="login-card">
      <h1>电商RAG知识库问答系统</h1>
      <h3>用户注册</h3>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleRegister">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名(2-50位)" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码(至少6位)" size="large" show-password />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" native-type="submit" style="width:100%">
            注册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-link">
        已有账号？<router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const formRef = ref(null)

const form = reactive({ username: '', password: '', confirmPassword: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次密码不一致'))
  else callback()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名2-50位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await auth.register(form.username, form.password)
    router.push('/chat')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container { display: flex; align-items: center; justify-content: center; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.login-card { width: 400px; padding: 40px; background: #fff; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.login-card h1 { text-align: center; font-size: 20px; color: #333; margin-bottom: 8px; }
.login-card h3 { text-align: center; font-weight: normal; color: #666; margin-bottom: 24px; }
.register-link { text-align: center; color: #999; }
.register-link a { color: #667eea; }
</style>

<template>
  <div class="main-layout">
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <h2 @click="$router.push('/chat')" style="cursor:pointer">电商RAG知识库问答</h2>
        </div>
        <div class="header-right">
          <el-button v-if="auth.isAdmin" @click="$router.push('/knowledge')">知识库管理</el-button>
          <el-button @click="$router.push('/chat')">问答</el-button>
          <el-button @click="$router.push('/user')">用户中心</el-button>
          <el-button type="danger" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main>
        <div class="center-container">
          <el-card style="max-width:500px;margin:0 auto">
            <template #header><h3>修改密码</h3></template>
            <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
              <el-form-item label="原密码" prop="oldPassword">
                <el-input v-model="form.oldPassword" type="password" show-password />
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input v-model="form.newPassword" type="password" show-password />
              </el-form-item>
              <el-form-item label="确认密码" prop="confirmPassword">
                <el-input v-model="form.confirmPassword" type="password" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="loading" @click="handleChange">修改密码</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const formRef = ref(null)

const form = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== form.newPassword) callback(new Error('两次密码不一致'))
  else callback()
}

const rules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

async function handleChange() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await auth.changePassword(form.oldPassword, form.newPassword)
    ElMessage.success('密码修改成功')
    form.oldPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
  } finally {
    loading.value = false
  }
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-layout { min-height: 100vh; background: #f5f7fa; }
.app-header { display: flex; align-items: center; justify-content: space-between; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.1); padding: 0 24px; height: 60px; }
.header-left h2 { font-size: 18px; color: #333; }
.header-right { display: flex; gap: 8px; }
.center-container { padding-top: 60px; }
</style>

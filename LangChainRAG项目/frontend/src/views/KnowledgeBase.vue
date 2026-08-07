<template>
  <div class="main-layout">
    <el-container style="height:100vh">
      <el-header class="app-header">
        <div class="header-left">
          <h2 @click="$router.push('/chat')" style="cursor:pointer">电商RAG知识库问答</h2>
          <el-tag type="warning" style="margin-left:12px">管理员模式</el-tag>
        </div>
        <div class="header-right">
          <el-button @click="$router.push('/chat')">问答</el-button>
          <el-button @click="$router.push('/user')">用户中心</el-button>
          <el-button type="danger" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main>
        <div class="kb-container">
          <!-- Upload Section -->
          <el-card style="margin-bottom:20px">
            <template #header>
              <h3>上传文档</h3>
            </template>
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :on-change="handleFileChange"
              :limit="10"
              :on-exceed="() => ElMessage.warning('一次最多上传10个文件')"
              :file-list="fileList"
              drag
              multiple
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div>将文件拖到此处，或<em>点击上传</em></div>
              <template #tip>
                <div style="margin-top:8px;color:#999">
                  支持 PDF、Word(.docx/.doc)、Excel(.xlsx/.xls)、TXT、Markdown、CSV，单文件最大50MB
                </div>
              </template>
            </el-upload>
            <el-button type="primary" @click="handleUpload" :loading="uploading" style="margin-top:12px" :disabled="!fileList.length">
              上传到知识库
            </el-button>
          </el-card>

          <!-- Document List -->
          <el-card>
            <template #header>
              <div style="display:flex;justify-content:space-between;align-items:center">
                <h3>已上传文档 ({{ documents.length }})</h3>
                <el-button type="danger" :disabled="!selectedIds.length" @click="handleBatchDelete">
                  删除选中 ({{ selectedIds.length }})
                </el-button>
              </div>
            </template>
            <el-table
              :data="documents"
              @selection-change="(rows) => selectedIds = rows.map(r => r.id)"
              stripe
              empty-text="暂无文档"
            >
              <el-table-column type="selection" width="50" />
              <el-table-column prop="filename" label="文件名" min-width="250" />
              <el-table-column prop="file_type" label="类型" width="80" />
              <el-table-column label="大小" width="100">
                <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
              </el-table-column>
              <el-table-column prop="chunk_count" label="分块数" width="80" />
              <el-table-column label="上传时间" width="170">
                <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
              </el-table-column>
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '../api'

const router = useRouter()
const auth = useAuthStore()
const documents = ref([])
const selectedIds = ref([])
const fileList = ref([])
const uploading = ref(false)
const uploadRef = ref(null)

onMounted(loadDocuments)

async function loadDocuments() {
  const res = await api.get('/knowledge/documents')
  documents.value = res.data
}

function handleFileChange(file, fileListRef) {
  fileList.value = fileListRef
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

async function handleUpload() {
  if (!fileList.value.length) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  let success = 0
  for (const fileInfo of fileList.value) {
    try {
      const form = new FormData()
      form.append('file', fileInfo.raw)
      await api.post('/knowledge/upload', form)
      success++
    } catch (e) {
      // error already handled by interceptor
    }
  }

  uploading.value = false
  fileList.value = []
  uploadRef.value.clearFiles()

  if (success) ElMessage.success(`成功上传 ${success} 个文件`)
  await loadDocuments()
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确定要删除此文档吗？', '确认', { type: 'warning' })
    await api.delete('/knowledge/documents', { data: { document_ids: [id] } })
    ElMessage.success('已删除')
    await loadDocuments()
  } catch (e) {
    if (e !== 'cancel') { /* api error handled by interceptor */ }
  }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 个文档吗？`, '确认', { type: 'warning' })
    await api.delete('/knowledge/documents', { data: { document_ids: selectedIds.value } })
    ElMessage.success('已删除')
    selectedIds.value = []
    await loadDocuments()
  } catch (e) {
    if (e !== 'cancel') { /* api error handled by interceptor */ }
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
.header-left { display: flex; align-items: center; }
.header-left h2 { font-size: 18px; color: #333; }
.header-right { display: flex; gap: 8px; }
.kb-container { max-width: 1100px; margin: 0 auto; padding: 20px 0; }
</style>

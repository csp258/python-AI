<template>
  <div class="main-layout">
    <el-container style="height:100vh">
      <el-header class="app-header">
        <div class="header-left">
          <h2>电商RAG知识库问答</h2>
        </div>
        <div class="header-right">
          <el-button v-if="auth.isAdmin" @click="$router.push('/knowledge')">知识库管理</el-button>
          <el-button @click="$router.push('/user')">用户中心</el-button>
          <el-button type="danger" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-container>
        <!-- Session Sidebar -->
        <el-aside width="280px" class="session-sidebar">
          <div class="sidebar-header">
            <el-button type="primary" @click="handleNewSession" style="width:100%">
              <el-icon><Plus /></el-icon> 新建会话
            </el-button>
          </div>
          <div class="session-list">
            <div
              v-for="s in chatStore.sessions"
              :key="s.id"
              :class="['session-item', { active: chatStore.currentSessionId === s.id }]"
              @click="handleSelectSession(s.id)"
            >
              <div class="session-title">{{ s.title }}</div>
              <div class="session-time">{{ formatTime(s.updated_at) }}</div>
              <el-popconfirm title="确定删除此会话?" @confirm="chatStore.deleteSession(s.id)">
                <template #reference>
                  <el-button class="session-delete" :icon="Delete" circle size="small" text @click.stop />
                </template>
              </el-popconfirm>
            </div>
            <div v-if="!chatStore.sessions.length" class="empty-hint">暂无会话，点击上方按钮创建</div>
          </div>
        </el-aside>

        <!-- Chat Area -->
        <el-main class="chat-area">
          <div v-if="!chatStore.currentSessionId" class="empty-chat">
            <h2>欢迎使用电商知识库问答系统</h2>
            <p>请选择或创建一个会话开始提问</p>
          </div>

          <div v-else class="chat-container">
            <!-- Messages -->
            <div class="messages-container" ref="msgContainer">
              <div v-for="(msg, idx) in chatStore.messages" :key="idx" :class="['message-item', msg.role]">
                <div class="message-avatar">
                  {{ msg.role === 'user' ? auth.user?.username?.[0]?.toUpperCase() : 'AI' }}
                </div>
                <div class="message-content">
                  <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
                  <div v-if="msg.sources && msg.sources.length" class="message-sources">
                    <div class="sources-title">引用来源：</div>
                    <div v-for="(src, i) in msg.sources" :key="i" class="source-item">
                      <el-popover placement="top" :width="500" trigger="click">
                        <template #reference>
                          <el-tag size="small" type="info" style="cursor:pointer">
                            {{ src.filename }} ({{ (src.score * 100).toFixed(0) }}%)
                          </el-tag>
                        </template>
                        <div class="source-content">{{ src.content }}</div>
                      </el-popover>
                    </div>
                  </div>
                  <!-- Streaming indicator for last assistant message -->
                  <div v-if="idx === chatStore.messages.length - 1 && msg.role === 'assistant' && isStreaming && msg.content === ''"
                    class="streaming-indicator">
                    <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Input Area -->
            <div class="input-area">
              <el-input
                v-model="question"
                type="textarea"
                :rows="3"
                placeholder="输入您的问题，基于知识库内容回答..."
                @keydown.enter.exact="handleSend"
                :disabled="isStreaming"
              />
              <el-button
                type="primary"
                :loading="isStreaming"
                :disabled="!question.trim()"
                @click="handleSend"
                style="margin-top:8px"
              >
                {{ isStreaming ? '回答中...' : '发送' }}
              </el-button>
            </div>
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useChatStore } from '../stores/chat'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { marked } from 'marked'
// SECURITY: sanitize AI-generated markdown before rendering as HTML to prevent XSS
import DOMPurify from 'dompurify'

const router = useRouter()
const auth = useAuthStore()
const chatStore = useChatStore()
const question = ref('')
const isStreaming = ref(false)
const msgContainer = ref(null)
const abortController = ref(null)

marked.setOptions({ breaks: true, gfm: true })

/** Convert markdown text to safe HTML for display in the chat bubble. */
function renderMarkdown(text) {
  if (!text) return ''
  // SECURITY: sanitize with DOMPurify before binding to v-html to prevent
  // XSS via malicious content in knowledge base or AI-generated responses.
  return DOMPurify.sanitize(marked.parse(text))
}

/**
 * Format an ISO timestamp into a human-friendly relative time string.
 * Handles naive datetimes (no timezone) by treating them as UTC.
 */
function formatTime(t) {
  if (!t) return ''
  // Treat naive datetime strings as UTC (no 'Z' or timezone offset)
  const d = /[+\-Z]/i.test(t.slice(-6)) ? new Date(t) : new Date(t + 'Z')
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString('zh-CN')
}

/** Scroll the message container to the latest message after DOM update. */
function scrollToBottom() {
  nextTick(() => {
    const el = msgContainer.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

onMounted(() => {
  chatStore.loadSessions()
})

/** Create a new chat session and immediately load its (empty) message list. */
async function handleNewSession() {
  const s = await chatStore.createSession()
  await chatStore.loadMessages(s.id)
}

/** Switch to a different session. Blocked during streaming to avoid data races. */
async function handleSelectSession(id) {
  if (isStreaming.value) return  // prevent session switching while an answer is mid-stream
  await chatStore.loadMessages(id)
  scrollToBottom()
}

/**
 * Send the user's question to the backend via SSE streaming.
 * Uses AbortController so in-flight requests can be cancelled on logout.
 */
async function handleSend() {
  const q = question.value.trim()
  if (!q || isStreaming.value) return
  if (!chatStore.currentSessionId) {
    // Auto-create a session if none selected yet
    await handleNewSession()
  }

  chatStore.addUserMessage(q)
  question.value = ''
  scrollToBottom()

  // Add placeholder assistant message
  chatStore.messages.push({
    role: 'assistant',
    content: '',
    sources: [],
    id: Date.now() + 1,
    session_id: chatStore.currentSessionId,
  })
  const assistantIdx = chatStore.messages.length - 1
  scrollToBottom()

  isStreaming.value = true
  abortController.value = new AbortController()
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/sessions/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        session_id: chatStore.currentSessionId,
        question: q,
      }),
      signal: abortController.value.signal,
    })

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = JSON.parse(line.slice(6))

        if (data.type === 'chunk') {
          chatStore.messages[assistantIdx].content += data.content
          scrollToBottom()
        } else if (data.type === 'sources') {
          chatStore.messages[assistantIdx].sources = data.content
        }
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') {
      chatStore.messages[assistantIdx].content = '抱歉，请求失败，请重试。'
    }
  } finally {
    isStreaming.value = false
    abortController.value = null
    chatStore.loadSessions()
  }
}

/** Log out: abort any in-flight SSE stream, clear auth/chat state, go to login. */
function handleLogout() {
  if (abortController.value) abortController.value.abort()  // prevent stale callbacks
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-layout { min-height: 100vh; background: #f5f7fa; }
.app-header { display: flex; align-items: center; justify-content: space-between; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.1); padding: 0 24px; height: 60px; }
.header-left h2 { font-size: 18px; color: #333; }
.header-right { display: flex; gap: 8px; }

.session-sidebar { background: #fff; border-right: 1px solid #e8e8e8; display: flex; flex-direction: column; }
.sidebar-header { padding: 16px; border-bottom: 1px solid #eee; }
.session-list { flex: 1; overflow-y: auto; padding: 8px; }
.session-item { padding: 12px; border-radius: 8px; cursor: pointer; position: relative; margin-bottom: 4px; }
.session-item:hover { background: #f0f2f5; }
.session-item.active { background: #e6f7ff; border: 1px solid #91d5ff; }
.session-title { font-size: 14px; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 30px; }
.session-time { font-size: 12px; color: #999; margin-top: 4px; }
.session-delete { position: absolute; right: 8px; top: 12px; opacity: 0; }
.session-item:hover .session-delete { opacity: 1; }
.empty-hint { text-align: center; color: #999; padding: 40px 16px; font-size: 14px; }

.chat-area { background: #f5f7fa; display: flex; flex-direction: column; }
.empty-chat { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #999; }
.empty-chat h2 { color: #666; margin-bottom: 8px; }

.chat-container { flex: 1; display: flex; flex-direction: column; max-width: 900px; margin: 0 auto; width: 100%; }
.messages-container { flex: 1; overflow-y: auto; padding: 20px; }

.message-item { display: flex; margin-bottom: 20px; gap: 12px; }
.message-item.user { flex-direction: row-reverse; }
.message-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; color: #fff; flex-shrink: 0; }
.message-item.user .message-avatar { background: #667eea; }
.message-item.assistant .message-avatar { background: #52c41a; }
.message-content { max-width: 75%; }
.message-item.user .message-content { text-align: right; }
.message-text { padding: 12px 16px; border-radius: 12px; line-height: 1.6; word-break: break-word; }
.message-item.user .message-text { background: #667eea; color: #fff; border-bottom-right-radius: 4px; }
.message-item.assistant .message-text { background: #fff; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.message-sources { margin-top: 8px; }
.sources-title { font-size: 12px; color: #999; margin-bottom: 4px; }
.source-item { display: inline-block; margin-right: 6px; margin-bottom: 4px; }
.source-content { max-height: 300px; overflow-y: auto; font-size: 13px; line-height: 1.6; white-space: pre-wrap; }

.input-area { padding: 16px; background: #fff; border-top: 1px solid #eee; }

.streaming-indicator { display: inline-flex; gap: 4px; padding: 4px 0; }
.dot { width: 6px; height: 6px; background: #999; border-radius: 50%; animation: blink 1.4s infinite ease-in-out; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }
</style>

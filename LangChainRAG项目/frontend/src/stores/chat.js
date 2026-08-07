import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref([])
  const currentSessionId = ref(null)
  const messages = ref([])
  const loading = ref(false)

  async function loadSessions() {
    const res = await api.get('/sessions')
    sessions.value = res.data
  }

  async function createSession(title = '新对话') {
    const res = await api.post('/sessions', { title })
    sessions.value.unshift(res.data)
    return res.data
  }

  async function loadMessages(sessionId) {
    currentSessionId.value = sessionId
    const res = await api.get(`/sessions/${sessionId}/messages`)
    messages.value = res.data
  }

  function addUserMessage(content) {
    messages.value.push({
      role: 'user',
      content,
      id: Date.now(),
      session_id: currentSessionId.value,
    })
  }

  async function deleteSession(sessionId) {
    await api.delete(`/sessions/${sessionId}`)
    sessions.value = sessions.value.filter((s) => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
      messages.value = []
    }
  }

  function reset() {
    sessions.value = []
    currentSessionId.value = null
    messages.value = []
  }

  return {
    sessions, currentSessionId, messages, loading,
    loadSessions, createSession, loadMessages, addUserMessage, deleteSession, reset,
  }
})

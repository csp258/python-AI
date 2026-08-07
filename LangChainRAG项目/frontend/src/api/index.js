/**
 * Centralized Axios instance with JWT auth and 401 handling.
 *
 * - The request interceptor attaches the Bearer token from localStorage.
 * - The response interceptor catches 401 errors, clears auth/chat state,
 *   and redirects to the login page so the user can re-authenticate.
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'
import { useChatStore } from '../stores/chat'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// Attach JWT token to every outgoing request so the backend can identify the user
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401 (token expired/invalid), wipe auth state and chat data, then redirect
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      useChatStore().reset()   // prevent data leak to next login session
      router.push('/login')
    }
    const msg = err.response?.data?.detail || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default api

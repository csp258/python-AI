/**
 * Auth Store — manages user authentication state and JWT token lifecycle.
 *
 * On logout or 401 expiry, the chat store is reset so that the next user
 * who logs in does not see the previous user's session data.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'
import { useChatStore } from './chat'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  /**
   * Log in with username + password. On success, stores the JWT token and
   * user profile in localStorage so they survive page reloads.
   */
  function login(username, password) {
    return api.post('/auth/login', { username, password }).then((res) => {
      token.value = res.data.access_token
      user.value = res.data.user
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
      return res.data
    })
  }

  /** Register a new account and automatically log in on success. */
  function register(username, password) {
    return api.post('/auth/register', { username, password }).then((res) => {
      token.value = res.data.access_token
      user.value = res.data.user
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
      return res.data
    })
  }

  /**
   * Log out: clear auth state, remove persisted token, and reset the chat
   * store so no stale session data leaks to the next login.
   */
  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    useChatStore().reset()
  }

  /** Change the current user's password. Requires the old password for verification. */
  function changePassword(oldPassword, newPassword) {
    return api.put('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  }

  return { token, user, isLoggedIn, isAdmin, login, register, logout, changePassword }
})

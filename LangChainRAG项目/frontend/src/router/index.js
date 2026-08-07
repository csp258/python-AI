import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    redirect: '/chat',
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/Chat.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge',
    name: 'KnowledgeBase',
    component: () => import('../views/KnowledgeBase.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/user',
    name: 'UserCenter',
    component: () => import('../views/UserCenter.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  if (to.meta.requiresAdmin && !user.is_admin) {
    return next('/chat')
  }

  if (to.meta.guest && token) {
    return next('/chat')
  }

  next()
})

export default router

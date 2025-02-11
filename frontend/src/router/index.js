import { createRouter, createWebHistory } from 'vue-router'
import IndexPage from 'pages/IndexPage.vue'
import SignUpPage from 'pages/SignUpPage.vue'
import SignInPage from 'pages/SignInPage.vue'
import UserHome from 'pages/UserHome.vue'

const routes = [
  { path: '/', component: IndexPage },
  { path: '/signup', component: SignUpPage },
  { path: '/signin', component: SignInPage },
  { path: '/home', component: UserHome, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Ochrana stránek před nepřihlášenými uživateli
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('user') !== null
  if (to.matched.some(record => record.meta.requiresAuth) && !isAuthenticated) {
    next('/signin')
  } else {
    next()
  }
})

export default router

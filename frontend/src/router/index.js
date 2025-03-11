import { createRouter, createWebHistory } from 'vue-router'
import IndexPage from 'pages/IndexPage.vue'
import SignUpPage from 'pages/SignUpPage.vue'
import SignInPage from 'pages/SignInPage.vue'
import UserHome from 'pages/UserHome.vue'
import NewTranscriptionPage from 'pages/NewTranscriptionPage.vue'
import TranscriptionEdit from 'pages/TranscriptionEditPage.vue'
import TranscriptionViewPage from 'pages/TranscriptionViewPage.vue'

const routes = [
  { path: '/', component: IndexPage },
  { path: '/signup', component: SignUpPage },
  { path: '/signin', component: SignInPage },
  { path: '/home', component: UserHome, meta: { requiresAuth: true } },
  { path: '/new-transcription', name: 'new-transcription', component: NewTranscriptionPage },
  { path: '/transcription/:id', component: TranscriptionEdit },
  { path: '/transcriptionview/:id', component: TranscriptionViewPage }
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

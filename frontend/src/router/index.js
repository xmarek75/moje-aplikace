import { createRouter, createWebHistory } from 'vue-router'
import IndexPage from 'pages/IndexPage.vue'
import SignUpPage from 'pages/SignUpPage.vue'
import SignInPage from 'pages/SignInPage.vue'
import UserHome from 'pages/UserHome.vue'
import SettingsPage from 'pages/SettingsPage.vue'
import NewTranscriptionPage from 'pages/NewTranscriptionPage.vue'
import TranscriptionEdit from 'pages/TranscriptionEditPage.vue'
import TranscriptionViewPage from 'pages/TranscriptionViewPage.vue'
import SubtitleModePage from 'pages/SubtitleModePage.vue'
import TestTranscriptionEdit from 'pages/TestTranscriptionEditPage.vue'

const routes = [
  { path: '/', component: IndexPage },
  { path: '/signup', component: SignUpPage },
  { path: '/signin', component: SignInPage },
  { path: '/home', component: UserHome, meta: { requiresAuth: true } },
  { path: '/settings', component: SettingsPage, meta: { requiresAuth: true } },
  { path: '/new-transcription', name: 'new-transcription', component: NewTranscriptionPage },
  { path: '/transcription/:id', component: TranscriptionEdit },
  { path: '/transcription-test/:id', component: TestTranscriptionEdit },
  { path: '/transcriptionview/:id', component: TranscriptionViewPage },
  { path: "/subtitle-editor/:id", name: "SubtitleEditor", component: SubtitleModePage }
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

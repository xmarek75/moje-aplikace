<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated>
      <q-toolbar>
        <q-toolbar-title 
        class="clickable-title" 
        @click="goToIndexPage"
        >
          LexApp
        </q-toolbar-title>

        <!-- Uživatelské jméno a ikonka se zobrazí pouze, pokud je uživatel přihlášen -->
        <div v-if="isAuthenticated" class="row items-center">
          <span class="q-mr-md">{{ username }}</span> <!-- Uživatelské jméno -->
          <q-btn flat round icon="account_circle">
            <q-menu>
              <q-list>
                <q-item clickable v-close-popup @click="goToHome">
                  <q-item-section>Home Page</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="Settings">
                  <q-item-section>Settings</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="logout">
                  <q-item-section>Log Out</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </div>
      </q-toolbar>
    </q-header>

    <!-- Tady router vykreslí správnou stránku -->
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isAuthenticated = ref(!!localStorage.getItem('user'))
const username = ref(localStorage.getItem('user') || '')

// Funkce pro aktualizaci přihlášení a jména uživatele
const checkAuth = () => {
  isAuthenticated.value = !!localStorage.getItem('user')
  username.value = localStorage.getItem('user') || ''
}

// Přidání event listeneru pro změnu přihlášení
onMounted(() => {
  window.addEventListener('auth-changed', checkAuth)
  checkAuth() // Pro jistotu ověříme stav při načtení
})

// Odebrání listeneru při odchodu
onUnmounted(() => {
  window.removeEventListener('auth-changed', checkAuth)
})

// Funkce pro odhlášení
const logout = () => {
  localStorage.removeItem('user')
  localStorage.removeItem('token')  // Odstraníme i JWT token
  window.dispatchEvent(new Event('auth-changed')) // Spustíme event
  router.push('/signin')
}
// Funkce pro přesměrování na IndexPage
const goToIndexPage = () => {
  router.push('/')
}
// Funkce pro přesměrování na HomePage
const goToHome = () => {
  router.push('/home')
}
const Settings = () => {
  router.push('/settings')
}
</script>

<style scoped>
.clickable-title {
  cursor: pointer;
  transition: all 0.3s ease-in-out;
}

</style>
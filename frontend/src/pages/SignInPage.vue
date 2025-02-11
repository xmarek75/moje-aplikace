<template>
  <q-page :style="{ backgroundImage: `url(${backgroundImage})` }" class="signin-page">
    <div class="signin-container">
      <h2>Log In</h2>
      <q-input v-model="username" label="Username" outlined class="q-mb-md" />
      <q-input v-model="password" label="Password" type="password" outlined class="q-mb-md" />
      <q-btn label="Sign In" color="primary" @click="login" class="signin-btn" />
      <q-banner v-if="errorMessage" class="bg-red text-white q-mt-md">{{ errorMessage }}</q-banner>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from 'boot/axios'
import backgroundImage from 'src/assets/background.png'  // Dynamický import

const router = useRouter()
const username = ref('')
const password = ref('')
const errorMessage = ref('')

const login = async () => {
  try {
    const response = await api.post('/auth/login', { username: username.value, password: password.value })
    localStorage.setItem('user', response.data.username)
    localStorage.setItem('token', response.data.access_token)
    window.dispatchEvent(new Event('auth-changed'))
    router.push('/home')
  } catch (error) {
    errorMessage.value = 'Login failed!'
  }
}
</script>

<style scoped>
.signin-page {
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.signin-container {
  background: rgba(255, 255, 255, 0.2); /* Efekt průhlednosti */
  padding: 2rem;
  border-radius: 10px;
  backdrop-filter: blur(10px);
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
  text-align: center;
  max-width: 400px;
  width: 100%;
}

.signin-title {
  font-size: 2rem;
  font-weight: bold;
  color: white;
  margin-bottom: 1.5rem;
}

.signin-btn {
  width: 100%;
  font-size: 1.2rem;
  margin-top: 1rem;
}
</style>

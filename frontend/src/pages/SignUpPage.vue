<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from 'boot/axios'
import backgroundImage from 'src/assets/background.png'  // Dynamický import
import SignInPage from './SignInPage.vue'


const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')
const errorMessage = ref('')

const register = async () => {
  try {
    await api.post('/users/', { 
      username: username.value, 
      email: email.value,  
      password: password.value 
    })
    
    try {
    const response = await api.post('/auth/login', { username: username.value, password: password.value })
    localStorage.setItem('user', response.data.username)
    localStorage.setItem('token', response.data.access_token)
    localStorage.setItem("refresh_token", response.data.refresh_token);
    window.dispatchEvent(new Event('auth-changed'))
    router.push('/home')
  } catch (error) {
    errorMessage.value = 'Login failed!'
  }
    
  } catch (error) {
    errorMessage.value = 'Registration failed!'
  }
}
</script>

<template>
  <q-page :style="{ backgroundImage: `url(${backgroundImage})` }" class="signup-page">
    <div class="signup-container">
      <h2>Register</h2>
      <q-input v-model="username" label="Username" outlined class="q-mb-md" />
      <q-input v-model="email" label="E-mail" type="email" outlined class="q-mb-md" />
      <q-input v-model="password" label="Password" type="password" outlined class="q-mb-md" />
      <q-btn label="Sign Up" color="primary" @click="register" />
      <q-banner v-if="errorMessage" class="bg-red text-white q-mt-md">{{ errorMessage }}</q-banner>
    </div>
  </q-page>
</template>

<style scoped>
.signup-page {
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.signup-container {
  background: rgba(255, 255, 255, 0.2); /* Efekt průhlednosti */
  padding: 2rem;
  border-radius: 10px;
  backdrop-filter: blur(10px);
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
  text-align: center;
  max-width: 400px;
  width: 100%;
}
</style>

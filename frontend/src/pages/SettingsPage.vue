<template>
  <q-page class="q-pa-md">
    <q-card class="q-pa-lg" style="max-width: 600px; margin: auto;">
      <q-card-section>
        <div class="text-h5">⚙️ Account Settings</div>
      </q-card-section>

      <q-separator class="q-my-sm" />

      <!-- Zobrazit aktuální username -->
      <q-card-section>
        <div class="row items-center justify-between">
          <div><strong>Username:</strong> {{ currentUsername }}</div>
          <q-btn flat dense color="primary" label="Change" @click="usernameDialog = true" />
        </div>
      </q-card-section>

      <!-- Zobrazit aktuální email -->
      <q-card-section>
        <div class="row items-center justify-between">
          <div><strong>Email:</strong> {{ currentEmail }}</div>
          <q-btn flat dense color="primary" label="Change" @click="emailDialog = true" />
        </div>
      </q-card-section>

      <q-card-section>
        <q-btn color="primary" label="Change Password" @click="passwordDialog = true" />
      </q-card-section>
    </q-card>

    <!-- 🔹 Dialog pro změnu username -->
    <q-dialog v-model="usernameDialog">
      <q-card class="q-pa-md" style="min-width: 300px">
        <q-card-section>
          <div class="text-h6">Change Username</div>
        </q-card-section>

        <q-card-section>
          <q-input v-model="newUsername" label="New Username" filled />
          <q-input v-model="usernamePassword" label="Password" type="password" filled class="q-mt-md" />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn color="primary" label="Save and logout" @click="changeUsername" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- 🔹 Dialog pro změnu emailu -->
    <q-dialog v-model="emailDialog">
      <q-card class="q-pa-md" style="min-width: 300px">
        <q-card-section>
          <div class="text-h6">Change Email</div>
        </q-card-section>

        <q-card-section>
          <q-input v-model="newEmail" label="New Email" type="email" filled />
          <q-input v-model="emailPassword" label="Password" type="password" filled class="q-mt-md" />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn color="primary" label="Save" @click="changeEmail" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- 🔹 Dialog pro změnu hesla -->
    <q-dialog v-model="passwordDialog">
      <q-card class="q-pa-md" style="min-width: 300px">
        <q-card-section>
          <div class="text-h6">Change Password</div>
        </q-card-section>

        <q-card-section>
          <q-input v-model="oldPassword" label="Current Password" type="password" filled />
          <q-input v-model="newPassword" label="New Password" type="password" filled class="q-mt-md" />
          <q-input v-model="confirmPassword" label="Confirm New Password" type="password" filled class="q-mt-md" />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn color="primary" label="Save" @click="changePassword" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'

const router = useRouter()
const $q = useQuasar()

const currentUsername = ref(localStorage.getItem('user') || '')
const currentEmail = ref('')

const usernameDialog = ref(false)
const emailDialog = ref(false)
const passwordDialog = ref(false)

// Inputy pro formuláře
const newUsername = ref('')
const usernamePassword = ref('')

const newEmail = ref('')
const emailPassword = ref('')

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

// ✅ Načtení aktuálního uživatele
const fetchCurrentUser = async () => {
  try {
    const res = await api.get('/users/me', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    })
    currentUsername.value = res.data.username
    currentEmail.value = res.data.email
  } catch (err) {
    console.error("❌ Chyba při načítání uživatele:", err)
  }
}

// ✅ Změna uživatelského jména
const changeUsername = async () => {
  try {
    await api.put('/users/settings', {
      username: newUsername.value,
      password: usernamePassword.value
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })

    $q.notify({ type: 'positive', message: 'Username updated successfully.' })
    currentUsername.value = newUsername.value
    localStorage.setItem('user', newUsername.value)
    usernameDialog.value = false
  } catch (err) {
    $q.notify({ type: 'negative', message: 'Failed to update username.' })
    console.error(err)
  }
  logout()
}

// ✅ Změna e-mailu
const changeEmail = async () => {
  try {
    await api.put('/users/settings', {
      email: newEmail.value,
      password: emailPassword.value
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })

    $q.notify({ type: 'positive', message: 'Email updated successfully.' })
    currentEmail.value = newEmail.value
    emailDialog.value = false
  } catch (err) {
    $q.notify({ type: 'negative', message: 'Failed to update email.' })
    console.error(err)
  }
}

// ✅ Změna hesla
const changePassword = async () => {
  if (newPassword.value !== confirmPassword.value) {
    $q.notify({ type: 'negative', message: 'New passwords do not match.' })
    return
  }

  try {
    await api.put('/users/settings', {
      password: newPassword.value,
      old_password: oldPassword.value
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })

    $q.notify({ type: 'positive', message: 'Password changed successfully.' })
    passwordDialog.value = false
  } catch (err) {
    $q.notify({ type: 'negative', message: 'Failed to change password.' })
    console.error(err)
  }
}
const logout = () => {
  localStorage.removeItem('user')
  localStorage.removeItem('token')  // Odstraníme i JWT token
  window.dispatchEvent(new Event('auth-changed')) // Spustíme event
  router.push('/signin')
}

onMounted(() => {
  fetchCurrentUser()
})
</script>

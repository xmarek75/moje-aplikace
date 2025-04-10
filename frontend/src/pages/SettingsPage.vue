<template>
  <q-page class="q-pa-md">
    <q-card class="q-pa-lg" style="max-width: 600px; margin: auto;">
      <q-card-section>
        <div class="text-h6">Account Settings</div>
      </q-card-section>

      <q-separator />

      <q-card-section>
        <q-input v-model="username" label="Username" filled />
        <q-input v-model="email" label="Email" type="email" filled class="q-mt-md" />
        <q-input v-model="password" label="New Password" type="password" filled class="q-mt-md" />
        <q-input v-model="confirmPassword" label="Confirm Password" type="password" filled class="q-mt-md" />
      </q-card-section>

      <q-card-actions align="right">
        <q-btn label="Save Changes" color="primary" @click="updateAccount" />
      </q-card-actions>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const $q = useQuasar()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')

const updateAccount = async () => {
  if (password.value && password.value !== confirmPassword.value) {
    $q.notify({ type: 'negative', message: 'Passwords do not match.' })
    return
  }

  try {
    await api.put('/users/settings', {
      username: username.value,
      email: email.value,
      password: password.value || undefined
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    })

    $q.notify({ type: 'positive', message: 'Account updated successfully.' })
  } catch (err) {
    console.error(err)
    $q.notify({ type: 'negative', message: 'Failed to update account.' })
  }
}
</script>

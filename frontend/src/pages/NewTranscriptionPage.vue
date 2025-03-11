<template>
  <q-page class="flex flex-center">
    <div class="upload-container">
      <h3 v-if="step === 1">Choose files to transcribe</h3>
      <h3 v-if="step === 2">Choose model & Upload</h3>

      <!-- Krok 1: Nahrání souborů -->
      <div v-if="step === 1">
        <q-file v-model="files" label="Upload files" multiple outlined class="q-mb-md" />
        <q-btn label="Next" color="primary" @click="step = 2" :disable="files.length === 0" />
      </div>

      <!-- Krok 2: Výběr modelu + Upload -->
      <div v-if="step === 2">
        <q-option-group
          v-model="selectedModel"
          :options="models"
          type="radio"
          class="q-mb-md"
        />
        <q-btn label="Back" color="secondary" @click="step = 1" class="q-mr-md" />
        <q-btn label="Upload" color="primary" @click="saveToDatabase" :disable="!selectedModel || uploading" />
      </div>

      <!-- Indikátor nahrávání -->
      <div v-if="uploading">
        <p>Uploading and processing files...</p>
        <q-spinner size="50px" color="primary" class="q-mb-md" />
      </div>

      <!-- Chybová hláška -->
      <q-banner v-if="errorMessage" class="bg-red text-white q-mt-md">{{ errorMessage }}</q-banner>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from 'boot/axios'

const router = useRouter()
const step = ref(1)
const files = ref([])
const selectedModel = ref(null)
const uploading = ref(false)
const errorMessage = ref("")

const models = [
  { label: 'Model A', value: 'model_a' },
  { label: 'Model B', value: 'model_b' },
  { label: 'Model C', value: 'model_c' }
]

const saveToDatabase = async () => {
  try {
    uploading.value = true;
    const token = localStorage.getItem('token');
    if (!token) {
      errorMessage.value = "No token found, user might not be logged in.";
      return;
    }

    for (const file of files.value) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('model', selectedModel.value);

      const response = await api.post('/upload', formData, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' }
      });

      if (!response.data.id) {
        errorMessage.value = "Failed to upload file.";
        return;
      }

      await api.post('/transcriptions/', {
        media_id: response.data.id,
        text: '',
        model: selectedModel.value,
        progress: 0.0
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
    }

    uploading.value = false;
    router.push('/home');  // ✅ Přesměrování na homepage po uploadu
  } catch (error) {
    uploading.value = false;
    errorMessage.value = 'Error uploading and saving files: ' + (error.response?.data?.detail || error.message);
    console.error(errorMessage.value);
  }
}
</script>

<style scoped>
.upload-container {
  background: rgba(255, 255, 255, 0.2);
  padding: 2rem;
  border-radius: 10px;
  backdrop-filter: blur(10px);
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
  text-align: center;
  max-width: 400px;
  width: 100%;
}
</style>

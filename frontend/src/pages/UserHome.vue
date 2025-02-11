<template>
  <q-layout view="hHh lpR fFf">
    <!-- Levé menu -->
    <q-drawer show-if-above v-model="drawer" side="left" bordered>
      <q-list>
        <q-item-label header>
          <q-btn class="add-btn" label="Add" icon="add">
            <q-menu>
              <q-list>
                <q-item clickable v-close-popup @click="createNew('transcription')">
                  <q-item-section>New Transcription</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="createNew('folder')">
                  <q-item-section>New Folder</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </q-item-label>
        <q-item clickable v-ripple @click="selectedTab = 'myTranscriptions'">
          <q-item-section>My Transcriptions</q-item-section>
        </q-item>
        <q-item clickable v-ripple @click="selectedTab = 'folders'">
          <q-item-section>Folders</q-item-section>
        </q-item>
        <q-item clickable v-ripple @click="selectedTab = 'transcribing'">
          <q-item-section>Transcribing</q-item-section>
        </q-item>
        <q-item clickable v-ripple @click="selectedTab = 'sharedWithMe'">
          <q-item-section>Shared with Me</q-item-section>
        </q-item>
        <q-item clickable v-ripple @click="selectedTab = 'trash'">
          <q-item-section>Trash</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <!-- Obsah stránky -->
    <q-page-container>
      <q-page padding>
        <div v-if="selectedTab === 'myTranscriptions'">
          <h2>My Transcriptions</h2>
          <q-table
            flat bordered
            :rows="transcriptions"
            :columns="columns"
            row-key="id"
          />
        </div>
        <div v-if="selectedTab === 'folders'">
          <h2>Folders</h2>
          <p>folders TODO</p>
        </div>
        <div v-if="selectedTab === 'transcribing'">
          <h2>Transcribing</h2>
          <p>Trasncribing TODO</p>
        </div>
        <div v-if="selectedTab === 'sharedWithMe'">
          <h2>Shared with Me</h2>
          <p>Shared with Me TODO</p>
        </div>
        <div v-if="selectedTab === 'trash'">
          <h2>Trash</h2>
          <p>Deleted transcriptions TODO</p>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'

const drawer = ref(true)
const selectedTab = ref('myTranscriptions')
const transcriptions = ref([])

const columns = [
  { name: 'name', required: true, label: 'Name', align: 'left', field: row => row.video.title },
  { name: 'created', label: 'Created', align: 'left', field: row => new Date(row.created_at).toLocaleDateString() },
  { name: 'updated', label: 'Last Update', align: 'left', field: row => new Date(row.updated_at).toLocaleDateString() },
  { name: 'owner', label: 'Owner', align: 'left', field: row => row.owner.username },
  { name: 'status', label: 'Status', align: 'left', field: row => `${row.progress}%` }
]

// Načtení transkripcí při spuštění
const fetchTranscriptions = async () => {
  try {
    const token = localStorage.getItem('token');  // Načtení tokenu z localStorage
    if (!token) {
      console.error("No token found, user might not be logged in.");
      return;
    }

    const response = await api.get('/transcriptions/my', {
      headers: { Authorization: `Bearer ${token}` }
    });

    transcriptions.value = response.data;
  } catch (error) {
    console.error('Error loading transcriptions:', error);
  }
};

onMounted(() => {
  if (selectedTab.value === 'myTranscriptions') {
    fetchTranscriptions();
  }
});
</script>

<style scoped>
.q-item {
  cursor: pointer;
}

.add-btn {
  background-color: #1976d2; /* Modrá barva tlačítka */
  color: white;
  border-radius: 8px; /* Lehce zaoblené hrany */
  padding: 8px 16px;
}

.add-btn:hover {
  background-color: #1565c0; /* Tmavší modrá při najetí myší */
}
</style>

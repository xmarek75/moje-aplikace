<template>
  <q-layout view="hHh lpR fFf">
    <!-- Levé menu -->
    <q-drawer show-if-above v-model="drawer" side="left" bordered>
      <q-list>
        <q-item-label header>
          <q-btn class="add-btn" label="Add" icon="add">
            <q-menu>
              <q-list>
                <q-item clickable v-close-popup @click="navigateTo('/new-transcription')">
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
          <h3>My Transcriptions</h3>
          <q-table
            flat bordered
            :rows="transcriptions"
            :columns="columns"
            row-key="id"
            :pagination="{ sortBy: 'updated', descending: true, rowsPerPage: 15 }"
          >
            <template v-slot:body="props">
              <q-tr :props="props">
                <q-td v-for="col in columns" :key="col.name" @dblclick="router.push(`/transcription/${props.row.id}`)">
                  {{ col.field(props.row) }}
                </q-td>
                <!-- Sloupec pro menu -->
                <q-td>
                  <q-btn dense flat round icon="more_vert">
                    <q-menu>
                      <q-list>
                        <q-item clickable v-close-popup @click="router.push(`/transcription/${props.row.id}`)">
                          <q-item-section>📂 Open</q-item-section>
                        </q-item>
                        <q-item clickable v-close-popup @click="downloadTranscription(props.row)">
                          <q-item-section>⬇️ Download</q-item-section>
                        </q-item>
                        <q-item clickable v-close-popup @click="showRenameDialog(props.row)">
                          <q-item-section>✏️ Rename</q-item-section>
                        </q-item>
                        <q-item clickable v-close-popup @click="deleteTranscription(props.row.id)">
                          <q-item-section class="text-red">🗑️ Delete</q-item-section>
                        </q-item>
                      </q-list>
                    </q-menu>
                  </q-btn>
                </q-td>
              </q-tr>
            </template>
          </q-table>
        </div>
      </q-page>
    </q-page-container>
    <!-- Dialog pro přejmenování -->
    <q-dialog v-model="renameDialogVisible">
      <q-card class="rename-card">
        <q-card-section>
          <h5 class="rename-title">Rename Transcription</h5>
          <q-input v-model="newTitle" label="New Name" autofocus />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn label="Cancel" color="negative" flat @click="renameDialogVisible = false" />
          <q-btn label="Save" color="primary" @click="renameMedia" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { useRouter } from 'vue-router' 

const drawer = ref(true)
const selectedTab = ref('myTranscriptions')
const transcriptions = ref([])
const selectedTranscriptionId = ref(null)
const contextMenuVisible = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const router = useRouter()

const selectedMedia = ref(null); // ✅ Musí být definováno
const renameDialogVisible = ref(false);  // ✅ Správná vazba na dialog
const newTitle = ref(""); // ✅ Uchovává nový název

const columns = [
  { name: 'name', required: true, label: 'Name', align: 'left', field: row => row.media.title, sortable: true },
  { name: 'created', label: 'Created', align: 'left', field: row => formatDateTime(row.created_at), sortable: true },
  { name: 'updated', label: 'Last Update', align: 'left', field: row => formatDateTime(row.updated_at), sortable: true },
  { name: 'owner', label: 'Owner', align: 'left', field: row => row.owner.username },
  { name: 'status', label: 'Status', align: 'left', field: row => `${row.progress}%` }
]

// Navigace na novou stránku
const navigateTo = (route) => {
  router.push(route)
}

// Načtení transkripcí při spuštění
const fetchTranscriptions = async () => {
  try {
    const token = localStorage.getItem('token');  
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



// Funkce pro zobrazení kontextového menu na správném místě
const showContextMenu = (event, row) => {
  selectedTranscriptionId.value = row.id;
  
  contextMenuX.value = event.clientX; // X souřadnice myši
  contextMenuY.value = event.clientY; // Y souřadnice myši
  contextMenuVisible.value = true;
}

// Funkce pro smazání transkripce
const deleteTranscription = async (id) => {
  try {
    await api.delete(`/transcriptions/${id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    });

    // Aktualizace UI - odstranění z tabulky
    transcriptions.value = transcriptions.value.filter(t => t.id !== id)
  } catch (error) {
    console.error("Chyba při mazání transkripce:", error);
  }
}

onMounted(() => {
  if (selectedTab.value === 'myTranscriptions') {
    fetchTranscriptions();
  }
});

// Formátování data
const formatDateTime = (dateString) => {
  const date = new Date(dateString);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());

  return date.toLocaleString(); // Zjednodušeno pomocí `toLocaleString()`
}

// ✅ Zobrazení dialogu pro přejmenování
const showRenameDialog = (row) => {
  selectedMedia.value = row.media;
  newTitle.value = row.media.title;
  renameDialogVisible.value = true;
};

// ✅ Odeslání změny názvu media na server
const renameMedia = async () => {
  if (!selectedMedia.value) return;

  try {
    await api.put(`/media/${selectedMedia.value.id}/rename`, 
      { title: newTitle.value },
      { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
    );

    // ✅ Aktualizace UI
    selectedMedia.value.title = newTitle.value;
    renameDialogVisible.value = false;
  } catch (error) {
    console.error("Chyba při přejmenování média:", error);
  }
};


</script>

<style scoped>
.q-item {
  cursor: pointer;
}

.add-btn {
  background-color: #1976d2;
  color: white;
  border-radius: 8px;
  padding: 8px 16px;
}

.add-btn:hover {
  background-color: #1565c0;
}

/* Oprava pozice kontextového menu */
.q-menu {
  position: fixed !important;
}

/* 🔹 Styling pop-up okna */
.rename-card {
  width: 400px;
  padding: 20px;
}
.rename-title {
  font-size: 1.2rem;
  font-weight: bold;
  color: #1976d2;
}
</style>

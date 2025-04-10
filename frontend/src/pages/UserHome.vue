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
                <q-item clickable v-close-popup @click="showFolderDialog('folder')">
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
          <h4>My Transcriptions</h4>
          <q-table
            flat
            bordered
            :rows="transcriptions"
            :columns="columns"
            row-key="id"
            :pagination="{ sortBy: 'updated', descending: true, rowsPerPage: 15 }"
          >
            <!-- ⚠️ Vlastní hlavička pro checkbox -->
            <template v-slot:header="props">
              <q-tr :props="props">
                <q-th auto-width>
                  <q-btn
                  dense
                  size="sm"
                  label=""
                  color="primary"
                  icon="more_vert"
                  :disable="selectedIds.length === 0"
                >
                  <q-menu>
                    <q-list dense>
                      <q-item clickable v-close-popup @click="moveSelectedToTrash">
                        <q-item-section>🗑️ Move to trash</q-item-section>
                      </q-item>
                      <q-item clickable v-close-popup @click="markAsFinished">
                        <q-item-section>✅ Mark as Finished</q-item-section>
                      </q-item>
                      <q-item clickable v-close-popup @click="unMarked">
                        <q-item-section>↩️ Unmark</q-item-section>
                      </q-item>
                    </q-list>
                  </q-menu>
                </q-btn>
                </q-th> <!-- checkbox sloupec -->
                <q-th v-for="col in props.cols" :key="col.name" :props="props">
                  {{ col.label }}
                </q-th>
              </q-tr>
            </template>
            <template v-slot:body="props">
              <q-tr 
              :props="props"
              :class="{ 'finished-row': props.row.status_flag === 2 }"
              >
                <q-td>
                  <q-checkbox
                    v-model="selectedIds"
                    :val="props.row.id"
                    size="sm"
                  />
                </q-td>
                <q-td
                  v-for="col in columns"
                  :key="col.name"
                  @dblclick="openTranscription(props.row)"
                >
                  {{ col.field(props.row) }}
                </q-td>
                <q-td>
                  <!-- akce pro jeden řádek -->
                  <q-btn dense flat round icon="more_vert">
                    <q-menu>
                      <q-list>
                        <q-item clickable v-close-popup @click="router.push(`/transcription-test/${props.row.id}`)">
                          <q-item-section>📂 Open</q-item-section>
                        </q-item>
                        <q-item clickable v-close-popup @click="downloadTranscription(props.row)">
                          <q-item-section>⬇️ Download</q-item-section>
                        </q-item>
                        <q-item clickable v-close-popup @click="showRenameDialog(props.row)">
                          <q-item-section>✏️ Rename</q-item-section>
                        </q-item>
                        <q-item clickable v-close-popup @click="showShareDialog(props.row)">
                          <q-item-section>Share</q-item-section>
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
        <div v-else-if="selectedTab === 'sharedWithMe'">
          <div class="row items-center justify-between q-mb-md q-pt-md">
            <div class="text-h6 text-primary">
              <q-icon name="people" class="q-mr-sm" />
              Shared With Me
            </div>
          </div>
          <q-table
            flat bordered
            :rows="sharedTranscriptions"
            :columns="columnsShared"
            row-key="id"
            :pagination="{ sortBy: 'updated', descending: true, rowsPerPage: 15 }"
          >
            <template v-slot:body="props">
              <q-tr :props="props">
                <q-td v-for="col in columnsShared" :key="col.name" @dblclick="openTranscription(props.row)">
                  {{ col.field(props.row) }}
                </q-td>
              </q-tr>
            </template>
          </q-table>
        </div>
          <div v-if="selectedTab === 'folders'">
            <div class="row items-center justify-between q-mb-md q-pt-md ">
              <div class="text-h6 text-primary">
                <q-icon name="folder" class="q-mr-sm" />
                Folders</div>
              <q-btn 
                label="New Folder" 
                icon="create_new_folder" 
                color="primary" 
                @click="showFolderDialog('folder')" 
              />
            </div>
            <q-table
              :rows="folders"
              :columns="columnsFolders"
              row-key="folder"
            >
              <template v-slot:body="props">
                <q-tr :props="props" @dblclick="openFolder(props.row.folder)">
                  <q-td v-for="col in columnsFolders" :key="col.name">
                    {{ col.field(props.row) }}
                  </q-td>
                </q-tr>
              </template>
            </q-table>
          </div>
        <div v-if="selectedTab === 'folderContents'">
          <div class="row items-center text-primary text-h6 q-mb-md q-pt-md">
            <q-icon name="folder" class="q-mr-sm cursor-pointer" @click="selectedTab = 'folders'"/>
            <div class="q-mr-sm cursor-pointer" @click="selectedTab = 'folders'">Folder:</div>
            <div class="text-weight-regular">{{ selectedFolder }}</div>
            <q-btn flat dense round icon="edit" size="sm" @click="showRenameFolderDialog" />
          </div>
          <q-table
            flat bordered
            :rows="folderTranscriptions"
            :columns="columns"
            row-key="id"
            :pagination="{ sortBy: 'updated', descending: true, rowsPerPage: 15 }"
          >
            <template v-slot:body="props">
              <q-tr :props="props">
                <q-td
                  v-for="col in columns"
                  :key="col.name"
                  @dblclick="openTranscription(props.row)"
                >
                  {{ col.field(props.row) }}
                </q-td>
              </q-tr>
            </template>
          </q-table>
          <q-btn
            flat
            icon="arrow_back"
            label="Back to Folders"
            @click="selectedTab = 'folders'"
            class="q-mt-md"
          />
        </div>
        <div v-if="selectedTab === 'trash'">
          <div class="row items-center justify-between q-mb-md q-pt-md" @click="showEmptyTrashDialog = true">
            <div class="text-h6 text-primary">
              <q-icon name="delete" class="q-mr-sm" />
              Trash
            </div>
          </div>
          <q-table
            flat
            bordered
            :rows="trashedTranscriptions"
            :columns="columnsDeleted"
            row-key="id"
            :pagination="{ sortBy: 'updated', descending: true, rowsPerPage: 15 }"
          >
            <!-- ⚠️ Vlastní hlavička pro checkbox -->
            <template v-slot:header="props">
              <q-tr :props="props">
                <q-th auto-width>
                  <q-btn
                  dense
                  size="sm"
                  label=""
                  color="primary"
                  icon="more_vert"
                  :disable="selectedDeletedIds.length === 0"
                >
                  <q-menu>
                    <q-list dense>
                      <q-item clickable v-close-popup @click="restoreSelected">
                        <q-item-section>♻️ Restore Selected</q-item-section>
                      </q-item>
                      <q-item clickable v-close-popup @click="permanentlyDeleteSelected">
                        <q-item-section class="text-red">🗑️ Permanently Delete</q-item-section>
                      </q-item>
                    </q-list>
                  </q-menu>
                </q-btn>
                  </q-th> <!-- checkbox sloupec -->
                <q-th v-for="col in props.cols" :key="col.name" :props="props">
                  {{ col.label }}
                </q-th>
              </q-tr>
            </template>
            <template v-slot:body="props">
              <q-tr :props="props">
                <q-td>
                  <q-checkbox
                    v-model="selectedDeletedIds"
                    :val="props.row.id"
                    size="sm"
                  />
                </q-td>
                <q-td
                  v-for="col in columnsDeleted"
                  :key="col.name"
                  @dblclick="openTranscription(props.row)"
                >
                  {{ col.field(props.row) }}
                </q-td>
              </q-tr>
            </template>
          </q-table>
        </div>
        <div v-if="selectedTab === 'transcribing'">
          <h5>Transcribing</h5>
          <q-table
            flat
            bordered
            :rows="transcribingTranscriptions"
            :columns="columns"
            row-key="id"
            :pagination="{ sortBy: 'updated', descending: true, rowsPerPage: 15 }"
          >
            <template v-slot:body="props">
              <q-tr :props="props">
                <q-td v-for="col in columns" :key="col.name">
                  {{ col.field(props.row) }}
                </q-td>
              </q-tr>
            </template>
          </q-table>
        </div>
      </q-page>
    </q-page-container>
    <!-- Dialog pro přejmenování prepisu-->
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
    <!-- Dialog pro přejmenování slozky-->
    <q-dialog v-model="renameFolderDialogVisible">
      <q-card class="rename-card">
        <q-card-section>
          <h5 class="rename-title">Rename Folder</h5>
          <q-input v-model="newFolderName" label="New Folder Name" autofocus />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="negative" @click="renameFolderDialogVisible = false" />
          <q-btn flat label="Save" color="primary" @click="renameFolder" />
        </q-card-actions>
      </q-card>
    </q-dialog>
    <!-- Dialog pro sdilení -->
    <q-dialog v-model="shareDialogVisible">
      <q-card class="rename-card">
        <q-card-section>
          <h5 class="rename-title">Share Transcription</h5>
          <q-input 
            v-model="searchQuery" 
            label="Search user by name or email" 
            debounce="300" 
            @update:model-value="searchUsers" 
            clearable
            autofocus
          />
          <q-list bordered separator class="q-mt-md">
            <q-item 
              v-for="user in userResults" 
              :key="user.id" 
              clickable 
              @click="selectedUser = user"
              :active="selectedUser && selectedUser.id === user.id"
              active-class="bg-primary text-white"
            >
              <q-item-section>{{ user.username }} ({{ user.email }})</q-item-section>
            </q-item>
          </q-list>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="negative" @click="shareDialogVisible = false" />
          <q-btn 
            label="Share" 
            color="primary" 
            :disable="!selectedUser" 
            @click="shareWithUser" 
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
    <!-- Dialog pro vytvoreni slozky -->
    <q-dialog v-model="createFolderDialog">
      <q-card class="rename-card">
        <q-card-section>
          <h5 class="rename-title">Create new folder</h5>
          <q-input v-model="newFolderName" label="Folder Name" autofocus />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="negative" @click="createFolderDialog = false" />
          <q-btn 
            label="Create" 
            color="primary" 
            :disable="!newFolderName" 
            @click="submitNewFolder" 
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
    <q-dialog v-model="showEmptyTrashDialog">
      <q-card>
        <q-card-section>
          <div class="text-h6">Are you sure you want to permanently delete all trashed transcriptions?</div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn label="Yes, Delete All" color="negative" @click="emptyTrash" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-layout>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { api } from 'boot/axios'
import { useRouter } from 'vue-router' 
import { useQuasar } from 'quasar'

const $q = useQuasar()
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
//zobrazeni slozek
const folders = ref([])
//otevreni slozek
const selectedFolder = ref(null)
const folderTranscriptions = ref([])

//sdileni prepisu global
const shareDialogVisible = ref(false);
const searchQuery = ref("");
const userResults = ref([]);
const selectedUser = ref(null);
const transcriptionToShare = ref(null);
const sharedTranscriptions = ref([])//pro fetch

//vytvoreni nove slozky
const createFolderDialog = ref(false)
const newFolderName = ref("")
//prejmenovani slozky
const renameFolderDialogVisible = ref(false)
const newRenamedFolderName = ref("")
//hromadny vyber
const selectedIds = ref([]) 
//hromadny vyber v kosi
const selectedDeletedIds = ref([])
const showEmptyTrashDialog = ref(false)
//smazane polozky
const trashedTranscriptions = ref([])
//polling interval, pro aktualizaci progresu u prepisujicich prepisu
const pollingActive = ref(false)
let pollingInterval = null;
//zrovna prepisujici 
const transcribingTranscriptions = ref([])

const columns = [
  { name: 'name', required: true, label: 'Name', align: 'left', field: row => row.media.title, sortable: true },
  { name: 'created', label: 'Created', align: 'left', field: row => formatDateTime(row.created_at), sortable: true },
  { name: 'updated', label: 'Last Update', align: 'left', field: row => formatDateTime(row.updated_at), sortable: true },
  { name: 'owner', label: 'Owner', align: 'left', field: row => row.owner.username },
  { name: 'status', label: 'Status', align: 'left', field: row => `${row.progress}%` }
]
const columnsShared = [
  { name: 'title', label: 'Name', align: 'left', field: r => r.title ?? '[No Title]', sortable: true },
  { name: 'owner', label: 'Owner', align: 'left', field: r => r.owner ?? '[Unknown]', sortable: true },
  { name: 'created', label: 'Created', align: 'left', field: r => formatDateTime(r.created_at), sortable: true },
  { name: 'updated', label: 'Last Update', align: 'left', field: r => formatDateTime(r.updated_at), sortable: true }
]
const columnsFolders = [
  { name: 'folder', label: 'Folder', align: 'left', field: row => row.folder, sortable: true },
  { name: 'created', label: 'Created', align: 'left', field: row => formatDateTime(row.created), sortable: true },
  { name: 'last_update', label: 'Last Update', align: 'left', field: row => formatDateTime(row.last_update), sortable: true },
  { name: 'count', label: 'Transcriptions', align: 'left', field: row => row.count, sortable: true }
]
const columnsDeleted = [
  { name: 'name', label: 'Name', field: row => row.media?.title ?? '[No Title]', sortable: true, align: 'left' },
  { name: 'deleted_at', label: 'Deleted At', field: row => row.deleted_at ? formatDateTime(row.deleted_at) : '[No Date]', sortable: true, align: 'left' }
]

// Navigace na novou stránku
const navigateTo = (route) => {
  router.push(route)
}
//otevreni prepisu
const openTranscription = (row) => {
  if (row.progress < 100) {
    $q.notify({
      type: 'warning',
      message: 'Transcription is not yet ready to be opened.',
      timeout: 2000
    })
    return
  }
  router.push(`/transcription/${row.id}`)
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

    const anyInProgress = transcriptions.value.some(t => t.progress < 100)
    if (anyInProgress && !pollingActive.value) {
      startPolling()
    }

  } catch (error) {
    console.error('Error loading transcriptions:', error);
  }
};
//nacteni sdilenych prepisu
const fetchSharedTranscriptions = async () => {
  try {
    const token = localStorage.getItem('token');  
    if (!token) {
      console.error("Token not found.");
      return;}
    const response = await api.get('/transcriptions/shared', {
      headers: { Authorization: `Bearer ${token}` }
    });
    sharedTranscriptions.value = response.data;
  } catch (error) {
    console.error('Error loading shared transcriptions:', error);
  }
};
//nacteni slozek
const fetchFolders = async () => {
  try {
    const token = localStorage.getItem("token");
    const response = await api.get("/folders", {
      headers: { Authorization: `Bearer ${token}` }
    });
    folders.value = response.data;
  } catch (error) {
    console.error("Chyba při načítání složek:", error);
  }
}
//nacteni smazanych prepisu
const fetchTrash = async () => {
  try {
    const token = localStorage.getItem("token");
    const response = await api.get("/transcriptions/fetch/trash", {
      headers: { Authorization: `Bearer ${token}` }
    });
    trashedTranscriptions.value = response.data;
  } catch (error) {
    console.error("Chyba při načítání smazaných přepisů:", error);
  }
};
//nacteni prepisujicich prepisu
const fetchTranscribingTranscriptions = async () => {
  try {
    const token = localStorage.getItem("token")
    const response = await api.get("/transcribing", {
      headers: { Authorization: `Bearer ${token}` }
    })
    transcribingTranscriptions.value = response.data
  } catch (err) {
    console.error("Chyba při načítání transcribing přepisů:", err)
  }
}
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
  } else if (selectedTab.value === 'sharedWithMe') {
    fetchSharedTranscriptions();
  } else if (selectedTab.value === 'folders') {
    fetchFolders();
  }
});
watch(selectedTab, (newVal) => {
  if (newVal === 'myTranscriptions') {
    fetchTranscriptions();
  } else if (newVal === 'sharedWithMe') {
    fetchSharedTranscriptions();
  } else if (newVal === 'folders') {
    fetchFolders();
  } else if (newVal === 'trash') {
  fetchTrash();
  } else if (newVal === 'transcribing') {
    fetchTranscribingTranscriptions()
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
// Otevře share dialog
const showShareDialog = (row) => {
  transcriptionToShare.value = row;
  shareDialogVisible.value = true;
  searchQuery.value = "";
  userResults.value = [];
  selectedUser.value = null;
};
// Vyhledání uživatelů
const searchUsers = async () => {
  try {
    const response = await api.get(`/users/search?query=${searchQuery.value}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });
    userResults.value = response.data;
  } catch (error) {
    console.error("Chyba při hledání uživatelů:", error);
  }
};

// Odeslání sdílení
const shareWithUser = async () => {
  if (!selectedUser.value || !transcriptionToShare.value) return;

  try {
    await api.post(`/transcriptions/${transcriptionToShare.value.id}/share`, {
      target_user_id: selectedUser.value.id
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });

    shareDialogVisible.value = false;
  } catch (error) {
    console.error("Chyba při sdílení přepisu:", error);
  }
};
//otevreni slozky a nacteni prepisu
const openFolder = async (folder) => {
  selectedFolder.value = folder
  selectedTab.value = 'folderContents'
  try {
    const token = localStorage.getItem('token')
    const response = await api.get(`/transcriptions/by-folder/${encodeURIComponent(folder)}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    folderTranscriptions.value = response.data
  } catch (error) {
    console.error('Chyba při načítání přepisů ve složce:', error)
  }
}
//otevre folder dialog
const showFolderDialog = (type) => {
  if (type === 'folder') {
    newFolderName.value = ""
    createFolderDialog.value = true
  }
}
const submitNewFolder = async () => {
  try {
    const token = localStorage.getItem("token")
    await api.post("/folders", { folder: newFolderName.value }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    createFolderDialog.value = false
    fetchFolders() // refresh po vytvoření
  } catch (err) {
    console.error("Chyba při vytváření složky:", err)
  }
}
//otevre folder dialog pro prejmenovani uz vytvoreneho folderu
const showRenameFolderDialog = () => {
  newFolderName.value = selectedFolder.value
  renameFolderDialogVisible.value = true
}
//prejmenovani folderu
const renameFolder = async () => {
  try {
    const token = localStorage.getItem("token")
    await api.put(`/folders/rename`, {
      old_name: selectedFolder.value,
      new_name: newFolderName.value
    }, {
      headers: { Authorization: `Bearer ${token}` }
    })

    renameFolderDialogVisible.value = false
    fetchFolders() // znovunačti složky
    selectedFolder.value = newFolderName.value // aktualizuj aktuální složku
  } catch (err) {
    console.error("Chyba při přejmenování složky:", err)
  }
}
//presun do kose
const moveSelectedToTrash = async () => {
  if (selectedIds.value.length === 0) return;

  try {
    const token = localStorage.getItem("token");

    await api.put(
      "/transcriptions/actions/move-to-trash",
      { transcription_ids: selectedIds.value },  
      {
        headers: {Authorization: `Bearer ${token}`}
      }
    );
    transcriptions.value = transcriptions.value.filter(
      t => !selectedIds.value.includes(t.id)
    );
    selectedIds.value = [];

  } catch (error) {
    console.error("Chyba při přesunu do koše:", error);
  }
};
//obnov z kose
const restoreSelected = async () => {
  if (selectedDeletedIds.value.length === 0) return;

  try {
    const token = localStorage.getItem("token");

    await api.put(
      "/transcriptions/actions/remove-from-trash",
      { transcription_ids: selectedDeletedIds.value },  
      {
        headers: {Authorization: `Bearer ${token}`}
      }
    );
    trashedTranscriptions.value = trashedTranscriptions.value.filter(
      t => !selectedDeletedIds.value.includes(t.id)
    );
    selectedDeletedIds.value = [];

  } catch (error) {
    console.error("Chyba při přesunu do koše:", error);
  }
};
//oznaceni jako finished
const markAsFinished = async () => {
  if (selectedIds.value.length === 0) return;

  try {
    const token = localStorage.getItem("token")
  await api.put("/transcriptions/action/bulk-set-flag", {
    transcription_ids: selectedIds.value,  
    new_status: 2                           
  }, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

    // refresh data
    await fetchTranscriptions()
    selectedIds.value = [];

    $q.notify({
      type: 'positive',
      message: 'Marked as finished!'
    });
  } catch (err) {
    console.error("❌ Error marking as finished:", err);
    $q.notify({
      type: 'negative',
      message: 'Error marking as finished.'
    });
  }
}
//odOznacit
const unMarked = async () => {
  if (selectedIds.value.length === 0) return;

  try {
    const token = localStorage.getItem("token")
  await api.put("/transcriptions/action/bulk-set-flag", {
    transcription_ids: selectedIds.value,  
    new_status: 0                           
  }, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

    // refresh data
    await fetchTranscriptions()
    selectedIds.value = [];

    $q.notify({
      type: 'positive',
      message: 'Unmarked succesfully!'
    });
  } catch (err) {
    console.error("❌ Error unmarking:", err);
    $q.notify({
      type: 'negative',
      message: 'Error while unmarking'
    });
  }
}
//unmarked
//odstranit vsechny oznacene permanentne
const permanentlyDeleteSelected = async () => {
  if (selectedDeletedIds.value.length === 0) return

  try {
    const token = localStorage.getItem("token")

    await api.delete("/transcriptions/actions/permanently-delete", {
      headers: { Authorization: `Bearer ${token}` },
      data: { transcription_ids: selectedDeletedIds.value }
    })

    // Odstraň smazané přepisy z UI
    trashedTranscriptions.value = trashedTranscriptions.value.filter(
      t => !selectedDeletedIds.value.includes(t.id)
    )
    selectedDeletedIds.value = []

    $q.notify({
      type: 'positive',
      message: 'Selected transcriptions permanently deleted'
    })
  } catch (error) {
    console.error("Chyba při trvalém smazání:", error)
    $q.notify({
      type: 'negative',
      message: 'Failed to delete permanently'
    })
  }
}
const emptyTrash = async () => {
  try {
    const token = localStorage.getItem("token")
    await api.delete('/permanently-delete-all', {
      headers: { Authorization: `Bearer ${token}` }
    })
    trashedTranscriptions.value = []
    $q.notify({
      type: 'positive',
      message: 'Trash has been emptied!'
    })
    showEmptyTrashDialog.value = false
  } catch (err) {
    console.error("Chyba při vyprazdňování koše:", err)
    $q.notify({
      type: 'negative',
      message: 'Error emptying trash.'
    })
  }
}
//polling s aktualizaci prepisujicich prepisu
const startPolling = () => {
  if (pollingActive.value || pollingInterval) return
  console.log("🟢 [Polling] Spouštím polling...")

  pollingActive.value = true
  pollingInterval = setInterval(async () => {
    await fetchTranscriptions()

    const isStillTranscribing = transcriptions.value.some(t => t.progress < 100)
    if (!isStillTranscribing) {
      stopPolling()
    }
  }, 3000)
}

const stopPolling = () => {
  console.log("🔴 [Polling] Vypínám polling – vše hotovo.")
  pollingActive.value = false
  clearInterval(pollingInterval)
  pollingInterval = null
}


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
  padding: 5px;
}
.rename-title {
  font-size: 1.2rem;
  font-weight: bold;
  color: #1976d2;
}
.finished-row {
  background-color: #e8f5e9 !important; /* světle zelené pozadí */
}
</style>

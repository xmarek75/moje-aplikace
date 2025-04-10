<template>
  <q-page class="q-pa-md column">
<!-- 🔹 Horní lišta s názvem -->
    <div class="transcription-button-container">
      <q-btn label="Transcription" color="primary" icon="article" @click="openTranscriptionMenu" class=TranscriptionButton>
        <q-menu>
          <q-list>
            <q-item clickable v-close-popup @click="openModelDialog">
              <q-item-section>Choose Different Model</q-item-section>
            </q-item>
            <q-item clickable v-close-popup @click="redirectToTranscriptionMode">
              <q-item-section>Transcription Mode</q-item-section>
            </q-item>
            <q-item clickable v-close-popup @click="downloadTranscription">
              <q-item-section>Download</q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>
    </div>
    <!-- Horní část (text + video vedle sebe) -->
    <div class="row justify-between q-mb-md">
      <!-- 🔹 Levá část: Text -->
      <div class="text-area">
        
        <div
          v-for="(segment, index) in segments"
          :key="index"
          class="segment-item q-pa-sm bg-grey-2 q-mb-sm row items-center no-wrap"
          :class="{ selected: selectedSegmentIndex === index }"
          @click="selectSegment(index)"
          :ref="el => setSegmentRef(el, index)"
        >
          <q-input
            v-model.number="segment.start"
            dense
            type="number"
            class="timestamp-field"
            
            @blur="onTimeChange(index)"
          />
          <span class="mx-1">–</span>

          <q-input
            v-model.number="segment.end"
            dense
            type="number"
            class="timestamp-field"
            @blur="onTimeChange(index)"
          />
          <span class="mx-1">:</span>

          <q-input
            v-model="segment.text"
            dense
            class="text-field"
            @update:model-value="onTextChange(index)"
          />
        </div>
      </div>

      <!-- 🔸 Pravá část: Video -->
      <div class="media-box">
        <video
          ref="videoPlayer"
          controls
          class="video-player"
          :src="getMediaPath(transcription.media?.file_path)"
          @timeupdate="onVideoTimeUpdate"
        ></video>
      </div>
    </div>

    <!-- 🔻 Spodní část: Timeline -->
    <div class="timeline-container" ref="timelineContainer" />
    <q-dialog v-model="renameDialogVisible">
      <q-card>
        <q-card-section>
          <div class="text-h6">Rename Transcription</div>
          <q-input v-model="newTitle" label="New Title" autofocus />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn label="Save" color="primary" @click="renameMedia" />
        </q-card-actions>
      </q-card>
    </q-dialog>
    <!-- Pop-up okno pro zmenu modelu -->
    <q-dialog v-model="modelDialogVisible">
      <q-card class="model-card">
        <q-card-section class="model-header">
          <h5 class="model-title">Choose Model</h5>
        </q-card-section>

        <q-card-section class="model-body">
          <q-option-group
            v-model="selectedModel"
            :options="models"
            type="radio"
            class="model-options"
          />
        </q-card-section>

        <q-card-actions align="right" class="model-actions">
          <q-btn label="Cancel" color="negative" flat @click="modelDialogVisible = false" />
          <q-btn label="Save" color="primary" @click="changeModel"/>
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
  
</template>





<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataSet, Timeline } from 'vis-timeline/standalone'
import { api } from 'boot/axios'
import 'vis-timeline/styles/vis-timeline-graph2d.min.css'

const route = useRoute()
const router = useRouter();
const videoPlayer = ref(null)
const timelineContainer = ref(null)
const timeline = ref(null)
const segments = ref([])
const transcription = ref({ media: null })

const selectedSegmentIndex = ref(-1)
const segmentRefs = ref({})
let items = null

const renameDialogVisible = ref(false);
const newTitle = ref("");

const modelDialogVisible = ref(false);
const selectedModel = ref(""); 

//tabulka modelu
const models = [
  { label: 'Base', value: 'model_a' },
  { label: 'Medium', value: 'model_b' },
  { label: 'Large', value: 'model_c' }
]

const getMediaPath = (path) => {
  if (!path) return ''
  return path.startsWith('http') ? path : `http://localhost:8000${path}`
}

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

const parseTime = (timeString) => {
  const [min, sec] = timeString.split(':').map(Number)
  return (min || 0) * 60 + (sec || 0)
}


onMounted(() => {
  fetchTranscription().then(() => {
    if (videoPlayer.value?.duration) {
      initTimeline(videoPlayer.value.duration)
    } else {
      videoPlayer.value?.addEventListener("loadedmetadata", () => {
        initTimeline(videoPlayer.value.duration)
      })
    }
  })
})


const initTimeline = () => {
  const mediaDuration = videoPlayer.value?.duration || 300; // fallback: 5 min

  items = new DataSet(
    segments.value.map((s, index) => ({
      id: index,
      content: s.text,
      start: new Date(s.start * 1000),
      end: new Date(s.end * 1000),
      editable: true,
    }))
  )

  timeline.value = new Timeline(timelineContainer.value, items, {
    editable: { updateTime: true, overrideItems: true },
    stack: false,
    margin: { item: 10 },
    zoomable: true,
    moveable: true,
    showCurrentTime: true,
    timeAxis: { scale: 'second', step: 5 },
    showMinorLabels: true,
    showMajorLabels: false,
  })

  items.on('update', (changedItems) => {
    const updatedData = items.get()
    segments.value = updatedData.map(item => ({
      ...segments.value[item.id],
      start: item.start.getTime() / 1000,
      end: item.end.getTime() / 1000,
    }))
  })
  timeline.value.on('select', (props) => {
  const index = props.items?.[0]
  if (index != null) {
    selectedSegmentIndex.value = index
    scrollToSegment(index)
    const segment = segments.value[index]
    if (segment && videoPlayer.value) {
      videoPlayer.value.currentTime = segment.start
    }
  }
})
}

const fetchTranscription = async () => {
  try {
    const id = route.params.id
    const token = localStorage.getItem('token')
    const response = await api.get(`/transcriptions/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    transcription.value = response.data
    segments.value = response.data.segments.map((s, i) => ({
      id: i,
      ...s,
      startDisplay: formatTime(s.start),
      endDisplay: formatTime(s.end),
    }))
  } catch (err) {
    console.error('Failed to load transcription:', err)
  }
}

const updateTimelineFromSegments = () => {
  const updatedItems = segments.value.map((s, i) => ({
    id: i,
    content: s.text,
    start: new Date(s.start * 1000),
    end: new Date(s.end * 1000),
  }))
  items.update(updatedItems)
}

const onTimeChange = (index) => {
  updateTimelineFromSegments()
  
  
}

const onTextChange = (index) => {
  if (items) {
    items.update({
      id: index,
      content: segments.value[index].text,
    })
  }
}

const selectSegment = (index) => {
  selectedSegmentIndex.value = index

  const segment = segments.value[index]
  if (!segment) return

  // Posuň videoplayer
  if (videoPlayer.value) {
    videoPlayer.value.currentTime = segment.start
  }

  // Zvýrazni blok v timeline
  if (timeline.value) {
    timeline.value.setSelection([index], { focus: false })//zvyrazni dane blok
    timeline.value.moveTo(new Date(segment.start * 1000), {//posune blok na stred
    animation: {
    duration: 300,
    easingFunction: 'easeInOutQuad'
    }
})
  }
  scrollToSegment(index)
}
// reakce podle posunu casu ve videu
const onVideoTimeUpdate = () => {
  const current = videoPlayer.value?.currentTime || 0

  const currentSegmentIndex = segments.value.findIndex(seg =>
    current >= seg.start && current <= seg.end
  )

  if (currentSegmentIndex !== -1 && currentSegmentIndex !== selectedSegmentIndex.value) {
    selectedSegmentIndex.value = currentSegmentIndex
    scrollToSegment(currentSegmentIndex)
    timeline.value.setSelection([currentSegmentIndex])
    timeline.value.moveTo(new Date(segments.value[currentSegmentIndex].start * 1000), {
        animation: {
          duration: 300,
          easingFunction: 'easeInOutQuad'
        }
      });
  }
}
// Uloží referenci k danému segmentu
const setSegmentRef = (el, index) => {
  if (el) {
    segmentRefs.value[index] = el
  }
}
const scrollToSegment = (index) => {
  const el = segmentRefs.value[index]
  if (el && el.scrollIntoView) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}
//zmena nazvu
const openRenameDialog = () => {
  newTitle.value = transcription.value.media?.title || "";
  renameDialogVisible.value = true;
};

const renameMedia = async () => {
  try {
    const token = localStorage.getItem('token');
    await api.put(`/media/${transcription.value.media.id}/rename`, 
      { title: newTitle.value }, 
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    transcription.value.media.title = newTitle.value;
    renameDialogVisible.value = false;
  } catch (err) {
    console.error("Failed to rename transcription:", err);
  }
};
//zmena modelu
const changeModel = async () => {
  try {
    if (!selectedModel.value) {
      console.error("❌ Žádný model nebyl vybrán!");
      return;
    }

    await api.put(`/transcriptions/${transcription.value.id}/change-model`, 
      { model: selectedModel.value },  //
      { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
    );

    console.log(`✅ Model změněn na: ${selectedModel.value}`);
    modelDialogVisible.value = false; // ✅ Zavřít dialog po úspěšné změně
  } catch (error) {
    console.error("❌ Chyba při změně modelu:", error);
  }
  cancelEdit()
};
//otevreni dialogu pro zmenu modelu
const openModelDialog = () => {
  selectedModel.value = transcription.value.model || '';
  modelDialogVisible.value = true;
};
const redirectToTranscriptionMode = () =>{
  if (!route.params.id) {
    console.error("❌ Chyba: Chybí ID transkripce!");
    return;
  }
  // Přesměrování na stránku s úpravou titulků
  router.push(`/transcription/${route.params.id}`);
};
</script>



<style scoped>
.text-area {
  width: 50%;
  max-height: calc(100vh - 340px);
  overflow-y: auto;
  padding-right: 12px;
}

.media-box {
  width: 50%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 8px;
}

.video-player {
  max-width: 90%;
  height: calc(100vh - 350px);
  border-radius: 8px;
  object-fit: contain;
  background-color: grey;
}

.timeline-container {
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 8px;
  margin-top: 16px;
}

.segment-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.timestamp-field {
  width: 65px;
}

.text-field {
  flex: 1;
}

.mx-1 {
  margin: 0 4px;
}

.selected {
  background-color: #e3f2fd !important; /* jemně modrá */
  border-left: 4px solid #1976d2;
  transition: background-color 0.3s ease;
}
/* 🔹 Kontejner pro tlačítko */
.transcription-button-container {
  display: flex;
  justify-content: flex-start;
  padding: 10px 10px;
}
</style>


<template>
  <q-page class="q-pa-md column">
<!-- 🔹 Horní lišta s názvem -->
    <div class="row items-center q-gutter-sm q-mb-md transcription-header">
  <q-btn label="Transcription" color="primary" icon="article" @click="openTranscriptionMenu" class="TranscriptionButton">
    <q-menu>
      <q-list>
        <q-item clickable v-close-popup @click="openModelDialog">
          <q-item-section>Choose Different Model</q-item-section>
        </q-item>
        <q-item clickable v-close-popup @click="redirectToTranscriptionMode">
          <q-item-section>Transcription Mode</q-item-section>
        </q-item>
        <q-item clickable v-close-popup @click="showDownloadDialog = true">
          <q-item-section>Download</q-item-section>
        </q-item>
      </q-list>
    </q-menu>
  </q-btn>

  <q-btn label="Save" color="primary" @click="saveTranscription" />

  <div class="row items-center q-ml-sm">
    <div class="text-subtitle1 q-mr-xs">{{ transcription.media?.title }}</div>
    <q-btn dense flat round icon="edit" size="sm" @click="openRenameDialog" />
  </div>
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
            v-model="segment.startDisplay"
            dense
            type="text"
            class="timestamp-field"
            
            @blur="onTimeChange(index)"
          />
          <span class="mx-1">–</span>

          <q-input
            v-model="segment.endDisplay"
            dense
            type="text"
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
      <div class="media-box" style="position: relative;">
        <video
          ref="videoPlayer"
          controls
          class="video-player"
          :src="getMediaPath(transcription.media?.file_path)"
          @timeupdate="onVideoTimeUpdate"
        ></video>
        <div
          v-if="shouldShowSubtitle"
          class="subtitle-overlay"
        >
          {{ segments[selectedSegmentIndex]?.text }}
        </div>
      </div>
    </div>
    <div class="q-my-md">
  <q-btn label="Split segment" color="secondary" :disable="selectedSegmentIndex < 0" @click="openSplitDialog" />
<q-btn
  label="Delete segment"
  color="negative"
  :disable="selectedSegmentIndex < 0"
  @click="deleteSelectedSegment"
/>
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
     <!-- rename dialog -->
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
    <!--  dialog pro split -->
    <q-dialog v-model="splitDialogVisible">
      <q-card>
        <q-card-section>
          <div class="text-h6">Split Segment</div>
          <p>Click the word where the segment should be split</p>
          <div class="q-mt-sm q-mb-sm">
            <span
              v-for="(word, i) in splitWords"
              :key="i"
              @click="selectSplitIndex(i)"
              :class="['split-word', { selected: splitIndex === i }]"
            >
              {{ word.word }}
            </span>
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn label="Split" color="primary" @click="performSplit" :disable="splitIndex === null" />
        </q-card-actions>
      </q-card>
    </q-dialog>
    <q-dialog v-model="showDownloadDialog">
      <q-card>
        <q-card-section>
          <div class="text-h6">Download Options</div>
        </q-card-section>
        <q-card-section>
          <q-btn 
            label="Download plain text TXT" 
            color="primary" 
            class="q-mb-sm full-width"
            @click="downloadPlainText"
          />
          <q-btn 
            label="Download subtitles SRT" 
            color="secondary" 
            class="full-width"
            @click="downloadSRT"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="negative" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
  
</template>





<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataSet, Timeline } from 'vis-timeline/standalone'
import { api } from 'boot/axios'
import 'vis-timeline/styles/vis-timeline-graph2d.min.css'
import { useQuasar } from 'quasar'

import { useDownload } from 'src/components/useDownload'


const $q = useQuasar()
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
let saveTimeout = null
const renameDialogVisible = ref(false);
const newTitle = ref("");

const modelDialogVisible = ref(false);
const selectedModel = ref(""); 
const { downloadPlainText, downloadSRT } = useDownload(transcription)
const showDownloadDialog = ref(false);
//split
const splitDialogVisible = ref(false)
const splitWords = ref([])
const splitIndex = ref(null)
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
  const cs = Math.floor((seconds % 1) * 100)
  return `${m}:${s.toString().padStart(2, '0')}.${cs.toString().padStart(2, '0')}`
}

const parseTime = (timeString) => {
  const [minSec, msPart] = timeString.split('.')
  const [min, sec] = minSec.split(':').map(Number)
  const cs = Number(csPart || 0)
  return (min || 0) * 60 + (sec || 0) + cs / 100
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
    editable: { updateTime: true, overrideItems: true, },
    stack: false,
    margin: { item: 10 },
    zoomable: true,
    moveable: true,
    showCurrentTime: true,
    timeAxis: { scale: 'second', step: 5 },
    showMinorLabels: true,
    showMajorLabels: false,
    min: new Date(0),  // začátek od 0 sekund
    max: new Date(mediaDuration * 1000),
    
  })

  items.on('update', (changedItems) => {
    const updatedData = items.get()
    segments.value = updatedData.map(item => ({
      ...segments.value[item.id],
      start: item.start.getTime() / 1000,
      end: item.end.getTime() / 1000,
      startDisplay: formatTime(item.start.getTime() / 1000),// doplneno pozdeji
      endDisplay: formatTime(item.end.getTime() / 1000),//doplneno pozdeji
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
  const segment = segments.value[index]
  segment.start = parseTime(segment.startDisplay)
  segment.end = parseTime(segment.endDisplay)
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

  if (currentSegmentIndex !== selectedSegmentIndex.value) {
  selectedSegmentIndex.value = currentSegmentIndex
  if (currentSegmentIndex !== -1) {
    scrollToSegment(currentSegmentIndex)
    timeline.value.setSelection([currentSegmentIndex])
    timeline.value.moveTo(new Date(segments.value[currentSegmentIndex].start * 1000), {
      animation: {
        duration: 300,
        easingFunction: 'easeInOutQuad'
      }
    })
  }
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
  saveTranscription();
  router.push(`/transcription/${route.params.id}`);
};
const regenerateTranscription = () => {
  const globalWords = [];
  const segmentsWithWords = segments.value
  .filter(segment => segment.text && segment.text.trim().length > 0)  // 💡 ošetření
  .map(segment => {
    const originalWords = segment.words || [];
    const wordsArray = segment.text.trim().split(/\s+/);

    const wordsWithTiming = wordsArray.map((word, i) => {
      const original = originalWords[i];
      const w = {
        word: (i === 0 ? "" : " ") + word,
        start: original?.start ?? segment.start,
        end: original?.end ?? segment.end,
        confidence: original?.confidence ?? 1.0
      };
      globalWords.push(w);
      return w;
    });

    return {
      ...segment,
      words: wordsWithTiming
    };
  });


  transcription.value.segments = segmentsWithWords;
  transcription.value.words = globalWords;
  transcription.value.text = globalWords.map(w => w.word).join(""); // složí text s mezerami
};

const autoSaveTranscription = () => {
  regenerateTranscription();
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    try {
      await api.put(`/transcriptions/${route.params.id}`, transcription.value, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      console.log("✅ Automaticky uloženo!");
    } catch (error) {
      console.error("Chyba při automatickém ukládání:", error);
    }
  }, 1000);
};
const saveTranscription = async () => {
  regenerateTranscription();
  try {
    await api.put(`/transcriptions/${route.params.id}`, transcription.value, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });

    $q.notify({ type: 'positive', message: 'Changes saved successfully.' });
  } catch (error) {
    console.error("Chyba při ukládání:", error);
    $q.notify({ type: 'negative', message: 'Failed to save changes.' });
  }
};
const shouldShowSubtitle = computed(() => {
  const index = selectedSegmentIndex.value

  // zkontroluj platnost indexu a existenci segmentu
  if (index === null || index < 0 || index >= segments.value.length) return false

  const segment = segments.value[index]
  const time = videoPlayer.value?.currentTime ?? 0

  return time >= segment.start && time <= segment.end
});

const openSplitDialog = () => {
  const segment = segments.value[selectedSegmentIndex.value]
  splitWords.value = segment.words || segment.text.split(/\s+/).map(w => ({ word: w }))
  splitIndex.value = null
  splitDialogVisible.value = true
}

const selectSplitIndex = (index) => {
  splitIndex.value = index
}

const performSplit = () => {
  const segment = segments.value[selectedSegmentIndex.value]
  if (!segment || splitIndex.value === null) return

  const firstWords = splitWords.value.slice(0, splitIndex.value + 1)
  const secondWords = splitWords.value.slice(splitIndex.value + 1)

  if (firstWords.length === 0 || secondWords.length === 0) return

  const firstText = firstWords.map(w => w.word).join("").trim()
  const secondText = secondWords.map(w => w.word).join("").trim()

  const newSegments = [
    {
      ...segment,
      text: firstText,
      end: firstWords.at(-1).end, // konec prvního = konec posledního slova
      words: firstWords,
    },
    {
      ...segment,
      text: secondText,
      start: secondWords[0].start, // začátek druhého = začátek prvního slova
      words: secondWords,
    },
  ]

  segments.value.splice(selectedSegmentIndex.value, 1, ...newSegments)
  segments.value = segments.value.map((s, i) => ({ ...s, id: i }))
  splitDialogVisible.value = false
  updateTimelineFromSegments()

}

const deleteSelectedSegment = () => {
  if (selectedSegmentIndex.value < 0) return

  segments.value.splice(selectedSegmentIndex.value, 1)

  segments.value = segments.value.map((s, i) => ({
    id: i,
    start: s.start ?? 0,
    end: s.end ?? 0,
    text: s.text ?? "",
    words: s.words ?? [],
    startDisplay: formatTime(s.start ?? 0),
    endDisplay: formatTime(s.end ?? 0),
  }))

  selectedSegmentIndex.value = -1
  updateTimelineFromSegments()
}
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
  margin-top: 35px;
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
  align-items: center;
  justify-content: flex-start; /* vše držet vlevo */
  gap: 12px; /* mezera mezi prvky */
  flex-wrap: wrap;
}
.subtitle-overlay {
  position: absolute;
  bottom: 10%;
  left: 50%;
  transform: translateX(-50%);
  max-width: 90%;
  text-align: center;
  font-size: 1.2rem;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 0.4em 1em;
  border-radius: 4px;
  pointer-events: none;
  z-index: 10;
}
.transcription-button-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  flex-wrap: wrap;
}
.transcription-header {
  justify-content: flex-start;
  flex-wrap: nowrap;
}
.split-word {
  display: inline-block;
  margin: 4px;
  padding: 6px 10px;
  border-radius: 4px;
  background: #f0f0f0;
  cursor: pointer;
}
.split-word.selected {
  background-color: #1976d2;
  color: rgb(9, 72, 232);
}
</style>


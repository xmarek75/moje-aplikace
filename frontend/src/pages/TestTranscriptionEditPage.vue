<template>
  <q-page class="page-container">
    <!-- 🔹 Tlačítko "Transcription" s menu -->
    <div class="transcription-button-container">
      <q-btn label="Transcription" color="primary" icon="article"  class=TranscriptionButton>
        <q-menu>
          <q-list>
            <q-item clickable v-close-popup @click="openModelDialog">
              <q-item-section>Choose Different Model</q-item-section>
            </q-item>
            <q-item clickable v-close-popup @click="redirectToSubtitleMode">
              <q-item-section>Subtitle Mode</q-item-section>
            </q-item>
            <q-item clickable v-close-popup @click="showDownloadDialog = true">
              <q-item-section>Download</q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>
      <div class="shortcut-header">
        <q-btn
            dense
            round
            icon="help_outline"
            flat
            @click="showShortcutsDialog = true"
        >
            <q-tooltip>Keyboard Shortcuts</q-tooltip>
        </q-btn>
      </div>
    </div>

    <q-card class="main-card">
      <q-card-section class="header">
        <div class="title-container">
          <h5>{{ transcription.media?.title }}</h5>
          <q-btn flat dense icon="edit" class="edit-icon" @click="openRenameDialog"/>
        </div>
      </q-card-section>

      <div class="content-container">
        <!-- Levá část: Textová transkripce -->
        <div 
        class="transcription-container" 
        ref="transcriptionContainer" 
        contenteditable="true"
        @keydown="handleKeyDown"
        
        >
            <div 
                v-for="segment in transcription.segments" 
                :key="segment.start" 
                class="segment-line"
            >
                <span 
                v-for="(word) in segment.words" 
                :key="word.start"
                :ref="setWordRef"
                :data-word-start="word.start"
                :class="[getConfidenceClass(word.confidence), { 'highlighted': isHighlighted(word.start) }]"
                contenteditable="true"
                spellcheck="false"
                >
                {{ word.word }}
                </span>
            </div>
        </div>
        <!-- Pravá část: Detaily slova -->
        <div class="details-container" v-if="selectedWord">
          <div class="details-box">
            <div class="word">
              <strong>{{ selectedWord.word }}</strong>
            </div>
            <div class="info">
              <span>🕒 {{ formatTime(selectedWord.start) }} - {{ formatTime(selectedWord.end) }}</span>
              <span>🎯 Confidence: {{ (selectedWord.confidence * 100).toFixed(1) }}%</span>
            </div>
            <q-btn label="✔ Confirm" color="primary" @click="confirmCorrectness" class="confirm-btn"/>
          </div>
        </div>
      </div>

      <!-- Akční tlačítka -->
      <q-card-actions align="right">
        <q-btn label="Save" color="primary" @click="saveTranscription" />
        <q-btn label="Cancel" color="negative" flat @click="cancelEdit" />
      </q-card-actions>
    </q-card>

    <!-- Audio přehrávač pevně připojený dole -->
    <div v-if="transcription.media" class="audio-container row items-center q-gutter-sm">
      <audio 
        ref="audioPlayer"
        controls 
        :src="getMediaPath(transcription.media.file_path)"
        class="audio-player"
        @timeupdate="updateActiveWord"
        @play="onMediaPlay"
        @pause = "MediaPlayerPlaying = false"
      >          
      </audio>
      <!-- Výběr rychlosti přehrávání -->
      <q-select
        v-model="playbackRate"
        :options="speedOptions"
        label="Speed"
        dense
        outlined
        class="speed-select"
        @update:model-value="changePlaybackRate"
      />
      <div style="min-width: 200px; max-width: 250px;">
        <q-slider
          v-model="confidenceThreshold"
          :min="0"
          :max="1"
          :step="0.01"
          label
          color="red"
          thumb-color="red"
          track-color="grey-5"
        />
        <div class="text-caption text-grey text-center">Confidence threshold</div>
  </div>
    </div>
    <!-- Pop-up okno pro přejmenování -->
    <q-dialog v-model="renameDialogVisible">
      <q-card class="rename-card">
        <q-card-section>
          <h5 class="rename-title">Rename Transcription</h5>
          <q-input v-model="newTitle" label="New Title" autofocus />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn label="Cancel" color="negative" flat @click="renameDialogVisible = false" />
          <q-btn label="Save" color="primary" @click="renameMedia"/>
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
    <q-dialog v-model="showShortcutsDialog">
        <q-card>
            <q-card-section>
            <div class="text-h6">⌨️ Keyboard Shortcuts</div>
            </q-card-section>

            <q-card-section>
            <q-list dense bordered class="q-mb-md">
                <q-item>
                <q-item-section>Ctrl + →</q-item-section>
                <q-item-section side>Next word</q-item-section>
                </q-item>
                <q-item>
                <q-item-section>Ctrl + ←</q-item-section>
                <q-item-section side>Previous word</q-item-section>
                </q-item>
                <q-item>
                <q-item-section>Ctrl + ↑</q-item-section>
                <q-item-section side>Previous segment</q-item-section>
                </q-item>
                <q-item>
                <q-item-section>Ctrl + ↓</q-item-section>
                <q-item-section side>Next segment</q-item-section>
                </q-item>
                <q-item>
                <q-item-section>Ctrl + Enter</q-item-section>
                <q-item-section side>Mark word as correct (black)</q-item-section>
                </q-item>
                <q-item>
                <q-item-section>Ctrl + Space</q-item-section>
                <q-item-section side>Play / Pause media</q-item-section>
                </q-item>
                <q-item>
                <q-item-section>Ctrl + "1"</q-item-section>
                <q-item-section side>Mark word green</q-item-section>
                </q-item>
                <q-item>
                <q-item-section>Ctrl + "2"</q-item-section>
                <q-item-section side>Set confidence as 0.6(Red)</q-item-section>
                </q-item>
            </q-list>
            
            </q-card-section>

            <q-card-actions align="right">
            <q-btn flat label="Close" color="primary" v-close-popup />
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
        label="Download without timestamps" 
        color="primary" 
        class="q-mb-sm full-width"
        @click="handleDownloadPlain"
      />
      <q-btn 
        label="Download with timestamps" 
        color="secondary" 
        class="full-width"
        @click="handleDownloadWithTimestamps"
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
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar'
import contenteditable from 'vue-contenteditable'


const $q = useQuasar()
const route = useRoute();
const router = useRouter();
const transcription = ref({ text: "", segments: [], media: null,id: null, model: '' });
const selectedWord = ref(null);
const audioPlayer = ref(null);
const activeWordStart = ref(null); // Aktuálně zvýrazněné slovo
let saveTimeout = null; // ✅ Uchovává timeout pro debounce efekt
const renameDialogVisible = ref(false); //viditelnost rename dialogu
const modelDialogVisible = ref(false); //viditelnost model dialogu
const newTitle = ref(""); //uchovava novy nazev
const selectedModel = ref(""); //novy model
const playbackRate = ref(1.0); //defaultni rychlost prehravani
const speedOptions = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]; //moznosti rychlosti prehravani
const transcriptionContainer = ref(null) //pro automaticke scrollovani
const wordElements = ref({})
const MediaPlayerPlaying = ref(false); //flag pro media player 
const showShortcutsDialog = ref(false); // dialog napovedy
const showDownloadDialog = ref(false); // dialog pro stazeni
const confidenceThreshold = ref(0.7) // pod jakou confidence hodnotu zobrazovat cervene
let lockInterval = null// interval pro uzamknuti, pro shared transcriptions
const editedWords = ref({}); // sleduje zmeny
const previousWordRef = ref(null);
const currentSegmentID = ref(null);
const previousSegmentID = ref(null);
// ✅ Tabulka sloupců pro vybrané slovo
const columns = [
  { name: "word", label: "Word", align: "left", field: row => row.word },
  { name: "start", label: "Start Time", align: "left", field: row => formatTime(row.start) },
  { name: "end", label: "End Time", align: "left", field: row => formatTime(row.end) },
  { name: "confidence", label: "Confidence", align: "left", field: row => Math.min(row.confidence * 100, 100).toFixed(1) + "%" }
];
//tabulka modelu
const models = [
  { label: 'Base', value: 'model_a' },
  { label: 'Medium', value: 'model_b' },
  { label: 'Large', value: 'model_c' }
]
// ✅ Načtení transkripce z API
const fetchTranscription = async () => {
  try {
    const response = await api.get(`/transcriptions/${route.params.id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });
    console.log("✅ Transcription data received:", response.data);
    transcription.value = response.data || { text: '', segments: [], media: null, id: null, model: ''}; // ✅ Oprava chybějících dat
  } catch (error) {
    console.error("Chyba při načítání transkripce:", error);
  }
};

const regenerateFromWords = () => {
  const segments = transcription.value.segments

  // ✅ Update `text`
  const allWords = segments.flatMap(s => s.words)
  transcription.value.text = allWords.map(w => w.word).join(' ')

  // ✅ Update `segments` (pouze text v segmentech)
  segments.forEach(segment => {
    segment.text = segment.words.map(w => w.word).join(' ')
  })

  transcription.value.segments = [...segments]
}


// ulozeni markeru
const autoSaveTranscription = () => {
  
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    try {
      await api.put(`/transcriptions/${route.params.id}`, 
        transcription.value,  
        { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
      );
      console.log("✅ Automaticky uloženo!");
    } catch (error) {
      console.error("Chyba při automatickém ukládání:", error);
    }
  }, 1000);
};

// ✅ Funkce pro manuální uložení
const saveTranscription = async () => {
  regenerateTextAndSegmentsFromWords()

  try {
    await api.put(`/transcriptions/${route.params.id}`, transcription.value, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });
    console.log("✅ Změny uloženy!");
    $q.notify({ type: 'positive', message: 'Transcription saved successfully!' })
  } catch (error) {
    console.error("❌ Chyba při ukládání:", error);
    $q.notify({ type: 'negative', message: 'Error saving transcription.' })
  }
};
const regenerateTextAndSegmentsFromWords = () => {
  const segments = transcription.value.segments

  //  Update text (sloučíme všechna slova z všech segmentů)
  const allWords = segments.flatMap(s => s.words)
  transcription.value.text = allWords.map(w => w.word).join(' ')

  //  Update text v každém segmentu
  segments.forEach(segment => {
    segment.text = segment.words.map(w => w.word).join(' ')
  })

  transcription.value.segments = [...segments]  // znovu přepíšeme pro reaktivitu
}

// ✅ Funkce pro návrat zpět
const cancelEdit = () => {
  router.push("/home");
};
const redirectToSubtitleMode = () =>{
  if (!route.params.id) {
    console.error("❌ Chyba: Chybí ID transkripce!");
    return;
  }
  // Přesměrování na stránku s úpravou titulků
  saveTranscription()
  router.push(`/subtitle-editor/${route.params.id}`);
};

// ✅ Funkce pro formátování času
const formatTime = (time) => {
  if (time === null || time === undefined) return "N/A";
  const minutes = Math.floor(time / 60);
  const seconds = (time % 60).toFixed(2);
  return `${minutes}:${seconds}`;
};

// ✅ Ověření, zda je slovo zvýrazněné
const isHighlighted = (wordStart) => {
  return activeWordStart.value === wordStart;
};

// ✅ Určuje barvu podle confidence
const getConfidenceClass = (confidence) => {
  if (confidence > 1.0) return 'text-green';
  if (confidence < confidenceThreshold.value) return "text-red";
  return "text-black";
};

// ✅ Výběr slova pro detaily, upravi cas v audiplayeru, nastavi slovo na aktivni
const selectWord = (word) => {
  selectedWord.value = word;
  if (audioPlayer.value) {
    audioPlayer.value.currentTime = word.start; // Posun přehrávače
    
  }
  activeWordStart.value = word.start; //zvyraznit slovo
};

// Aktualizace aktivního slova při přehrávání
const updateActiveWord = () => {
  if (!audioPlayer.value || !MediaPlayerPlaying.value) return;
  const currentTime = audioPlayer.value.currentTime;
  let foundWord = null;

  transcription.value.segments.forEach(segment => {
    segment.words.forEach(word => {
      if (
        currentTime >= (word.start) &&
        currentTime <= (word.end)
      ) {
        foundWord = word;
      }
    });
  });

  if (foundWord) {
    activeWordStart.value = foundWord.start;
    selectedWord.value = foundWord;

    const el = wordElements.value[foundWord.start];
    if (el && transcriptionContainer.value) {
      const container = transcriptionContainer.value;
      const offsetTop = el.offsetTop - container.offsetTop;
      const scrollTarget = offsetTop - container.clientHeight / 2 + el.clientHeight / 2;
      container.scrollTo({
        top: scrollTarget,
        behavior: 'smooth'
      });
    }
  }
};

// ✅ Potvrzení správnosti slova
const confirmCorrectness = () => {
  if (selectedWord.value) {
    selectedWord.value.confidence = 1.0;
    autoSaveTranscription(); // ✅ Automaticky uloží potvrzení
  }
};

const getMediaPath = (path) => {
  if (!path.startsWith("http")) {
    return `http://localhost:8000${path}`; // ✅ Oprava URL pro Vue
  }
  return path;
};

const openRenameDialog = () => {
  newTitle.value = transcription.value.media?.title || "";
  renameDialogVisible.value = true;
};

//prejmenovani nazvu media
const renameMedia = async () => {
  if (!newTitle.value.trim()) return;
  
  try {
    await api.put(`/media/${transcription.value.media.id}/rename`, 
      { title: newTitle.value },
      { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
    );

    transcription.value.media.title = newTitle.value;
    renameDialogVisible.value = false;
  } catch (error) {
    console.error("Chyba při přejmenování:", error);
  }
};

//zmena rychlosti prehravani
const changePlaybackRate = () => {
  if (audioPlayer.value) {
    audioPlayer.value.playbackRate = playbackRate.value;
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
// Pomocná funkce pro přiřazení ref ke slovům
const setWordRef = (el) => {
  if (el && el.dataset && el.dataset.wordStart) {
    wordElements.value[el.dataset.wordStart] = el
  }
}
//podle kurzoru zmena detailu a casu na mediaplayer   + autoscroll
const handleSelectionChange = () => {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return;

  const range = selection.getRangeAt(0);
  const node = range.startContainer?.parentElement;

  if (node && node.dataset.wordStart) {
    const startTime = parseFloat(node.dataset.wordStart);
    const currentWord = findWordByStart(startTime);

    if (currentWord) {
      // 🟢 Nejdřív ulož předchozí, pokud existuje
      if (previousWordRef.value && previousWordRef.value !== currentWord) {
        const oldNode = wordElements.value[previousWordRef.value.start];
        const newText = oldNode?.innerText;

        if (newText && previousWordRef.value.word.trim() !== newText.trim()) {
          autoSaveOneWord(previousWordRef.value.start, previousSegmentID.value, newText)
          console.log(`💾 Ukládám::"${previousSegmentID.value}"---"${previousWordRef.value.word}" → "${newText}"`);
          
          previousWordRef.value.word = newText;
          editedWords.value[previousWordRef.value.start] = newText;
        }
      }

      // 🔁 Aktualizuj previousWord
      previousWordRef.value = currentWord;

      // ⏩ Vyber aktuální slovo
      activeWordStart.value = currentWord.start;
      selectedWord.value = currentWord;

      if (audioPlayer.value) {
        audioPlayer.value.currentTime = currentWord.start;
      }

      // 🔄 Scroll doprostřed
      const el = wordElements.value[currentWord.start];
      if (el && transcriptionContainer.value) {
        const container = transcriptionContainer.value;
        const offsetTop = el.offsetTop - container.offsetTop;
        const scrollTarget = offsetTop - container.clientHeight / 2 + el.clientHeight / 2;
        container.scrollTo({
          top: scrollTarget,
          behavior: 'smooth'
        });
      }
    }
  }
};
//automaticke ulozeni zmeneneho slova
const autoSaveOneWord = async (word_start, segmentId, new_word) => {
  // 🔒 Typová kontrola
  if (
    typeof word_start !== 'number' ||
    typeof segmentId !== 'number' ||
    typeof new_word !== 'string' ||
    new_word.trim() === ''
  ) {
    console.warn("⚠️ Neplatné vstupní hodnoty pro autoSaveOneWord:", {
      word_start,
      segmentId,
      new_word
    })
    return
  }

  try {
    await api.put(`/transcriptions/${route.params.id}/update-word`, {
      word_start,
      segment_id: segmentId,
      new_word: new_word.trim()
    }, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    })
    console.log(`💾 Slovo "${new_word}" (start: ${word_start}, segment: ${segmentId}) úspěšně uloženo.`)
  } catch (err) {
    console.error("❌ Chyba při ukládání jednoho slova:", err)
  }
}

const findWordByStart = (start) => {
  for (const segment of transcription.value.segments) {
    const found = segment.words.find(w => w.start === start)
    if (found) {
      previousSegmentID.value = currentSegmentID.value
      currentSegmentID.value = segment.segment_id
      return found
    }
  }
  return null
}
// Klávesová navigace a ovládání přehrávače
const handleKeyboardNavigation = (event) => {
  const segments = transcription.value.segments;
  const flatWords = segments.flatMap(s => s.words);

  // ⏯️ Ctrl + Mezerník → Play / Pause
  if (event.ctrlKey && event.code === 'Space') {
    event.preventDefault();
    if (audioPlayer.value) {
      audioPlayer.value.paused ? audioPlayer.value.play() : audioPlayer.value.pause();
    }
    return;
  }

  // ✅ Ctrl + Enter → potvrzení správnosti
  if (event.ctrlKey && event.key === 'Enter') {
    event.preventDefault();
    confirmCorrectness();
    return;
  }
  // Ctrl + 1 → Mark word as "done"
  if (event.ctrlKey && event.key.toLowerCase() === '1') {
    if (selectedWord.value) {
        selectedWord.value.confidence = 1.1;
        autoSaveTranscription();
    }
    return;
    }
  // Ctrl + 2 → Mark word as "confidence=0.6"
  if (event.ctrlKey && event.key.toLowerCase() === '2') {
    if (selectedWord.value) {
        selectedWord.value.confidence = 0.6;
        autoSaveTranscription();
    }
    return;
    }

  const currentIndex = flatWords.findIndex(w => w.start === activeWordStart.value);

  // 🚀 Ctrl + šipka vpravo/vlevo → mezi slovy
  if (event.ctrlKey && (event.key === 'ArrowRight' || event.key === 'ArrowLeft')) {
    event.preventDefault();

    let nextIndex = currentIndex;
    if (event.key === 'ArrowRight' && currentIndex < flatWords.length - 1) {
      nextIndex++;
    } else if (event.key === 'ArrowLeft' && currentIndex > 0) {
      nextIndex--;
    }

    const nextWord = flatWords[nextIndex];
    if (nextWord) {
      jumpToWord(nextWord);
    }
    return;
  }

  // 🔽 Ctrl + šipka nahoru/dolů → mezi segmenty
  if (event.ctrlKey && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
    event.preventDefault();

    const currentSegmentIndex = segments.findIndex(s =>
      s.words.some(w => w.start === activeWordStart.value)
    );

    let nextSegment = null;
    if (event.key === 'ArrowDown' && currentSegmentIndex < segments.length - 1) {
      nextSegment = segments[currentSegmentIndex + 1];
    } else if (event.key === 'ArrowUp' && currentSegmentIndex > 0) {
      nextSegment = segments[currentSegmentIndex - 1];
    }

    if (nextSegment && nextSegment.words.length > 0) {
      jumpToWord(nextSegment.words[0]); // první slovo segmentu
    }
  }
};
// Pomocná funkce pro skok na dané slovo
const jumpToWord = (word) => {
  selectedWord.value = word;
  activeWordStart.value = word.start;

  if (audioPlayer.value) {
    audioPlayer.value.currentTime = word.start;
  }

  const el = wordElements.value[word.start];
  if (el && transcriptionContainer.value) {
    const container = transcriptionContainer.value;
    const offsetTop = el.offsetTop - container.offsetTop;
    const scrollTarget = offsetTop - container.clientHeight / 2 + el.clientHeight / 2;

    container.scrollTo({
      top: scrollTarget,
      behavior: 'smooth'
    });

    // kurzor do slova
    const range = document.createRange();
    const selection = window.getSelection();
    range.selectNodeContents(el);
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
    el.focus();
  }
};
//sledování změny paused
watch(MediaPlayerPlaying, (isPlaying) => {
  if (!isPlaying && activeWordStart.value) {
    focusActiveWordElement()
  }
})
const onMediaPlay = () => {
  MediaPlayerPlaying.value = true
  

  //  Odstranit focus z aktivního elementu
  if (document.activeElement && document.activeElement.blur) {
    document.activeElement.blur()
  }

  
}

//presun kurzoru po stopnuti mediaplayeru na zvyraznene slovo
const focusActiveWordElement = () => {
  const el = wordElements.value[activeWordStart.value]
  if (el) {
    const range = document.createRange()
    const selection = window.getSelection()
    range.selectNodeContents(el)
    range.collapse(false)
    selection.removeAllRanges()
    selection.addRange(range)
    el.focus()
  }
}
//handlekeydown pro hromadne oznaceni slov
const handleKeyDown = (event) => {
  if (event.ctrlKey && event.key === 'Enter') {
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed) return

    const range = selection.getRangeAt(0)
    const selectedNodes = getSpansInRange(range)

    selectedNodes.forEach((el) => {
      const start = parseFloat(el.dataset.wordStart) 
      for (const segment of transcription.value.segments) {
        const word = segment.words.find(w => w.start === start)
        if (word) {
          word.confidence = 1.0
        }
      }
    })

    // aktualizuj reaktivitu
    transcription.value = { ...transcription.value }
    autoSaveTranscription()
  }
  else if (event.ctrlKey && event.key === '1') {
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed) return

    const range = selection.getRangeAt(0)
    const selectedNodes = getSpansInRange(range)

    selectedNodes.forEach((el) => {
      const start = parseFloat(el.dataset.wordStart) 
      for (const segment of transcription.value.segments) {
        const word = segment.words.find(w => w.start === start)
        if (word) {
          word.confidence = 1.1
        }
      }
    })

    // aktualizuj reaktivitu
    transcription.value = { ...transcription.value }
    autoSaveTranscription()
  }
  else if (event.ctrlKey && event.key === '2') {
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed) return

    const range = selection.getRangeAt(0)
    const selectedNodes = getSpansInRange(range)

    selectedNodes.forEach((el) => {
      const start = parseFloat(el.dataset.wordStart) 
      for (const segment of transcription.value.segments) {
        const word = segment.words.find(w => w.start === start)
        if (word) {
          word.confidence = 0.6
        }
      }
    })

    // aktualizuj reaktivitu
    transcription.value = { ...transcription.value }
    autoSaveTranscription()
  }
}
//zamykani prepisu
const keepTranscriptionLocked = async () => {
  try {
    await api.put(`/transcriptions/${route.params.id}/lock`, null, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });
    console.log("🔐 Zámek obnoven");
  } catch (err) {
    console.error("❌ Chyba při prodlužování zámku:", err);
  }
};
const getSpansInRange = (range) => {
  const selected = []
  const walker = document.createTreeWalker(
    range.commonAncestorContainer,
    NodeFilter.SHOW_ELEMENT,
    {
      acceptNode: (node) => {
        if (
          node.nodeName === 'SPAN' &&
          node.dataset.wordStart &&
          range.intersectsNode(node)
        ) {
          return NodeFilter.FILTER_ACCEPT
        }
        return NodeFilter.FILTER_SKIP
      }
    }
  )

  let node = walker.nextNode()
  while (node) {
    selected.push(node)
    node = walker.nextNode()
  }

  return selected
}
const downloadPlainText = () => {
  const text = transcription.value.segments
    .map(seg => seg.words.map(w => w.word).join(" "))
    .join("\n\n");

  triggerDownload(text, 'plain');
}

const downloadWithTimestamps = () => {
  const text = transcription.value.segments
    .map(seg => {
      const time = `${formatTime(seg.start)} - ${formatTime(seg.end)}`
      const content = seg.words.map(w => w.word).join(" ")
      return `[${time}] ${content}`
    })
    .join("\n\n");

  triggerDownload(text, 'timestamps');
}

const triggerDownload = (text, type) => {
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const title = transcription.value.media?.title || "transcription";
  a.download = `${title}${type === 'timestamps' ? '_with_timestamps' : ''}.txt`;
  a.href = url;
  a.click();
  URL.revokeObjectURL(url);
}

const handleDownloadPlain = () => {
  downloadPlainText()
  showDownloadDialog.value = false
}
const handleDownloadWithTimestamps = () => {
  downloadWithTimestamps()
  showDownloadDialog.value = false
}
onMounted(async () => {
  const id = route.params.id;
  
  try {
    //prvni uzamknuti
    await api.put(`/transcriptions/${id}/lock`, null, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });

    //  Pokud zámek úspěšný, načti transkripci
    await fetchTranscription();
    //uzamknuti kazdych 10s
    lockInterval = setInterval(keepTranscriptionLocked, 10000);
    document.addEventListener('selectionchange', handleSelectionChange);
    window.addEventListener('keydown', handleKeyboardNavigation);

  } catch (err) {
    if (err.response?.status === 403) {
      $q.notify({
        type: 'negative',
        message: 'This transcription is already being edited by someone else.'
      });
      router.push('/home');
    } else {
      console.error("Chyba při zamykání přepisu:", err);
    }
  }
});

onBeforeUnmount(async () => {
  //  Odebrání listenerů
  document.removeEventListener('selectionchange', handleSelectionChange);
  window.removeEventListener('keydown', handleKeyboardNavigation);
  clearInterval(lockInterval);
});


</script>

<style scoped>
/* 🔹 Hlavní kontejner stránky */
.page-container {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100vh;
  padding-bottom: 80px; /* Zajistit místo pro přehrávač */
}

/* 🔹 Hlavní karta */
.main-card {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  width: 90%;
  margin: auto;
  padding: 20px;
  max-height: 80vh; /* Zabrání přetékání mimo viewport */
  overflow: hidden;
}

/* 🔹 Kontejner pro obsah - transkripce a detaily vedle sebe */
.content-container {
  display: flex;
  flex-grow: 1;
  overflow: hidden;
}

/* 🔹 Levá část - Transkripce */
.transcription-container {
  flex: 4;
  background: #f5f5f5;
  padding: 10px;
  border-radius: 5px;
  max-height: 60vh; /* Umožní skrolování */
  overflow-y: auto;
  margin-right: 10px;
}

/* 🔹 Pevně připojený audio přehrávač dole */
.audio-container {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background: white;
  padding: 10px;
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  display: flex;
  justify-content: center;
}

/* 🔹 Přehrávač */
.audio-player {
  width: 100%;
  max-width: 800px;
  padding: 5px;
  border-radius: 10px;
}

/* 🔹 Zvýraznění aktivního slova */
.highlighted {
  background-color: yellow;
  font-weight: bold;
}

/* 🔹 Kontejner pro detaily */
.details-container {
  flex: 1;
  background: #ffffff;
  padding: 10px;
  border-radius: 8px;
  max-height: 60vh;
  overflow-y: auto;
  border-left: 2px solid #ddd; /* Oddělení od transkripce */
  display: flex;
  align-items: center;
  justify-content: center;
 
}

/* 🔹 Box s informacemi */
.details-box {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 10px;
  box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 300px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 🔹 Zvýrazněné slovo */
.details-box .word {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

/* 🔹 Informace pod slovem */
.details-box .info {
  font-size: 0.9rem;
  color: #666;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 🔹 Tlačítko pro potvrzení */
.confirm-btn {
  margin-top: 10px;
  width: 100%;
}

/* 🔹 Kontejner pro název a edit ikonku */
.title-container {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header {
  padding-top: 0px;
  padding-bottom: 8px; /* Mírný prostor dole */
}

.title-container h5 {
  margin: 0;
  padding: 0;
  font-size: 1.2rem;
  line-height: 1.2;
  text-decoration: underline;
}
/* 🔹 Stylizace tužtičky */
.edit-icon {
  font-size: 1.0rem;
  color: #1976d2;
}

/* 🔹 Při najetí změna barvy */
.edit-icon:hover {
  color: #15c090;
}

/* 🔹 Styling pop-up okna */
.rename-card {
  width: 400px;
  padding: 20px;
}

/* 🔹 Styling dropdownu pro rychlost */
.speed-select {
  width: 100px;
  min-width: 80px;
  padding: 5px;
  border-radius: 10px;
}

/* 🔹 Kontejner pro tlačítko */
.transcription-button-container {
  display: flex;
  justify-content: flex-start;
  padding: 10px 10px;
}
.transcription-container span {
  font-size: 1.05rem; /* nebo třeba 1.4rem pro větší efekt */
  line-height: 1.8;
  padding: 2px;
}
.TranscriptionButton{
  border-radius: 8px;
  padding: 8px 16px;
  
}
.model-card {
  width: 400px;
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.2);
}

/* 🔹 Hlavička dialogu */
.model-header {
  text-align: center;
  padding-bottom: 0;
}

.model-title {
  font-size: 1.2rem;
  font-weight: bold;
  color: #1976d2;
}
.rename-title {
  font-size: 1.2rem;
  font-weight: bold;
  color: #1976d2;
}

/* 🔹 Možnosti modelů */
.model-body {
  padding: 10px 20px ;
}

.model-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 🔹 Animace při výběru */
.model-options .q-radio {
  transition: transform 0.2s ease-in-out;
}

.model-options .q-radio:active {
  transform: scale(1.1);
}
.segment-line {
  margin-bottom: 5px;
  
}
.shortcut-header {
  position: absolute;
  top: 10px;
  right: 20px;
  z-index: 10;
}
.text-green {
  color: green;
  font-weight: bold;
}
</style>

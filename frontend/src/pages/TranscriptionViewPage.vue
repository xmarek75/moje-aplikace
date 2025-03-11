<template>
  <q-page padding>
    <q-card>
      <q-card-section>
        <h2>Transcription</h2>
        <p>{{ transcription.text }}</p>
      </q-card-section>

      <q-card-section>
        <h3>Segmenty</h3>
        <div v-for="segment in transcription.segments" :key="segment.start">
          <q-card class="q-mb-md">
            <q-card-section>
              <div>
                <strong>Start:</strong> {{ formatTime(segment.start) }}
                <strong>End:</strong> {{ formatTime(segment.end) }}
              </div>
              <p><strong>Text:</strong> {{ segment.text }}</p>
            </q-card-section>
            <q-card-section>
              <h4>Slova</h4>
              <ul>
                <li v-for="word in segment.words" :key="word.start">
                  <strong>{{ word.word }}</strong> 
                  ({{ formatTime(word.start) }} - {{ formatTime(word.end) }})
                  <span :class="getConfidenceClass(word.confidence)">
                    Confidence: {{ (word.confidence * 100).toFixed(1) }}%
                  </span>
                </li>
              </ul>
            </q-card-section>
          </q-card>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { api } from 'boot/axios';

const route = useRoute();
const transcription = ref({ text: "", segments: [] });

const fetchTranscription = async () => {
  try {
    const response = await api.get(`/transcriptions/${route.params.id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });
    transcription.value = response.data;
  } catch (error) {
    console.error("Chyba při načítání transkripce:", error);
  }
};

// ✅ Pomocná funkce pro formátování času
const formatTime = (time) => {
  if (time === null || time === undefined) return "N/A";
  const minutes = Math.floor(time / 60);
  const seconds = (time % 60).toFixed(2);
  return `${minutes}:${seconds}`;
};

// ✅ Určuje barvu pro pravděpodobnost
const getConfidenceClass = (confidence) => {
  if (confidence > 0.9) return "text-green";
  if (confidence > 0.7) return "text-orange";
  return "text-red";
};

onMounted(fetchTranscription);
</script>

<style scoped>
.text-green {
  color: green;
}

.text-orange {
  color: orange;
}

.text-red {
  color: red;
}
</style>

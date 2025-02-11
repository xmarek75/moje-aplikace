<template>
  <q-page class="index-page flex flex-center">
    <div class="content-container">
      <div class="hero-section">
        <h1 class="app-title">LexApp</h1>
        <p class="app-tagline">Revolutionizing Speech-to-Text Technology</p>
      </div>
      <div class="features">
        <q-card class="feature-card">
          <q-icon name="mic" color="primary" size="3rem" />
          <p>High-accuracy Speech-to-Text</p>
        </q-card>
        <q-card class="feature-card">
          <q-icon name="edit" color="primary" size="3rem" />
          <p>Intuitive Text Editing</p>
        </q-card>
        <q-card class="feature-card">
          <q-icon name="share" color="primary" size="3rem" />
          <p>Easy Sharing & Collaboration</p>
        </q-card>
        <q-card class="feature-card">
          <q-icon name="subtitles" color="primary" size="3rem" />
          <p>Generate High-Quality Subtitles</p>
        </q-card>
      </div>
      <div class="action-buttons">
        <q-btn label="Sign Up" color="primary" to="/signup" class="q-mt-md action-btn" />
        <q-btn label="Sign In" color="secondary" to="/signin" class="q-mt-md action-btn" />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import backgroundImage from 'src/assets/IndexPageBackground.webp' // Přidej obrázek do src/assets/
</script>

<style scoped>
.index-page {
  background: url('src/assets/IndexPageBackground.webp') no-repeat center center fixed;
  background-size: cover;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: white;
}

.content-container {
  background: rgba(0, 0, 0, 0.7);
  padding: 3rem;
  border-radius: 20px;
  backdrop-filter: blur(12px);
  box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.5);
  max-width: 800px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-section {
  margin-bottom: 2rem;
}

.app-title {
  font-size: 3.5rem;
  font-weight: bold;
  letter-spacing: 2px;
  margin-bottom: 0.5rem;
}

.app-tagline {
  font-size: 1.5rem;
  font-weight: 300;
}

.features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.feature-card {
  background: rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0px 4px 10px rgba(255, 255, 255, 0.2);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: scale(1.05);
  box-shadow: 0px 6px 15px rgba(255, 255, 255, 0.4);
}

.action-buttons {
  display: flex;
  gap: 1rem;
}

.action-btn {
  border-radius: 30px;
  font-size: 1.2rem;
  font-weight: bold;
  padding: 1rem 2rem;
  box-shadow: 0px 4px 15px rgba(255, 255, 255, 0.3);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.action-btn:hover {
  transform: scale(1.1);
  box-shadow: 0px 6px 20px rgba(255, 255, 255, 0.5);
}
</style>

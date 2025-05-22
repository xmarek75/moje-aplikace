import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

export function useDownload(transcription) {
  const $q = useQuasar()

  const downloadPlainText = () => {
    const blob = new Blob([transcription.value.text], { type: 'text/plain;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${transcription.value.media?.title || 'transcription'}.txt`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const downloadSRT = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await api.get(`/transcriptions/${transcription.value.id}/export-srt`, {
        responseType: 'blob',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const blob = new Blob([response.data], { type: 'text/srt;charset=utf-8' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${transcription.value.media?.title || 'subtitles'}.srt`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      $q.notify({ type: 'negative', message: 'Download failed.' })
    }
  }

  return {
    downloadPlainText,
    downloadSRT
  }
}

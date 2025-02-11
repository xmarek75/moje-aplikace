import { boot } from 'quasar/wrappers'
import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })  // Opravená cesta k backendu

export default boot(({ app }) => {
  app.config.globalProperties.$api = api
})

export { api }


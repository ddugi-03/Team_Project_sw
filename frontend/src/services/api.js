import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 60000,
})

export const requestIdeas = async (params) => {
  const { data } = await api.post('/api/v1/generate', params)
  return data
}

export const requestCombination = async (ids) => {
  const { data } = await api.post('/api/v1/combine', { idea_ids: ids })
  return data
}

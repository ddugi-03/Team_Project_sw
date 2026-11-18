import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 240000,
})

export const requestIdeas = async (params) => {
  const { data } = await api.post('/api/v1/generate', params)
  return data
}

export const requestCombination = async (ideas) => {
  const { data } = await api.post('/api/v1/combine', {
    selected_ideas: ideas.map((idea) => ({
      id: idea.id,
      title: idea.title,
      description: idea.description,
      tags: idea.tags,
      parent_ids: idea.parent_ids || idea.parentIds || [],
    })),
  })
  return data
}

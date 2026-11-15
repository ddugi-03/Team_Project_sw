import { create } from 'zustand'
import { requestIdeas, requestCombination } from '../services/api'

const normalize = (items) => items.map((item, index) => ({
  ...item,
  id: String(item.id ?? crypto.randomUUID()),
  title: item.title || `아이디어 ${index + 1}`,
  description: item.description || '',
  tags: Array.isArray(item.tags) ? item.tags : [],
}))

const errorMessage = (error) => {
  if (error.code === 'ERR_NETWORK') return '서버에 연결할 수 없습니다.'
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail
    return typeof detail === 'string' ? detail : '요청 형식을 확인해 주세요.'
  }
  return '요청을 처리하지 못했습니다. 다시 시도해 주세요.'
}

export const useIdeaStore = create((set, get) => ({
  topic: '',
  ideas: [],
  selectedIds: [],
  isGenerating: false,
  isCombining: false,
  notice: null,
  dismissNotice: () => set({ notice: null }),
  toggleIdea: (id) => set((state) => {
    if (state.isGenerating || state.isCombining) return {}
    if (state.selectedIds.includes(id)) {
      return { selectedIds: state.selectedIds.filter((value) => value !== id) }
    }
    return { selectedIds: [...state.selectedIds, id] }
  }),
  clearSelection: () => set((state) => state.isCombining ? {} : { selectedIds: [] }),
  generateIdeas: async (params) => {
    if (get().isGenerating || get().isCombining) return
    set({ isGenerating: true, notice: null })
    try {
      const result = await requestIdeas(params)
      if (!Array.isArray(result?.ideas) || !result.ideas.length) throw new Error('INVALID_RESPONSE')
      set({
        topic: params.keyword,
        ideas: normalize(result.ideas),
        selectedIds: [],
      })
    } catch (error) {
      set({ notice: { type: 'error', text: error.message === 'INVALID_RESPONSE' ? '아이디어를 불러오지 못했습니다.' : errorMessage(error) } })
    } finally {
      set({ isGenerating: false })
    }
  },
  combineIdeas: async () => {
    const state = get()
    if (state.selectedIds.length < 2 || state.isCombining || state.isGenerating) return
    const parents = state.selectedIds.map((id) => state.ideas.find((idea) => idea.id === id))
    if (parents.some((idea) => !idea)) return
    const ids = [...state.selectedIds]
    set({ isCombining: true, notice: null })
    try {
      const result = await requestCombination(ids)
      if (!Array.isArray(result?.ideas) || !result.ideas.length) throw new Error('INVALID_RESPONSE')
      const added = normalize(result.ideas.map((idea) => ({
        ...idea,
        parentIds: ids,
      })))
      set((current) => ({
        ideas: [...current.ideas, ...added],
        selectedIds: [],
        notice: { type: 'success', text: '결합한 아이디어를 추가했습니다.' },
      }))
      return added[0].id
    } catch (error) {
      set({ notice: { type: 'error', text: error.message === 'INVALID_RESPONSE' ? '조합 결과를 불러오지 못했습니다.' : errorMessage(error) } })
    } finally {
      set({ isCombining: false })
    }
  },
}))

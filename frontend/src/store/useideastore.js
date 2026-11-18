import { create } from 'zustand'
import { requestIdeas, requestCombination } from '../services/api'

const normalize = (items) => items.map((item, index) => ({
  ...item,
  id: String(item.id ?? crypto.randomUUID()),
  title: item.title || `아이디어 ${index + 1}`,
  description: item.description || '',
  tags: Array.isArray(item.tags) ? item.tags : [],
  parentIds: Array.isArray(item.parent_ids) && item.parent_ids.length
    ? item.parent_ids
    : item.parentIds?.length ? item.parentIds : undefined,
}))

const errorMessage = (error) => {
  if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') return '응답 대기 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.'
  if (error.code === 'ERR_NETWORK') return '서버에 연결할 수 없습니다.'
  const message = error.response?.data?.error?.message || error.response?.data?.message
  if (typeof message === 'string' && message.trim()) return message
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
  positions: {},
  isGenerating: false,
  isCombining: false,
  notice: null,
  dismissNotice: () => set({ notice: null }),
  moveCard: (id, position) => set((state) => {
    if (state.isGenerating || state.isCombining || !Number.isFinite(position.x) || !Number.isFinite(position.y)) return {}
    if (id !== 'topic' && !state.ideas.some((idea) => idea.id === id)) return {}
    return { positions: { ...state.positions, [id]: { x: Math.max(24, position.x), y: Math.max(24, position.y) } } }
  }),
  resetPositions: () => set((state) => state.isGenerating || state.isCombining ? {} : { positions: {} }),
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
    if (!Number.isInteger(params.count) || params.count < 1 || params.count > 10 || !params.keyword?.trim()) {
      set({ notice: { type: 'error', text: '주제와 생성 개수(1~10)를 확인해 주세요.' } })
      return
    }
    set({ isGenerating: true, notice: null })
    try {
      const result = await requestIdeas(params)
      if (!Array.isArray(result?.ideas) || !result.ideas.length) throw new Error('INVALID_RESPONSE')
      set({
        topic: params.keyword,
        ideas: normalize(result.ideas),
        selectedIds: [],
        positions: {},
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
      const result = await requestCombination(parents)
      if (!Array.isArray(result?.ideas) || !result.ideas.length) throw new Error('INVALID_RESPONSE')
      const added = normalize(result.ideas.map((idea) => ({
        ...idea,
        parentIds: idea.parent_ids?.length ? idea.parent_ids : ids,
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

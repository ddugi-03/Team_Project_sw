
import { create } from 'zustand'
import { mockIdeas } from '../data/mockideas'

export const useIdeaStore = create((set) => ({
  // 생성된 아이디어 목록
  ideas: [],

  // 선택한 아이디어 ID 목록
  selectedIds: [],

  // Dummy 아이디어 생성
  generateIdeas: (count) => {
    set({
      ideas: mockIdeas.slice(0, count),
      selectedIds: [],
    })
  },

  // 아이디어 선택 및 해제
  toggleIdea: (id) => {
    set((state) => ({
      selectedIds: state.selectedIds.includes(id)
        ? state.selectedIds.filter((item) => item !== id)
        : [...state.selectedIds, id],
    }))
  },
}))

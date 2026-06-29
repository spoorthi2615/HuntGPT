import { create } from 'zustand';

export const useStore = create((set) => ({
  results: [],
  setResults: (results) => set({ results }),
}));

import { create } from 'zustand';
import type { User } from '@/types';

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  token: localStorage.getItem('planner_token'),
  user: null,
  setAuth: (token, user) => {
    localStorage.setItem('planner_token', token);
    set({ token, user });
  },
  logout: () => {
    localStorage.removeItem('planner_token');
    set({ token: null, user: null });
  },
}));

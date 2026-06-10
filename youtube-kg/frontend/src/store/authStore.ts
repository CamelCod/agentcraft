import { create } from 'zustand'
import type { Session, User } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'

interface AuthState {
  session: Session | null
  user: { id: string; email: string; role: string } | null
  isAuthenticated: boolean
  setSession: (session: Session | null) => void
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  session: null,
  user: null,
  isAuthenticated: false,

  setSession: (session) => {
    if (session) {
      const u = session.user as User
      set({
        session,
        user: { id: u.id, email: u.email ?? '', role: 'analyst' },
        isAuthenticated: true,
      })
    } else {
      set({ session: null, user: null, isAuthenticated: false })
    }
  },

  logout: async () => {
    await supabase.auth.signOut()
    set({ session: null, user: null, isAuthenticated: false })
  },
}))

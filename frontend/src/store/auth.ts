import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "@/lib/api";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  firm_id: string;
}

const DEMO_USER: User = {
  id: "demo-user",
  email: "demo@wasp.vc",
  full_name: "Demo User",
  role: "partner",
  firm_id: "demo-firm",
};

interface AuthState {
  token: string | null;
  user: User | null;
  isDemo: boolean;
  isHydrated: boolean;
  login: (email: string, password: string) => Promise<void>;
  demoLogin: () => void;
  logout: () => void;
  setAuth: (token: string, user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isDemo: false,
      isHydrated: false,
      login: async (email: string, password: string) => {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/auth/login`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
          }
        );
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Invalid email or password");
        }
        const data = await res.json();
        api.setToken(data.access_token);
        set({ token: data.access_token, user: data.user, isDemo: false });
      },
      demoLogin: () => {
        api.setToken("demo-token");
        set({ token: "demo-token", user: DEMO_USER, isDemo: true });
      },
      logout: () => {
        api.setToken(null);
        set({ token: null, user: null, isDemo: false });
      },
      setAuth: (token: string, user: User) => {
        api.setToken(token);
        set({ token, user });
      },
      setHydrated: () => set({ isHydrated: true }),
    }),
    {
      name: "wasp-auth",
      partialize: (s) => ({ token: s.token, user: s.user, isDemo: s.isDemo }),
      onRehydrateStorage: () => (state) => {
        if (state?.token) api.setToken(state.token);
        useAuthStore.setState({ isHydrated: true });
      },
    }
  )
);

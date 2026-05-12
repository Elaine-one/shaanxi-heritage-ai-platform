import { defineStore } from 'pinia'
import { ref } from 'vue'
import authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoggedIn = ref(false)

  async function fetchUser() {
    try {
      const data = await authApi.getUser()
      user.value = data
      isLoggedIn.value = true
      return data
    } catch {
      user.value = null
      isLoggedIn.value = false
      return null
    }
  }

  async function login(credentials) {
    const data = await authApi.adminLogin(credentials)
    user.value = data
    isLoggedIn.value = true
    return data
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      clearUser()
    }
  }

  function clearUser() {
    user.value = null
    isLoggedIn.value = false
  }

  return { user, isLoggedIn, fetchUser, login, logout, clearUser }
})

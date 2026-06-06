import { api as apiClient } from './client'

export interface UserProfile {
  id: number
  username: string
  email: string
  full_name: string
  age?: number
  weight_kg?: number
  height_cm?: number
  goal: string
  activity_level: string
  allergies: string[]
  dietary_preferences: string[]
  bmi?: number
  daily_calorie_target?: number
  created_at: string
}

export const usersApi = {
  getProfile: () => apiClient.get<UserProfile>('/users/me').then((r) => r.data),

  updateProfile: (data: Partial<UserProfile>) =>
    apiClient.put<UserProfile>('/users/me', data).then((r) => r.data),
}

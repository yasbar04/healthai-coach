import { api as apiClient, slowApi } from './client'

export interface NutritionLog {
  id: number
  user_id: number
  meal_type: string
  foods_detected: string[]
  total_calories: number
  protein_g: number
  carbs_g: number
  fat_g: number
  fiber_g: number
  health_score: number
  imbalances: string[]
  suggestions: string[]
  notes?: string
  logged_at: string
}

export interface NutritionStats {
  period_days: number
  avg_daily_calories: number
  avg_protein_g: number
  avg_carbs_g: number
  avg_fat_g: number
  avg_fiber_g: number
  avg_health_score: number
  total_logs: number
  calorie_trend: { day: string; calories: number }[]
  macro_trend: { day: string; protein: number; carbs: number; fat: number }[]
  top_foods: string[]
}

export const nutritionApi = {
  analyzePhoto: (file: File, mealType: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('meal_type', mealType)
    form.append('save_log', 'true')
    return apiClient.post('/nutrition/analyze', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },

  logManual: (data: {
    meal_type: string
    total_calories: number
    protein_g?: number
    carbs_g?: number
    fat_g?: number
    fiber_g?: number
    notes?: string
    foods_detected?: string[]
  }) => apiClient.post<NutritionLog>('/nutrition/log', data).then((r) => r.data),

  getHistory: (days = 7) =>
    apiClient.get<NutritionLog[]>(`/nutrition/history?days=${days}`).then((r) => r.data),

  getStats: (days = 7) =>
    apiClient.get<NutritionStats>(`/nutrition/stats?days=${days}`).then((r) => r.data),

  getTrends: (days = 14) =>
    apiClient.get(`/nutrition/trends?days=${days}`).then((r) => r.data),

  deleteLog: (id: number) =>
    apiClient.delete(`/nutrition/log/${id}`),

  generateMealPlan: (data: {
    goal?: string
    duration_days?: number
    meals_per_day?: number
    budget_level?: string
  }) => apiClient.post('/ai/meal-plan', data).then((r) => r.data),

  analyzeWithAI: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return slowApi.post('/ai/analyze-meal', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },
}

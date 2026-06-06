import { api, recClient } from './client'

export interface RecommendationRequest {
  user_id: number
  goal: string
  fitness_level: string
  available_minutes: number
  equipment: string[]
  restrictions: string[]
  preferred_categories: string[]
  current_nutrition_score?: number
}

export interface Exercise {
  id: string
  name: string
  category: string
  muscle_groups: string[]
  equipment: string[]
  duration_minutes: number
  calories_per_hour: number
  difficulty: string
  description: string
  instructions: string[]
  benefits: string[]
}

export interface Workout {
  session_id: string
  name: string
  goal: string
  fitness_level: string
  total_duration_minutes: number
  estimated_calories: number
  exercises: Exercise[]
  warmup: string[]
  cooldown: string[]
}

export interface Recommendation {
  recommendation_id: string
  user_id: number
  workout: Workout
  rationale: string
  ai_tips: string[]
  next_session_suggestion: string
  generated_at: string
  _ollama?: boolean
  _demo?: boolean
}

export interface ActivityLog {
  id: string
  user_id: number
  exercise_id: string
  exercise_name: string
  duration_minutes: number
  calories_burned: number
  notes?: string
  perceived_effort: number
  logged_at: string
}

export const activityApi = {
  getRecommendation: (data: RecommendationRequest) =>
    api.post<Recommendation>('/ai/workout', data).then((r) => r.data),

  getHistory: (userId: number, limit = 10) =>
    recClient.get<Recommendation[]>(`/recommendations/history/${userId}?limit=${limit}`).then((r) => r.data),

  logActivity: (userId: number, data: {
    exercise_id: string
    exercise_name: string
    duration_minutes: number
    calories_burned?: number
    notes?: string
    perceived_effort?: number
  }) => recClient.post<ActivityLog>(`/recommendations/activity-log?user_id=${userId}`, data).then((r) => r.data),

  getStats: (userId: number, days = 7) =>
    recClient.get(`/recommendations/activity-stats/${userId}?days=${days}`).then((r) => r.data),
}

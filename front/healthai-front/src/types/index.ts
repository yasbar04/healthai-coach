/**
 * Type definitions for the HealthAI application
 */

// ===== Authentication Types =====
export interface User {
  id: string;
  email: string;
  username?: string;
  name?: string;
  role?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type?: string;
  user?: User;
}

// ===== API Response Types =====
export interface ApiError {
  detail?: string | Record<string, string[]>;
  message?: string;
  statusCode?: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

// ===== Pagination =====
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ===== Activities =====
export interface Activity {
  id: string;
  user_id: string;
  activity_type: string;
  duration_minutes: number;
  calories_burned?: number;
  date: string;
  notes?: string;
  created_at?: string;
}

// ===== Nutrition =====
export interface NutritionEntry {
  id: string;
  user_id: string;
  meal_type: "breakfast" | "lunch" | "dinner" | "snack";
  food_items: string[];
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  date: string;
  notes?: string;
  created_at?: string;
}

// ===== Biometrics =====
export interface BiometricEntry {
  id: string;
  user_id: string;
  weight_kg?: number;
  height_cm?: number;
  heart_rate?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  date: string;
  created_at?: string;
}

// ===== Analytics =====
export interface DashboardStats {
  total_activities: number;
  total_calories: number;
  avg_daily_steps?: number;
  weight_trend?: number;
  activity_trend?: number;
}

// ===== ETL Quality =====
export interface DataQualityReport {
  total_records: number;
  valid_records: number;
  invalid_records: number;
  missing_fields: Record<string, number>;
  last_check?: string;
  status: "good" | "warning" | "critical";
}

// ===== Common Form States =====
export interface FormState<T> {
  data: T;
  errors: Record<string, string>;
  isSubmitting: boolean;
  isValid: boolean;
}
